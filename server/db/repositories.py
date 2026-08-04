"""
VisionX — Tenant-Scoped Repositories
========================================
Query helpers that cannot be used to read another organisation's data.

The rule
--------
Every repository here is constructed with an ``org_id`` and injects it into
every statement it builds. There is no method that returns rows from more than
one organisation — with exactly one documented exception
(:func:`find_user_for_authentication`), which exists because login happens
before the caller has a tenant.

This is the application half of the isolation story; the database half is the
RLS policy described in :mod:`server.db.tenancy`. Neither is trusted alone.

Why not a mixin on the model
----------------------------
A ``Model.query_for(org)`` helper on the model class is easy to forget and easy
to bypass — the plain ``select(Model)`` is always one keystroke shorter. Routing
access through an object that has no unscoped path removes the shorter option.
"""

from __future__ import annotations

import uuid
from typing import Any, ClassVar, Generic, Optional, Sequence, TypeVar

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

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
from server.db.tenancy import allow_authentication_lookup

M = TypeVar("M")

#: Cap on any unbounded list call. Every list endpoint in the API was returning
#: unbounded results (ENGINEERING_REVIEW §5); the ceiling lives here so a
#: forgotten `limit=` in a route cannot page the whole events table into memory.
MAX_PAGE_SIZE = 500


def _coerce_uuid(value: Any, field: str) -> uuid.UUID:
    """Accept a UUID or its string form; reject anything else loudly."""
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (ValueError, AttributeError, TypeError) as exc:
        raise ValueError(f"{field} is not a valid UUID: {value!r}") from exc


# ============================================
# Organisations — the tenancy root
# ============================================


class OrganizationRepository:
    """
    Access to the ``organizations`` table itself.

    Not tenant-scoped, because an organisation *is* the tenant. Callers must
    therefore be either unauthenticated flows that create a tenant (signup) or
    platform-level operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self, *, name: str, slug: str, plan: str = "free", retention_days: int = 90
    ) -> Organization:
        org = Organization(
            name=name, slug=slug, plan=plan, retention_days=retention_days
        )
        self.session.add(org)
        await self.session.flush()
        return org

    async def get(self, org_id: Any) -> Optional[Organization]:
        return await self.session.get(Organization, _coerce_uuid(org_id, "org_id"))

    async def get_by_slug(self, slug: str) -> Optional[Organization]:
        result = await self.session.execute(
            sa.select(Organization).where(Organization.slug == slug)
        )
        return result.scalar_one_or_none()

    async def slug_exists(self, slug: str) -> bool:
        result = await self.session.execute(
            sa.select(sa.literal(1)).where(
                sa.exists().where(Organization.slug == slug)
            )
        )
        return result.scalar() is not None


# ============================================
# Tenant-scoped base
# ============================================


class TenantRepository(Generic[M]):
    """
    Base for every repository over an ``org_id``-carrying table.

    Subclasses set :attr:`model`. Construction validates that the model is
    actually tenant-owned, so a table that forgets ``org_id`` fails at import
    of the repository rather than at the first cross-tenant leak.
    """

    model: ClassVar[Any]

    def __init__(self, session: AsyncSession, org_id: Any) -> None:
        if getattr(self.model, "org_id", None) is None:
            raise TypeError(
                f"{self.model.__name__} has no org_id column and cannot be "
                f"accessed through a TenantRepository."
            )
        self.session = session
        self.org_id = _coerce_uuid(org_id, "org_id")

    # -- query construction ------------------------------------------------

    def select(self) -> sa.Select:
        """A ``SELECT`` already filtered to this tenant. The only entry point."""
        return sa.select(self.model).where(self.model.org_id == self.org_id)

    # -- reads -------------------------------------------------------------

    async def get(self, row_id: Any) -> Optional[M]:
        """
        Fetch one row by id **within this tenant**.

        Deliberately not ``session.get()``: that looks up by primary key alone
        and would happily return another organisation's row given its id.
        """
        result = await self.session.execute(
            self.select().where(self.model.id == _coerce_uuid(row_id, "id"))
        )
        return result.scalars().first()

    async def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        order_by: Optional[Any] = None,
    ) -> Sequence[M]:
        """List rows for this tenant. Always bounded — see :data:`MAX_PAGE_SIZE`."""
        limit = max(1, min(int(limit), MAX_PAGE_SIZE))
        stmt = self.select().limit(limit).offset(max(0, int(offset)))
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self) -> int:
        result = await self.session.execute(
            sa.select(sa.func.count())
            .select_from(self.model)
            .where(self.model.org_id == self.org_id)
        )
        return int(result.scalar_one())

    # -- writes ------------------------------------------------------------

    async def add(self, **fields: Any) -> M:
        """
        Insert a row into this tenant.

        ``org_id`` is set from the repository, not from ``fields`` — passing one
        is rejected rather than silently overridden, because a caller who
        supplies it believes it is being honoured.
        """
        if "org_id" in fields:
            raise ValueError(
                "org_id is set by the repository and must not be passed to add()"
            )
        instance = self.model(org_id=self.org_id, **fields)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def delete(self, row_id: Any) -> bool:
        """Delete one row within this tenant. Returns whether anything matched."""
        row = await self.get(row_id)
        if row is None:
            return False
        await self.session.delete(row)
        await self.session.flush()
        return True


# ============================================
# Concrete repositories
# ============================================


class UserRepository(TenantRepository[User]):
    """Users within one organisation."""

    model = User

    async def get_by_email(self, email: str) -> Optional[User]:
        """Look up a user by address **within this tenant**."""
        result = await self.session.execute(
            self.select().where(User.email == email.strip().lower())
        )
        return result.scalars().first()


class CameraRepository(TenantRepository[Camera]):
    model = Camera


class RuleRepository(TenantRepository[Rule]):
    model = Rule

    async def enabled(self, *, limit: int = 200) -> Sequence[Rule]:
        """Enabled rules, highest priority first — the engine's load query."""
        result = await self.session.execute(
            self.select()
            .where(Rule.enabled.is_(True))
            .order_by(Rule.priority.desc())
            .limit(max(1, min(int(limit), MAX_PAGE_SIZE)))
        )
        return result.scalars().all()


