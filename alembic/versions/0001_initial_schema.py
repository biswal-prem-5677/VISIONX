"""initial schema — nine tables, tenancy, RLS, partitions

The V1 schema from ENGINEERING_REVIEW.md §4.2. Nine tables, not ninety.

This file was seeded by ``--autogenerate`` and then rewritten by hand, because
the generated version was only correct for the database it was generated
against. Three classes of defect were fixed, all of which would have surfaced
as a failed production deploy rather than a failed test:

1. **Dialect-locked server defaults.** Autogenerate rendered the boolean
   defaults it saw on SQLite as ``sa.text('1')`` and the timestamp defaults as
   ``sa.text('(CURRENT_TIMESTAMP)')``. PostgreSQL rejects an integer default on
   a ``boolean`` column outright. Both are now expressed as SQLAlchemy
   constructs (``sa.true()``, ``sa.func.now()``) that each dialect compiles for
   itself.
2. **Missing composite indexes.** The expression indexes on the models
   (``occurred_at DESC``, ``created_at DESC``) were dropped entirely by
   autogenerate, leaving only the single-column ``org_id`` indexes. Those are
   the indexes that serve every V1 read pattern; without them the events
   timeline is a sequential scan.
3. **No RLS and no partitions.** Neither is expressible in model metadata, so
   autogenerate cannot know about them. They are the two things the review
   insists on doing before there is data to migrate
   (ENGINEERING_REVIEW.md §4.3), and they are applied at the bottom of
   :func:`upgrade`.

Portability
-----------
The DDL runs on PostgreSQL (production) and SQLite (tests). Everything that
only PostgreSQL can express — partitioning, row-level security — is guarded by
a dialect check and skipped elsewhere. The *column shape* is identical on both,
which is what ``tests/test_db.py::TestMigrationParity`` verifies; the storage
and isolation guarantees are not, which is why the SQLite path is a test target
and never a deployment target (``server/db/session.py`` refuses it in
production).

Revision ID: 0001
Revises:
Create Date: 2026-08-03 00:06:54.528247
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from server.db.tenancy import (
    login_lookup_policy_statements,
    login_lookup_teardown_statements,
    rls_statements,
    rls_teardown_statements,
)

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ============================================
# Portable column types
# ============================================
# Defined locally rather than imported from server.db.base. A migration is a
# historical record: if it borrowed its types from the models, editing a model
# type in 2027 would silently rewrite what this 2026 migration claims to have
# done, and a fresh database would stop matching an existing one.

_PK = sa.Uuid()
_JSON = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")
_TS = sa.DateTime(timezone=True)


def _created_at() -> sa.Column:
    return sa.Column("created_at", _TS, server_default=sa.func.now(), nullable=False)


def _updated_at() -> sa.Column:
    return sa.Column("updated_at", _TS, server_default=sa.func.now(), nullable=False)


def _org_fk(table: str) -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(
        ["org_id"],
        ["organizations.id"],
        name=op.f(f"fk_{table}_org_id_organizations"),
        ondelete="CASCADE",
    )


#: Every table carrying ``org_id``. Written out rather than derived from model
#: metadata for the same reason the column types are: a migration must describe
#: the schema as it was, not as the models later became. ``tests/test_db.py``
#: asserts this tuple still matches ``server.db.base.tenant_tables()``, so a new
#: tenant table cannot be added without a migration that covers it.
_TENANT_TABLES = (
    "users",
    "cameras",
    "rules",
    "api_keys",
    "audit_log",
    "events",
    "event_actions",
    "governance_log",
)


# ============================================
# Events partitioning
# ============================================

#: Monthly partitions are pre-created for this window. Fixed dates, not
#: "24 months from today", so that running this migration in 2026 and in 2028
#: produces the same database. A scheduled job must extend the window before it
#: closes; until then the DEFAULT partition below guarantees that an insert
#: outside the window still succeeds rather than raising.
_PARTITION_FIRST_YEAR = 2026
_PARTITION_LAST_YEAR = 2027

#: PostgreSQL 12 is the first release that allows a foreign key to *reference* a
#: partitioned table, which ``event_actions`` does. Older servers accept every
#: statement above this one and then fail on that constraint, so check up front.
_MIN_PG_VERSION = 120000


def _month_bounds(year: int, month: int) -> tuple[str, str]:
    """Half-open ``[start, end)`` bounds for one month, as ISO dates."""
    if month == 12:
        return f"{year}-12-01", f"{year + 1}-01-01"
    return f"{year}-{month:02d}-01", f"{year}-{month + 1:02d}-01"


def _create_event_partitions() -> None:
    """Create the monthly children of ``events`` plus a DEFAULT catch-all."""
    for year in range(_PARTITION_FIRST_YEAR, _PARTITION_LAST_YEAR + 1):
        for month in range(1, 13):
            start, end = _month_bounds(year, month)
            op.execute(
                f"CREATE TABLE IF NOT EXISTS events_{year}_{month:02d} "
                f"PARTITION OF events "
                f"FOR VALUES FROM ('{start}') TO ('{end}')"
            )

    # Created last, and deliberately. A DEFAULT partition accepts rows that fit
    # no other range, so a clock skew, a backfill, or a forgotten cron job
    # cannot turn an alert into an INSERT error. Attaching a new range partition
    # later requires the default to hold no rows for that range, which is the
    # cost of this safety net and is worth paying.
    op.execute("CREATE TABLE IF NOT EXISTS events_default PARTITION OF events DEFAULT")


# ============================================
# Upgrade
# ============================================


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    if is_postgres:
        version = bind.exec_driver_sql("SHOW server_version_num").scalar()
        if int(version) < _MIN_PG_VERSION:
            raise RuntimeError(
                f"PostgreSQL {_MIN_PG_VERSION // 10000}+ is required: event_actions "
                f"declares a foreign key referencing the partitioned events table, "
                f"which older servers cannot create. Server reports {version}."
            )

    # -- organizations: the tenancy root ----------------------------------
    op.create_table(
        "organizations",
        sa.Column("id", _PK, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("plan", sa.String(length=40), server_default="free", nullable=False),
        sa.Column(
            "retention_days", sa.Integer(), server_default="90", nullable=False
        ),
        _created_at(),
        _updated_at(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organizations")),
        sa.UniqueConstraint("slug", name=op.f("uq_organizations_slug")),
    )

    # -- users -------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", _PK, nullable=False),
        sa.Column("org_id", _PK, nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=200), server_default="", nullable=False),
        sa.Column("role", sa.String(length=40), server_default="user", nullable=False),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.true(), nullable=False
        ),
        sa.Column("last_login_at", _TS, nullable=True),
        _created_at(),
        _updated_at(),
        _org_fk("users"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_index(op.f("ix_users_org_id"), "users", ["org_id"], unique=False)

    # -- cameras -----------------------------------------------------------
    op.create_table(
        "cameras",
        sa.Column("id", _PK, nullable=False),
        sa.Column("org_id", _PK, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        # BYTEA/BLOB, not text: an RTSP URL embeds user:password@. See the
        # warning on server.db.models.Camera — nothing may write this column
        # until envelope encryption exists (tracker DEF-028).
        sa.Column("source_url_encrypted", sa.LargeBinary(), nullable=False),
        sa.Column(
            "status", sa.String(length=30), server_default="unknown", nullable=False
        ),
        sa.Column("last_seen_at", _TS, nullable=True),
        _created_at(),
        _updated_at(),
        _org_fk("cameras"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cameras")),
        sa.UniqueConstraint("org_id", "name", name="camera_name_unique_per_org"),
    )
    op.create_index(op.f("ix_cameras_org_id"), "cameras", ["org_id"], unique=False)

    # -- rules -------------------------------------------------------------
    op.create_table(
        "rules",
        sa.Column("id", _PK, nullable=False),
        sa.Column("org_id", _PK, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("definition", _JSON, nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("priority", sa.Integer(), server_default="0", nullable=False),
        sa.Column("cooldown_s", sa.Integer(), server_default="0", nullable=False),
        _created_at(),
        _updated_at(),
        _org_fk("rules"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rules")),
        sa.UniqueConstraint("org_id", "name", name="rule_name_unique_per_org"),
    )
    op.create_index(op.f("ix_rules_org_id"), "rules", ["org_id"], unique=False)
    op.create_index(
        "ix_rules_org_id_enabled", "rules", ["org_id", "enabled"], unique=False
    )

    # -- api_keys ----------------------------------------------------------
    op.create_table(
        "api_keys",
        sa.Column("id", _PK, nullable=False),
        sa.Column("org_id", _PK, nullable=False),
        sa.Column("key_hash", sa.String(length=255), nullable=False),
        sa.Column("prefix", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=200), server_default="", nullable=False),
        sa.Column("last_used_at", _TS, nullable=True),
        sa.Column("revoked_at", _TS, nullable=True),
        _created_at(),
        _org_fk("api_keys"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_api_keys")),
        sa.UniqueConstraint("key_hash", name=op.f("uq_api_keys_key_hash")),
    )
    op.create_index(op.f("ix_api_keys_org_id"), "api_keys", ["org_id"], unique=False)

    # -- audit_log ---------------------------------------------------------
    op.create_table(
        "audit_log",
        sa.Column("id", _PK, nullable=False),
        sa.Column("org_id", _PK, nullable=False),
        # No FK to users on purpose: the audit trail must outlive the actor.
        sa.Column("actor_id", _PK, nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("target", sa.String(length=200), server_default="", nullable=False),
        sa.Column("metadata", _JSON, server_default="{}", nullable=False),
        _created_at(),
        _org_fk("audit_log"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_log")),
    )
    op.create_index(op.f("ix_audit_log_org_id"), "audit_log", ["org_id"], unique=False)
    op.create_index(
        "ix_audit_log_org_id_created_at",
        "audit_log",
        ["org_id", sa.text("created_at DESC")],
        unique=False,
    )

    # -- events: the hot table, partitioned by month -----------------------
    op.create_table(
        "events",
        sa.Column("id", _PK, nullable=False),
        # Part of the primary key: PostgreSQL requires the partition key to
        # appear in every unique constraint on a partitioned table.
        sa.Column("occurred_at", _TS, nullable=False),
        sa.Column("org_id", _PK, nullable=False),
        sa.Column("camera_id", _PK, nullable=True),
        sa.Column("rule_id", _PK, nullable=True),
        sa.Column("type", sa.String(length=60), nullable=False),
        sa.Column(
            "severity", sa.String(length=20), server_default="info", nullable=False
        ),
        sa.Column("message", sa.Text(), server_default="", nullable=False),
        sa.Column("metadata", _JSON, server_default="{}", nullable=False),
        sa.Column("clip_url", sa.String(length=1024), nullable=True),
        _created_at(),
        # SET NULL, not CASCADE: deleting a camera must not erase the history
        # of what it saw.
        sa.ForeignKeyConstraint(
            ["camera_id"],
            ["cameras.id"],
            name=op.f("fk_events_camera_id_cameras"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["rule_id"],
            ["rules.id"],
            name=op.f("fk_events_rule_id_rules"),
            ondelete="SET NULL",
        ),
        _org_fk("events"),
        sa.PrimaryKeyConstraint("id", "occurred_at", name=op.f("pk_events")),
        postgresql_partition_by="RANGE (occurred_at)",
    )

    if is_postgres:
        _create_event_partitions()

    op.create_index(op.f("ix_events_org_id"), "events", ["org_id"], unique=False)
    # The two V1 read patterns: an org's timeline, and one camera's timeline
    # within an org. On PostgreSQL these are declared on the partitioned parent
    # and propagate to every partition, present and future.
    op.create_index(
        "ix_events_org_id_occurred_at",
        "events",
        ["org_id", sa.text("occurred_at DESC")],
        unique=False,
    )
    op.create_index(
        "ix_events_org_id_camera_id_occurred_at",
        "events",
        ["org_id", "camera_id", sa.text("occurred_at DESC")],
        unique=False,
    )

    # -- event_actions: the durable outbox ---------------------------------
    op.create_table(
        "event_actions",
        sa.Column("id", _PK, nullable=False),
        sa.Column("org_id", _PK, nullable=False),
        sa.Column("event_id", _PK, nullable=False),
        sa.Column("event_occurred_at", _TS, nullable=False),
        sa.Column("action_type", sa.String(length=60), nullable=False),
        sa.Column(
            "status", sa.String(length=20), server_default="pending", nullable=False
        ),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("scheduled_at", _TS, nullable=True),
        sa.Column("completed_at", _TS, nullable=True),
        _created_at(),
        # Composite, because the parent's primary key is composite. This is the
        # tax on partitioning events, and it is cheaper than an unpartitioned
        # events table.
        sa.ForeignKeyConstraint(
            ["event_id", "event_occurred_at"],
            ["events.id", "events.occurred_at"],
            name="fk_event_actions_event",
            ondelete="CASCADE",
        ),
        _org_fk("event_actions"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_event_actions")),
    )
    op.create_index(
        op.f("ix_event_actions_org_id"), "event_actions", ["org_id"], unique=False
    )
    op.create_index(
        "ix_event_actions_event_id", "event_actions", ["event_id"], unique=False
    )
    # The delivery worker's claim query: "what is owed, oldest first".
    op.create_index(
        "ix_event_actions_status_scheduled_at",
        "event_actions",
        ["status", "scheduled_at"],
        unique=False,
    )

    # -- governance_log ----------------------------------------------------
    op.create_table(
        "governance_log",
        sa.Column("id", _PK, nullable=False),
        sa.Column("org_id", _PK, nullable=False),
        sa.Column("rule_id", _PK, nullable=True),
        sa.Column("verdict", sa.String(length=20), nullable=False),
        sa.Column("policy_id", sa.String(length=80), server_default="", nullable=False),
        sa.Column("reason", sa.Text(), server_default="", nullable=False),
        _created_at(),
        sa.ForeignKeyConstraint(
            ["rule_id"],
            ["rules.id"],
            name=op.f("fk_governance_log_rule_id_rules"),
            ondelete="SET NULL",
        ),
        _org_fk("governance_log"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_governance_log")),
    )
    op.create_index(
        op.f("ix_governance_log_org_id"), "governance_log", ["org_id"], unique=False
    )
    op.create_index(
        "ix_governance_log_org_id_created_at",
        "governance_log",
        ["org_id", sa.text("created_at DESC")],
        unique=False,
    )

    # -- Row-Level Security ------------------------------------------------
    # The database half of multi-tenancy. Without it, isolation rests entirely
    # on every future query remembering to filter by org_id, and code review is
    # not an invariant. SQLite has no equivalent, so the test suite exercises
    # the application half only — recorded as tracker DEF-034, not assumed away.
    if is_postgres:
        for table in _TENANT_TABLES:
            for statement in rls_statements(table):
                op.execute(statement)

        # Login has to find a user by email before a tenant is known. This adds
        # a second, SELECT-only policy on users rather than weakening the first.
        for statement in login_lookup_policy_statements("users"):
            op.execute(statement)


# ============================================
# Downgrade
# ============================================


def downgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # Policies vanish with their table, but dropping them explicitly keeps the
    # downgrade readable and makes the teardown helpers exercised code rather
    # than documentation.
    if is_postgres:
        for statement in login_lookup_teardown_statements("users"):
            op.execute(statement)
        for table in reversed(_TENANT_TABLES):
            for statement in rls_teardown_statements(table):
                op.execute(statement)

    op.drop_index("ix_governance_log_org_id_created_at", table_name="governance_log")
    op.drop_index(op.f("ix_governance_log_org_id"), table_name="governance_log")
    op.drop_table("governance_log")

    op.drop_index("ix_event_actions_status_scheduled_at", table_name="event_actions")
    op.drop_index("ix_event_actions_event_id", table_name="event_actions")
    op.drop_index(op.f("ix_event_actions_org_id"), table_name="event_actions")
    op.drop_table("event_actions")

    op.drop_index("ix_events_org_id_camera_id_occurred_at", table_name="events")
    op.drop_index("ix_events_org_id_occurred_at", table_name="events")
    op.drop_index(op.f("ix_events_org_id"), table_name="events")
    # Dropping a partitioned parent drops its partitions with it.
    op.drop_table("events")

    op.drop_index("ix_audit_log_org_id_created_at", table_name="audit_log")
    op.drop_index(op.f("ix_audit_log_org_id"), table_name="audit_log")
    op.drop_table("audit_log")

    op.drop_index(op.f("ix_api_keys_org_id"), table_name="api_keys")
    op.drop_table("api_keys")

    op.drop_index("ix_rules_org_id_enabled", table_name="rules")
    op.drop_index(op.f("ix_rules_org_id"), table_name="rules")
    op.drop_table("rules")

    op.drop_index(op.f("ix_cameras_org_id"), table_name="cameras")
    op.drop_table("cameras")

    op.drop_index(op.f("ix_users_org_id"), table_name="users")
    op.drop_table("users")

    op.drop_table("organizations")
