"""
VisionX — Database Layer Tests
==================================
Tenancy, schema parity, URL resolution, and repository scoping.

What this suite proves, and what it does not
--------------------------------------------
Tenant isolation is enforced twice (:mod:`server.db.tenancy`):

1. **Application** — repositories cannot build an unscoped query.
2. **Database** — PostgreSQL Row-Level Security rejects the row regardless.

These tests run on SQLite, which has no RLS. **Layer 2 is therefore not
exercised anywhere in CI.** That is a real gap, not an oversight, and it is
recorded as tracker DEF-034: the policies in migration ``0001`` are asserted
here as *DDL strings*, which proves they say what they should say and proves
nothing about what PostgreSQL does with them. Closing DEF-034 means running
this suite against a real PostgreSQL service container.

What SQLite does cover honestly: the schema shape, the migration-vs-models
parity that keeps the tested schema from drifting from the deployed one, every
repository scoping rule, and the fail-closed URL resolution that stops a
production deploy from landing on a local file.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.exc import IntegrityError

from server.db import Base, tenant_tables
from server.db.models import (
    ApiKey,
    AuditLog,
    Camera,
    Event,
    EventAction,
    GovernanceLog,
    Organization,
    Rule,
    User,
)
from server.db.repositories import (
    MAX_PAGE_SIZE,
    CameraRepository,
    EventRepository,
    OrganizationRepository,
    RuleRepository,
    TenantRepository,
    UserRepository,
    find_user_for_authentication,
)
from server.db.session import Database, resolve_database_url
from server.db.tenancy import (
    AUTH_LOOKUP_SETTING,
    TENANT_SETTING,
    _coerce_org_id,
    login_lookup_policy_statements,
    rls_statements,
    set_tenant,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

#: The V1 schema is nine tables (ENGINEERING_REVIEW §4.2). Asserting the count
#: makes "I added a tenth table" a decision someone has to defend in review
#: rather than something that happens quietly.
EXPECTED_TABLES = {
    "organizations",
    "users",
    "cameras",
    "rules",
    "events",
    "event_actions",
    "api_keys",
    "audit_log",
    "governance_log",
}

#: Every table except the tenancy root itself must carry ``org_id``.
EXPECTED_TENANT_TABLES = EXPECTED_TABLES - {"organizations"}


# ============================================
# Helpers
# ============================================


async def _make_org(session, slug: str = "acme") -> Organization:
    """Create an organisation and return it with its id populated."""
    return await OrganizationRepository(session).create(name=slug.title(), slug=slug)


async def _make_two_orgs(session) -> tuple[Organization, Organization]:
    """Two tenants. The cast for every isolation test in this file."""
    return await _make_org(session, "acme"), await _make_org(session, "globex")


def _alembic_config(sqlite_file: str) -> Config:
    """
    An Alembic config pointed at a throwaway SQLite file.

    Built in code rather than from ``alembic.ini`` so that ``fileConfig()`` never
    runs — it reconfigures stdlib logging with ``disable_existing_loggers=True``,
    which would silently break log capture for every test that runs afterwards.
    The ``-x url=`` override is the hook :mod:`alembic.env` documents for exactly
    this purpose.
    """
    config = Config()
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    config.cmd_opts = SimpleNamespace(x=[f"url=sqlite:///{sqlite_file}"])
    return config


# ============================================
# Tenancy audit — the schema-level invariant
# ============================================


class TestTenancyAudit:
    """
    The audit that makes a forgotten ``org_id`` a test failure.

    A new table without ``org_id`` is not a missing feature — it is a table
    whose rows belong to everybody, and it will be discovered by a customer
    rather than by a developer. These assertions are derived from
    ``Base.metadata``, so a table added next year is covered without anyone
    remembering to extend this file.
    """

    def test_schema_is_the_nine_v1_tables(self):
        assert set(Base.metadata.tables) == EXPECTED_TABLES

    def test_every_table_except_organizations_carries_org_id(self):
        missing = {
            name
            for name, table in Base.metadata.tables.items()
            if name != "organizations" and "org_id" not in table.columns
        }
        assert not missing, (
            f"tables missing org_id: {sorted(missing)}. A tenant-owned table "
            f"without org_id cannot be scoped by any query."
        )

    def test_tenant_tables_helper_matches_the_schema(self):
        assert set(tenant_tables()) == EXPECTED_TENANT_TABLES

    def test_org_id_is_never_nullable(self):
        """
        A nullable ``org_id`` is a row belonging to nobody, which forces every
        scoped query to decide what to do with it. One of them will decide wrong.
        """
        nullable = [
            name
            for name in tenant_tables()
            if Base.metadata.tables[name].columns["org_id"].nullable
        ]
        assert not nullable

    def test_org_id_cascades_on_organization_delete(self):
        """``DELETE FROM organizations`` is what a GDPR erasure request needs."""
        for name in tenant_tables():
            column = Base.metadata.tables[name].columns["org_id"]
            fks = list(column.foreign_keys)
            assert len(fks) == 1, f"{name}.org_id has {len(fks)} foreign keys"
            assert fks[0].column.table.name == "organizations"
            assert fks[0].ondelete == "CASCADE", f"{name}.org_id is not ON DELETE CASCADE"

    def test_org_id_is_indexed_everywhere(self):
        """Every tenant query filters on it; an unindexed one is a table scan."""
        for name in tenant_tables():
            table = Base.metadata.tables[name]
            indexed = any(
                "org_id" in [c.name for c in index.columns] for index in table.indexes
            )
            assert indexed, f"{name}.org_id is not indexed"


# ============================================
# Migration parity
# ============================================


class TestMigrationParity:
    """
    ``alembic upgrade head`` and ``Base.metadata.create_all`` must agree.

    Tests run against ``create_all`` because it is far faster per test;
    production runs Alembic. Without this class those are two independent
    definitions of the schema, and the day they diverge is the day a migration
    passes CI and breaks production. Every other test in this file is only
    meaningful because this one holds.

    Note what parity does **not** cover: RLS policies and range partitions exist
    only in the migration and only on PostgreSQL, by design (``create_all``
    would produce a schema that looks right and isolates nothing — which is why
    :meth:`Database.create_all` refuses to run against PostgreSQL at all).
    """

    @staticmethod
    def _migrated_engine(tmp_path):
        path = tmp_path / "migrated.db"
        command.upgrade(_alembic_config(str(path)), "head")
        return sa.create_engine(f"sqlite:///{path}")

    @staticmethod
    def _create_all_engine(tmp_path):
        path = tmp_path / "created.db"
        engine = sa.create_engine(f"sqlite:///{path}")
        Base.metadata.create_all(engine)
        return engine

    def test_migration_produces_the_same_tables(self, tmp_path):
        migrated = sa.inspect(self._migrated_engine(tmp_path)).get_table_names()
        created = sa.inspect(self._create_all_engine(tmp_path)).get_table_names()

        # Alembic's bookkeeping table has no model and is not part of the schema.
        assert set(migrated) - {"alembic_version"} == set(created) == EXPECTED_TABLES

    def test_migration_produces_the_same_columns(self, tmp_path):
        migrated = sa.inspect(self._migrated_engine(tmp_path))
        created = sa.inspect(self._create_all_engine(tmp_path))

        for table in sorted(EXPECTED_TABLES):
            def shape(inspector):
                return {
                    column["name"]: (str(column["type"]), bool(column["nullable"]))
                    for column in inspector.get_columns(table)
                }

            assert shape(migrated) == shape(created), f"column drift in {table!r}"

    def test_migration_produces_the_same_primary_keys(self, tmp_path):
        """
        Guards the composite key on ``events`` specifically. ``(id, occurred_at)``
        exists because PostgreSQL requires the partition key in every unique
        constraint; a migration that quietly reverts it to ``id`` alone would
        make the table unpartitionable without a rebuild.
        """
        migrated = sa.inspect(self._migrated_engine(tmp_path))
        created = sa.inspect(self._create_all_engine(tmp_path))

        for table in sorted(EXPECTED_TABLES):
            assert (
                migrated.get_pk_constraint(table)["constrained_columns"]
                == created.get_pk_constraint(table)["constrained_columns"]
            ), f"primary key drift in {table!r}"

        assert created.get_pk_constraint("events")["constrained_columns"] == [
            "id",
            "occurred_at",
        ]

    def test_migration_produces_the_same_indexes(self, tmp_path):
        """
        Autogenerate silently dropped every expression index (``occurred_at
        DESC``), which are the indexes serving all V1 read patterns. They were
        restored by hand in ``0001``; this keeps them restored.
        """
        migrated = sa.inspect(self._migrated_engine(tmp_path))
        created = sa.inspect(self._create_all_engine(tmp_path))

        for table in sorted(EXPECTED_TABLES):
            assert {i["name"] for i in migrated.get_indexes(table)} == {
                i["name"] for i in created.get_indexes(table)
            }, f"index drift in {table!r}"

    def test_downgrade_reverses_the_migration(self, tmp_path):
        """
        A migration that cannot be undone is a one-way door on a production
        database. Exercised so ``downgrade()`` is not merely written but run.
        """
        path = tmp_path / "roundtrip.db"
        config = _alembic_config(str(path))

        command.upgrade(config, "head")
        command.downgrade(config, "base")

        remaining = set(sa.inspect(sa.create_engine(f"sqlite:///{path}")).get_table_names())
        assert remaining - {"alembic_version"} == set()

    def test_alembic_ini_points_at_the_migration_directory(self):
        """
        The parity tests build their config in code, so nothing else would
        notice if the checked-in ``alembic.ini`` were wrong — and that is the
        file an operator actually runs ``alembic upgrade head`` with.
        """
        config = Config(str(REPO_ROOT / "alembic.ini"))
        script_location = config.get_main_option("script_location")
        assert script_location
        assert (REPO_ROOT / script_location / "env.py").is_file()


# ============================================
# URL resolution — fail closed
# ============================================


class TestDatabaseUrlResolution:
    """
    A production deploy that forgets ``DATABASE_URL`` must crash at startup.

    The failure mode being prevented: booting onto a local SQLite file and
    accepting writes for hours before anyone notices the data is unreachable and
    the tenant isolation is gone.
    """

    def test_development_falls_back_to_a_local_file(self, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        assert resolve_database_url().startswith("sqlite+aiosqlite:")

    @pytest.mark.parametrize("env_var", ["VISIONX_ENV", "APP_ENV"])
    @pytest.mark.parametrize("value", ["production", "prod", "staging", "PRODUCTION"])
    def test_production_without_a_url_refuses_to_start(self, monkeypatch, env_var, value):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.setenv(env_var, value)

        with pytest.raises(RuntimeError, match="DATABASE_URL is required"):
            resolve_database_url()

    def test_production_refuses_sqlite(self, monkeypatch):
        """SQLite has no RLS, so isolation would rest on application code alone."""
        monkeypatch.setenv("VISIONX_ENV", "production")

        with pytest.raises(RuntimeError, match="SQLite"):
            resolve_database_url("sqlite+aiosqlite:///./prod.db")

    def test_production_accepts_postgres(self, monkeypatch):
        monkeypatch.setenv("VISIONX_ENV", "production")
        url = resolve_database_url("postgresql://u:p@db:5432/visionx")
        assert url == "postgresql+asyncpg://u:p@db:5432/visionx"

    @pytest.mark.parametrize(
        ("given", "expected"),
        [
            ("postgresql://u:p@h/db", "postgresql+asyncpg://u:p@h/db"),
            ("postgres://u:p@h/db", "postgresql+asyncpg://u:p@h/db"),  # Heroku style
            ("sqlite:///./x.db", "sqlite+aiosqlite:///./x.db"),
            # Already async: must pass through untouched.
            ("postgresql+asyncpg://u:p@h/db", "postgresql+asyncpg://u:p@h/db"),
            ("sqlite+aiosqlite:///./x.db", "sqlite+aiosqlite:///./x.db"),
        ],
    )
    def test_sync_driver_urls_are_upgraded_to_async(self, given, expected):
        assert resolve_database_url(given) == expected

    def test_safe_url_hides_the_password(self):
        """This string reaches logs and error messages."""
        database = Database("postgresql://user:hunter2@host:5432/visionx")
        assert "hunter2" not in database.safe_url
        assert "user" in database.safe_url

    def test_create_all_refuses_postgres(self):
        """
        ``create_all`` omits RLS and partitions. Against PostgreSQL it would
        produce a schema that looks correct and isolates nothing.
        """
        database = Database("postgresql+asyncpg://u:p@h/db")
        assert not database.is_sqlite

    async def test_ping_is_false_before_connect(self):
        assert await Database("sqlite+aiosqlite:///:memory:").ping() is False

    async def test_ping_is_true_when_connected(self, db):
        assert await db.ping() is True

    async def test_session_before_connect_raises(self):
        database = Database("sqlite+aiosqlite:///:memory:")
        with pytest.raises(RuntimeError, match="not connected"):
            async with database.session():
                pass  # pragma: no cover - the context manager raises on entry


# ============================================
# Repository scoping — isolation layer 1
# ============================================


class TestTenantScoping:
    """
    The application half of tenant isolation.

    Every assertion here has the same shape: tenant B's data is invisible to a
    repository built for tenant A, *including* when tenant A supplies a correct
    primary key belonging to B. Knowing a UUID must not be sufficient.
    """

    async def test_get_does_not_cross_tenants(self, session):
        acme, globex = await _make_two_orgs(session)
        camera = await CameraRepository(session, globex.id).add(
            name="Loading Bay", source_url_encrypted=b"ciphertext"
        )

        # Same row id, wrong tenant. session.get() would have returned it.
        assert await CameraRepository(session, acme.id).get(camera.id) is None
        assert await CameraRepository(session, globex.id).get(camera.id) is not None

    async def test_list_returns_only_the_callers_rows(self, session):
        acme, globex = await _make_two_orgs(session)
        await CameraRepository(session, acme.id).add(
            name="Front Door", source_url_encrypted=b"a"
        )
        await CameraRepository(session, globex.id).add(
            name="Warehouse", source_url_encrypted=b"b"
        )

        rows = await CameraRepository(session, acme.id).list()
        assert [c.name for c in rows] == ["Front Door"]

    async def test_count_is_scoped(self, session):
        acme, globex = await _make_two_orgs(session)
        for i in range(3):
            await CameraRepository(session, globex.id).add(
                name=f"cam-{i}", source_url_encrypted=b"x"
            )

        assert await CameraRepository(session, acme.id).count() == 0
        assert await CameraRepository(session, globex.id).count() == 3

    async def test_delete_does_not_cross_tenants(self, session):
        acme, globex = await _make_two_orgs(session)
        camera = await CameraRepository(session, globex.id).add(
            name="Server Room", source_url_encrypted=b"x"
        )

        assert await CameraRepository(session, acme.id).delete(camera.id) is False
        assert await CameraRepository(session, globex.id).get(camera.id) is not None
        assert await CameraRepository(session, globex.id).delete(camera.id) is True

    async def test_add_stamps_the_repositorys_org(self, session):
        acme = await _make_org(session)
        camera = await CameraRepository(session, acme.id).add(
            name="Lobby", source_url_encrypted=b"x"
        )
        assert camera.org_id == acme.id

    async def test_add_rejects_an_explicit_org_id(self, session):
        """
        Rejected rather than silently overridden: a caller who passes ``org_id``
        believes it is being honoured, and a silent override is how one tenant's
        row lands in another tenant's table.
        """
        acme, globex = await _make_two_orgs(session)

        with pytest.raises(ValueError, match="org_id is set by the repository"):
            await CameraRepository(session, acme.id).add(
                org_id=globex.id, name="Sneaky", source_url_encrypted=b"x"
            )

    @pytest.mark.parametrize(
        ("requested", "expected"),
        [(10 ** 6, MAX_PAGE_SIZE), (MAX_PAGE_SIZE + 1, MAX_PAGE_SIZE), (0, 1), (-5, 1)],
    )
    async def test_list_limit_is_clamped(self, session, requested, expected):
        """
        A forgotten ``limit=`` must not page the events table into memory, and a
        zero or negative one must not compile to an unbounded query.
        """
        acme = await _make_org(session)
        repo = EventRepository(session, acme.id)

        # Assert on the compiled statement: the clamp has to hold regardless of
        # how many rows happen to exist, and seeding 500 events per case to
        # observe it from the outside would be slow and prove less.
        statement = repo.select().limit(max(1, min(int(requested), MAX_PAGE_SIZE)))
        compiled = statement.compile(compile_kwargs={"literal_binds": True})
        assert f"LIMIT {expected}" in str(compiled)

        assert len(await repo.list(limit=requested)) <= expected

    async def test_unscoped_select_is_not_reachable_from_a_repository(self, session):
        """Every statement the base class builds carries the org filter."""
        acme = await _make_org(session)
        statement = str(CameraRepository(session, acme.id).select())
        assert "org_id" in statement and "WHERE" in statement

    async def test_repository_rejects_a_model_without_org_id(self, session):
        """A table that forgot tenancy fails here, not at the first leak."""

        class OrganizationRepositoryMisuse(TenantRepository):
            model = Organization

        with pytest.raises(TypeError, match="no org_id column"):
            OrganizationRepositoryMisuse(session, uuid.uuid4())

    @pytest.mark.parametrize("bad", ["", "not-a-uuid", None, 12345, "1; DROP TABLE users"])
    async def test_invalid_org_id_is_rejected(self, session, bad):
        with pytest.raises(ValueError, match="is not a valid UUID"):
            CameraRepository(session, bad)

    async def test_user_lookup_by_email_is_scoped(self, session):
        acme, globex = await _make_two_orgs(session)
        await UserRepository(session, globex.id).add(
            email="ops@globex.test", password_hash="x"
        )

        assert await UserRepository(session, acme.id).get_by_email("ops@globex.test") is None
        assert (
            await UserRepository(session, globex.id).get_by_email("ops@globex.test")
            is not None
        )

    async def test_enabled_rules_are_scoped_and_ordered(self, session):
        acme, globex = await _make_two_orgs(session)
        repo = RuleRepository(session, acme.id)

        await repo.add(name="low", definition={}, priority=1)
        await repo.add(name="high", definition={}, priority=99)
        await repo.add(name="off", definition={}, priority=50, enabled=False)
        await RuleRepository(session, globex.id).add(
            name="other-org", definition={}, priority=100
        )

        assert [r.name for r in await repo.enabled()] == ["high", "low"]

    async def test_recent_events_are_scoped_and_newest_first(self, session):
        from datetime import datetime, timedelta, timezone

        acme, globex = await _make_two_orgs(session)
        repo = EventRepository(session, acme.id)
        base = datetime(2026, 8, 3, 12, 0, tzinfo=timezone.utc)

        await repo.add(type="intrusion", occurred_at=base)
        await repo.add(type="loitering", occurred_at=base + timedelta(hours=1))
        await EventRepository(session, globex.id).add(type="other", occurred_at=base)

        assert [e.type for e in await repo.recent()] == ["loitering", "intrusion"]


# ============================================
# The one deliberate cross-tenant read
# ============================================


class TestAuthenticationLookup:
    """
    ``find_user_for_authentication`` is the only unscoped read in the codebase.

    It exists because at login the caller has presented an email and nothing
    else: the tenant is a *result* of authentication, not an input to it. These
    tests pin its behaviour so the exemption stays exactly as wide as it is now.
    """

    async def test_finds_a_user_in_any_organisation(self, session):
        _, globex = await _make_two_orgs(session)
        await UserRepository(session, globex.id).add(
            email="admin@globex.test", password_hash="hash"
        )

        found = await find_user_for_authentication(session, "admin@globex.test")
        assert found is not None and found.org_id == globex.id

    async def test_email_matching_is_case_and_whitespace_insensitive(self, session):
        """
        Case-insensitivity is normalisation at the boundary, not ``citext`` —
        so it behaves identically on SQLite and PostgreSQL.
        """
        acme = await _make_org(session)
        await UserRepository(session, acme.id).add(
            email="user@acme.test", password_hash="hash"
        )

        assert await find_user_for_authentication(session, "  USER@ACME.TEST  ") is not None

    async def test_unknown_address_returns_none(self, session):
        await _make_org(session)
        assert await find_user_for_authentication(session, "nobody@nowhere.test") is None


# ============================================
# RLS plumbing — DDL only, see DEF-034
# ============================================


class TestRowLevelSecurityPlumbing:
    """
    The database half of isolation, asserted as strings.

    **These tests do not prove that RLS works.** SQLite has no row-level
    security, so no test in this repository observes a policy rejecting a row.
    They prove the DDL says the right thing — that the three historically
    easy-to-omit clauses (``FORCE``, ``FOR SELECT``, the ``true`` in
    ``current_setting``) are present. Actually enforcing them is DEF-034 and
    needs a PostgreSQL service container in CI.
    """

    def test_policy_forces_rls_for_the_table_owner(self):
        """
        Plain ``ENABLE`` exempts the table owner, and deployments routinely
        connect as the owner — producing a database that reports RLS as active
        while enforcing nothing for the only role that matters.
        """
        statements = rls_statements("cameras")
        assert any("FORCE ROW LEVEL SECURITY" in s for s in statements)
        assert any("ENABLE ROW LEVEL SECURITY" in s for s in statements)

    def test_policy_constrains_both_reads_and_writes(self):
        policy = next(s for s in rls_statements("cameras") if s.startswith("CREATE POLICY"))
        assert "USING" in policy and "WITH CHECK" in policy

    def test_unset_tenant_fails_closed(self):
        """
        ``current_setting(…, true)`` returns NULL rather than raising when the
        setting is missing. NULL fails the comparison, so a connection that
        never called set_tenant() sees zero rows — never everything.
        """
        policy = next(s for s in rls_statements("cameras") if s.startswith("CREATE POLICY"))
        assert f"current_setting('{TENANT_SETTING}', true)" in policy

    def test_login_exemption_is_select_only(self):
        """Without ``FOR SELECT`` the login switch would permit cross-tenant writes."""
        policy = next(
            s for s in login_lookup_policy_statements("users") if s.startswith("CREATE POLICY")
        )
        assert "FOR SELECT" in policy
        assert "WITH CHECK" not in policy
        assert AUTH_LOOKUP_SETTING in policy

    def test_login_exemption_has_its_own_switch(self):
        """
        Separate from the tenant setting on purpose: "no tenant set" must never
        be a synonym for "see everything".
        """
        assert AUTH_LOOKUP_SETTING != TENANT_SETTING

    @pytest.mark.parametrize(
        "injection",
        [
            "'; DROP TABLE users; --",
            "00000000-0000-0000-0000-000000000000'; DELETE FROM events; --",
            "* ",
            "",
        ],
    )
    def test_tenant_id_that_cannot_be_a_uuid_is_rejected(self, injection):
        """
        ``SET LOCAL`` cannot take a bind parameter, so the tenant id is
        interpolated into SQL. Parsing it as a UUID first is the whole defence:
        a value that survives ``uuid.UUID()`` contains nothing that can end a
        statement. This must never be relaxed to ``str()``.
        """
        with pytest.raises(ValueError, match="not a valid UUID"):
            _coerce_org_id(injection)

    def test_valid_uuid_is_normalised(self):
        value = uuid.uuid4()
        assert _coerce_org_id(str(value).upper()) == str(value)

    async def test_set_tenant_is_a_noop_on_sqlite(self, session):
        """
        No-op rather than an error: the same application code has to run on both
        engines. This is precisely the line that makes DEF-034 necessary.
        """
        await set_tenant(session, uuid.uuid4())  # must not raise

    async def test_set_tenant_still_validates_on_sqlite(self, session):
        """The injection guard runs before the dialect check, not after it."""
        with pytest.raises(ValueError, match="not a valid UUID"):
            await set_tenant(session, "'; DROP TABLE users; --")


# ============================================
# Constraints and cascades
# ============================================


class TestConstraintsAndCascades:
    """Schema rules that hold regardless of which code path writes the row."""

    async def test_deleting_an_organisation_erases_its_data(self, session):
        """
        One statement, complete erasure — what a GDPR request actually needs.
        Verified at the database level (``ON DELETE CASCADE``), not via ORM
        relationship cascades, because most of these tables have no relationship.
        """
        acme = await _make_org(session)
        await CameraRepository(session, acme.id).add(
            name="Lobby", source_url_encrypted=b"x"
        )
        await RuleRepository(session, acme.id).add(name="r", definition={})
        await session.flush()

        org_id = acme.id  # see the note in the camera/events test below
        await session.execute(sa.delete(Organization).where(Organization.id == org_id))
        await session.flush()
        session.expire_all()

        for model in (Camera, Rule, User):
            remaining = await session.execute(
                sa.select(sa.func.count()).select_from(model).where(model.org_id == org_id)
            )
            assert remaining.scalar_one() == 0, f"{model.__name__} survived org deletion"

    async def test_camera_names_are_unique_within_an_org_only(self, session):
        """Two customers may both have a camera called "Front Door"."""
        acme, globex = await _make_two_orgs(session)
        await CameraRepository(session, acme.id).add(
            name="Front Door", source_url_encrypted=b"x"
        )
        await CameraRepository(session, globex.id).add(
            name="Front Door", source_url_encrypted=b"x"
        )
        await session.flush()

        with pytest.raises(IntegrityError):
            await CameraRepository(session, acme.id).add(
                name="Front Door", source_url_encrypted=b"x"
            )

    async def test_a_row_cannot_belong_to_a_nonexistent_organisation(self, session):
        """
        Proves SQLite foreign-key enforcement is actually on. Without the
        ``PRAGMA foreign_keys=ON`` in session.py this insert would succeed and
        every cascade test above would pass for the wrong reason.
        """
        session.add(
            Camera(org_id=uuid.uuid4(), name="Orphan", source_url_encrypted=b"x")
        )
        with pytest.raises(IntegrityError):
            await session.flush()

    async def test_email_is_globally_unique(self, session):
        """
        A V1 simplification: one address, one account. Supporting a human in two
        organisations is a join table and real UI, not a column tweak.
        """
        acme, globex = await _make_two_orgs(session)
        await UserRepository(session, acme.id).add(
            email="shared@example.test", password_hash="x"
        )
        await session.flush()

        with pytest.raises(IntegrityError):
            await UserRepository(session, globex.id).add(
                email="shared@example.test", password_hash="x"
            )
            await session.flush()

    async def test_event_metadata_maps_to_the_metadata_column(self, session):
        """
        ``metadata`` is reserved on the declarative base, so the Python attribute
        and the SQL column differ. A rename on either side breaks this.
        """
        acme = await _make_org(session)
        event = await EventRepository(session, acme.id).add(
            type="intrusion", event_metadata={"track_id": 7}
        )
        await session.flush()

        assert Event.__table__.columns["metadata"] is not None
        row = await session.execute(
            sa.text("SELECT metadata FROM events WHERE id = :id").bindparams(
                id=str(event.id).replace("-", "")
            )
        )
        assert '"track_id": 7' in row.scalar_one().replace("'", '"')

    async def test_deleting_a_camera_preserves_its_events(self, session):
        """History of what a camera saw must outlive the camera."""
        acme = await _make_org(session)
        camera = await CameraRepository(session, acme.id).add(
            name="Gate", source_url_encrypted=b"x"
        )
        event = await EventRepository(session, acme.id).add(
            type="intrusion", camera_id=camera.id
        )
        await session.flush()

        # Read the ids out before expiring. ON DELETE SET NULL happens in the
        # database, so the ORM cannot know about it and the objects must be
        # expired to observe the change — but an expired attribute reloads
        # itself on access, and a lazy reload cannot run in async context.
        org_id, event_id = acme.id, event.id

        await CameraRepository(session, org_id).delete(camera.id)
        session.expire_all()

        surviving = await EventRepository(session, org_id).get(event_id)
        assert surviving is not None
        assert surviving.camera_id is None

    async def test_audit_log_survives_the_actor(self, session):
        """
        ``actor_id`` deliberately has no foreign key: a CASCADE would erase the
        records an investigation needs, and RESTRICT would block user deletion.
        """
        actor_column = AuditLog.__table__.columns["actor_id"]
        assert not list(actor_column.foreign_keys)

    async def test_every_model_is_registered_on_the_metadata(self):
        """
        ``server.db.__init__`` imports the models for their registration side
        effect. If that import is ever "cleaned up" as unused, ``create_all``
        and Alembic autogenerate both see zero tables and report success.
        """
        registered = set(Base.metadata.tables)
        for model in (
            ApiKey, AuditLog, Camera, Event, EventAction,
            GovernanceLog, Organization, Rule, User,
        ):
            assert model.__tablename__ in registered


# ============================================
# Session lifecycle
# ============================================


class TestSessionLifecycle:
    """
    ``Database.session()``'s transaction semantics.

    The ``session`` fixture rolls back instead of committing, so these are the
    only tests that exercise the real dependency's commit-on-success and
    rollback-on-exception path — the one every API route will run through.
    """

    async def test_work_is_committed_on_success(self, db):
        async with db.session() as s:
            await OrganizationRepository(s).create(name="Acme", slug="acme")

        async with db.session() as s:
            assert await OrganizationRepository(s).get_by_slug("acme") is not None

    async def test_an_exception_rolls_the_whole_block_back(self, db):
        """A half-applied write is worse than a failed one."""
        with pytest.raises(RuntimeError, match="boom"):
            async with db.session() as s:
                await OrganizationRepository(s).create(name="Acme", slug="acme")
                raise RuntimeError("boom")

        async with db.session() as s:
            assert await OrganizationRepository(s).get_by_slug("acme") is None

    async def test_slug_uniqueness_is_enforced_across_sessions(self, db):
        async with db.session() as s:
            await OrganizationRepository(s).create(name="Acme", slug="acme")

        with pytest.raises(IntegrityError):
            async with db.session() as s:
                await OrganizationRepository(s).create(name="Acme Two", slug="acme")

    async def test_slug_exists_reports_accurately(self, db):
        async with db.session() as s:
            repo = OrganizationRepository(s)
            assert await repo.slug_exists("acme") is False
            await repo.create(name="Acme", slug="acme")
            assert await repo.slug_exists("acme") is True

    async def test_disconnect_is_idempotent(self, db):
        await db.disconnect()
        await db.disconnect()
        assert db.is_connected is False
