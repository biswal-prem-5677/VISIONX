"""
VisionX — Tenant Isolation
==============================
Row-Level Security plumbing for the PostgreSQL side of multi-tenancy.

The two layers
--------------
Tenant isolation is enforced twice, on purpose:

1. **Application** — :mod:`server.db.repositories` cannot construct a query
   without an ``org_id`` filter.
2. **Database** — RLS policies created by migration ``0001`` reject any row
   whose ``org_id`` does not match the current session's tenant setting.

Layer 1 catches ordinary mistakes. Layer 2 catches the mistake layer 1 is made
of: a developer writing a raw ``select()`` because the repository did not have
the method they wanted. Only layer 2 survives that, which is why the review
calls RLS "the cheapest insurance you will ever buy" (ENGINEERING_REVIEW §4.3).

How the tenant reaches the database
-----------------------------------
PostgreSQL policies read a session-local GUC. :func:`set_tenant` sets it with
``SET LOCAL``, which is scoped to the enclosing transaction and therefore
cannot leak into the next request that borrows the same pooled connection —
``SET`` (without ``LOCAL``) would.

On SQLite the function is a no-op: there is no RLS to configure. The test suite
consequently exercises layer 1 only, which is stated plainly in
``tests/test_db.py`` and tracked as DEF-034 rather than assumed away.
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from typing import AsyncIterator, Union

import sqlalchemy as sa
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

#: The PostgreSQL session setting read by every RLS policy.
TENANT_SETTING = "app.current_org"

#: A second setting, read only by the ``users`` login policy. Login has to find
#: a user by email *before* a tenant is known, so it needs a narrow exemption
#: from tenant scoping. Giving that exemption its own switch — rather than
#: letting an unset tenant mean "see everything" — keeps the exemption to the
#: one transaction that asked for it. See :func:`allow_authentication_lookup`.
AUTH_LOOKUP_SETTING = "app.login_lookup"

OrgId = Union[str, uuid.UUID]


def _coerce_org_id(org_id: OrgId) -> str:
    """
    Validate and stringify a tenant id.

    The value is interpolated into a ``SET LOCAL`` statement, which cannot take
    a bind parameter. Parsing it as a UUID first is what makes that safe: a
    value that survives ``uuid.UUID()`` contains nothing that can end a SQL
    statement. Never relax this into a plain ``str()``.
    """
    try:
        return str(uuid.UUID(str(org_id)))
    except (ValueError, AttributeError, TypeError) as exc:
        raise ValueError(f"org_id is not a valid UUID: {org_id!r}") from exc


async def set_tenant(session: AsyncSession, org_id: OrgId) -> None:
    """
    Bind the current transaction to one organisation.

    Must be called inside a transaction. ``SET LOCAL`` outside one is silently
    discarded by PostgreSQL, which would leave the policies evaluating against
    an unset tenant and returning nothing — a confusing "the data disappeared"
    failure rather than a loud one.
    """
    safe_id = _coerce_org_id(org_id)

    if session.bind is None or session.bind.dialect.name != "postgresql":
        logger.debug(
            f"set_tenant({safe_id}) is a no-op on "
            f"{getattr(session.bind, 'dialect', None) and session.bind.dialect.name}; "
            f"RLS exists only on PostgreSQL"
        )
        return

    if not session.in_transaction():
        raise RuntimeError(
            "set_tenant() must run inside a transaction — SET LOCAL outside one "
            "is discarded, which would silently disable tenant scoping."
        )

    await session.execute(sa.text(f"SET LOCAL {TENANT_SETTING} = '{safe_id}'"))


async def clear_tenant(session: AsyncSession) -> None:
    """Reset the tenant setting. Rarely needed — ``SET LOCAL`` expires anyway."""
    if session.bind is not None and session.bind.dialect.name == "postgresql":
        await session.execute(sa.text(f"RESET {TENANT_SETTING}"))


async def allow_authentication_lookup(session: AsyncSession) -> None:
    """
    Permit one transaction to find a user by email across all organisations.

    Login is the only operation that legitimately needs this: the caller has
    presented an address and nothing else, so the tenant is a *result* of
    authentication rather than an input to it.

    The exemption is deliberately shaped to be small and visible:

    - It is a separate setting from :data:`TENANT_SETTING`, so "no tenant set"
      never means "see everything".
    - ``SET LOCAL`` scopes it to the current transaction, so it cannot outlive
      the login attempt or leak to the next request on a pooled connection.
    - The matching policy is ``FOR SELECT`` only — this can read a user row, and
      cannot write one.

    No-op outside PostgreSQL.
    """
    if session.bind is None or session.bind.dialect.name != "postgresql":
        return

    if not session.in_transaction():
        raise RuntimeError(
            "allow_authentication_lookup() must run inside a transaction — "
            "SET LOCAL outside one is discarded."
        )

    await session.execute(sa.text(f"SET LOCAL {AUTH_LOOKUP_SETTING} = 'on'"))


@asynccontextmanager
async def tenant_scope(session: AsyncSession, org_id: OrgId) -> AsyncIterator[AsyncSession]:
    """
    Run a block of work as one tenant.

    Usage::

        async with database.session() as session:
            async with tenant_scope(session, user.org_id):
                ...
    """
    if not session.in_transaction():
        await session.begin()
    await set_tenant(session, org_id)
    yield session


# ============================================
# Policy DDL — used by the Alembic migration
# ============================================

def rls_statements(table: str) -> list[str]:
    """
    The DDL that puts one table under tenant policy.

    ``FORCE ROW LEVEL SECURITY`` is the important line. Plain ``ENABLE`` exempts
    the table's owner, and application deployments routinely connect as the
    owner — so ``ENABLE`` alone produces a database that reports RLS as active
    while enforcing nothing for the only role that matters.

    The ``USING`` clause uses ``current_setting(…, true)``: the ``true`` makes a
    missing setting return NULL instead of raising. NULL fails the comparison,
    so a connection that never called :func:`set_tenant` sees zero rows. Failing
    to *closed* rather than to *error* keeps an unset tenant from looking like a
    database outage — and it never looks like success.
    """
    return [
        f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY",
        f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY",
        f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table}",
        (
            f"CREATE POLICY {table}_tenant_isolation ON {table} "
            f"USING (org_id = NULLIF(current_setting('{TENANT_SETTING}', true), '')::uuid) "
            f"WITH CHECK (org_id = NULLIF(current_setting('{TENANT_SETTING}', true), '')::uuid)"
        ),
    ]


def rls_teardown_statements(table: str) -> list[str]:
    """Reverse of :func:`rls_statements`, for migration downgrade."""
    return [
        f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table}",
        f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY",
        f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY",
    ]


def login_lookup_policy_statements(table: str = "users") -> list[str]:
    """
    The extra ``users`` policy that makes login possible under RLS.

    PostgreSQL combines permissive policies with OR, so this sits alongside
    ``users_tenant_isolation`` rather than replacing it: a row is visible if it
    belongs to the current tenant **or** if this transaction has explicitly
    opted into an authentication lookup (:func:`allow_authentication_lookup`).

    ``FOR SELECT`` is load-bearing. Without it the same switch would also permit
    cross-tenant writes, turning a login affordance into a privilege escalation.
    """
    return [
        f"DROP POLICY IF EXISTS {table}_authentication_lookup ON {table}",
        (
            f"CREATE POLICY {table}_authentication_lookup ON {table} "
            f"FOR SELECT "
            f"USING (current_setting('{AUTH_LOOKUP_SETTING}', true) = 'on')"
        ),
    ]


def login_lookup_teardown_statements(table: str = "users") -> list[str]:
    """Reverse of :func:`login_lookup_policy_statements`."""
    return [f"DROP POLICY IF EXISTS {table}_authentication_lookup ON {table}"]