class EventRepository(TenantRepository[Event]):
    model = Event

    async def recent(self, *, limit: int = 50, offset: int = 0) -> Sequence[Event]:
        """The org timeline, newest first. Hits ``ix_events_org_id_occurred_at``."""
        return await self.list(
            limit=limit, offset=offset, order_by=Event.occurred_at.desc()
        )


class EventActionRepository(TenantRepository[EventAction]):
    model = EventAction


class ApiKeyRepository(TenantRepository[ApiKey]):
    model = ApiKey


class AuditLogRepository(TenantRepository[AuditLog]):
    model = AuditLog


class GovernanceLogRepository(TenantRepository[GovernanceLog]):
    model = GovernanceLog


# ============================================
# The one deliberate cross-tenant read
# ============================================


async def find_user_for_authentication(
    session: AsyncSession, email: str
) -> Optional[User]:
    """
    Find a user by email address across all organisations.

    **This is the only unscoped read in the codebase, and it exists for one
    reason:** at login the caller has presented an email and nothing else, so
    there is no tenant to scope to yet. The tenant is a *result* of
    authentication, not an input to it.

    Under PostgreSQL RLS this query would be rejected by the ``users`` tenant
    policy, so the function opts the transaction into the narrow, SELECT-only
    login exemption itself (:func:`server.db.tenancy.allow_authentication_lookup`).
    Doing it here rather than at the call site means the exemption travels with
    the one query that needs it and cannot be forgotten — or copied.

    Consequences, accepted knowingly:

    - It confirms nothing to the caller. ``server.api.routes.auth`` runs a
      constant-work password verification whether or not this returns a row, so
      the response does not reveal whether an address is registered.
    - It must never be called from a route that already has a ``CurrentUser``.
      Use :class:`UserRepository` there.
    """
    await allow_authentication_lookup(session)
    result = await session.execute(
        sa.select(User).where(User.email == email.strip().lower())
    )
    return result.scalars().first()


__all__ = [
    "ApiKeyRepository",
    "AuditLogRepository",
    "CameraRepository",
    "EventActionRepository",
    "EventRepository",
    "GovernanceLogRepository",
    "MAX_PAGE_SIZE",
    "OrganizationRepository",
    "RuleRepository",
    "TenantRepository",
    "UserRepository",
    "find_user_for_authentication",
]
