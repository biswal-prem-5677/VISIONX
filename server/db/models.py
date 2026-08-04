"""
VisionX — Database Models
=============================
The nine tables that make VisionX a product rather than a process.

Scope
-----
This is the V1 schema recommended in ENGINEERING_REVIEW.md §4.2 — nine tables,
not ninety. Every tenant-owned table carries ``org_id``; that column is the
whole point of this module. Retrofitting tenancy after launch is a 6–10 week
refactor, so it goes in before there is a single row to migrate.

Isolation is enforced twice, deliberately:

1. **In the application** — :mod:`server.db.repositories` refuses to build a
   query without an ``org_id`` filter.
2. **In the database** — Row-Level Security policies (migration ``0001``) make
   cross-tenant reads impossible even from a hand-written query or a psql
   session.

Layer 1 alone is a code-review invariant, and code review is not an invariant.

What is *not* here
------------------
Per-frame detections. They are aggregated at the edge and only rule-triggered
events are persisted. A 30 fps camera writing one row per frame is 78 million
rows per camera per month, and none of them answer a question anyone asks.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.db.base import (
    Base,
    EmailType,
    JSONType,
    PKType,
    TimestampType,
    created_at_column,
    org_fk_column,
    pk_column,
    updated_at_column,
    utcnow,
)

# ============================================
# Organisations — the tenancy root
# ============================================


class Organization(Base):
    """
    A customer account. Every other row in the system hangs off one of these.

    ``slug`` exists for URLs and support conversations ("the acme-logistics
    account"). It is unique and immutable by convention — renaming an org
    changes ``name``, never ``slug``.
    """

    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = pk_column()
    name: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    slug: Mapped[str] = mapped_column(sa.String(80), nullable=False, unique=True)
    plan: Mapped[str] = mapped_column(
        sa.String(40), nullable=False, server_default="free"
    )

    #: Event/clip retention in days. Org-configurable because it is both a cost
    #: lever and a GDPR data-minimisation control.
    retention_days: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default="90"
    )

    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()

    users: Mapped[list["User"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Organization {self.slug}>"


# ============================================
# Users
# ============================================


class User(Base):
    """
    A person who can sign in.

    ``email`` is globally unique, not unique-per-org. That is a deliberate V1
    simplification: one address, one account. Supporting the same human in two
    organisations means an ``org_memberships`` join table, and that is a real
    feature with real UI, not a column tweak — it waits until a customer asks.

    ``password_hash`` is produced by :mod:`server.auth.password` (bcrypt, with
    an stdlib scrypt fallback). Nothing else may write this column.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = pk_column()
    org_id: Mapped[uuid.UUID] = org_fk_column()

    email: Mapped[str] = mapped_column(EmailType, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    name: Mapped[str] = mapped_column(sa.String(200), nullable=False, server_default="")
    role: Mapped[str] = mapped_column(
        sa.String(40), nullable=False, server_default="user"
    )
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.true()
    )

    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        TimestampType, nullable=True
    )
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()

    organization: Mapped[Organization] = relationship(back_populates="users")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<User {self.email}>"


# ============================================
# Cameras
# ============================================


class Camera(Base):
    """
    A video source belonging to an organisation.

    ``source_url_encrypted`` is ``BYTEA``/``BLOB`` rather than text because an
    RTSP URL embeds ``user:password@``. Storing it as plaintext puts every
    customer's camera credentials one ``SELECT`` away from anyone with read
    access to the database or a backup of it.

    .. warning::
       The envelope-encryption helper that must write this column does **not
       exist yet** (tracker DEF-028). There is deliberately no camera-write path
       in the API this run, so nothing can put plaintext in a column whose name
       promises ciphertext. Do not add one before DEF-028 closes.
    """

    __tablename__ = "cameras"

    id: Mapped[uuid.UUID] = pk_column()
    org_id: Mapped[uuid.UUID] = org_fk_column()

    name: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    source_url_encrypted: Mapped[bytes] = mapped_column(sa.LargeBinary, nullable=False)
    status: Mapped[str] = mapped_column(
        sa.String(30), nullable=False, server_default="unknown"
    )
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(
        TimestampType, nullable=True
    )

    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()

    __table_args__ = (
        sa.UniqueConstraint("org_id", "name", name="camera_name_unique_per_org"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Camera {self.name}>"


# ============================================
# Rules
# ============================================


class Rule(Base):
    """
    A persisted decision rule, consumed by :mod:`decision.engine`.

    ``definition`` is JSONB because rule shapes genuinely vary (conditions,
    zones, schedules) and the engine — not the database — interprets them. The
    fields that are *filtered on* (``enabled``, ``priority``, ``cooldown_s``)
    are real columns, because JSONB you filter on is a table you have not
    designed yet.
    """

    __tablename__ = "rules"

    id: Mapped[uuid.UUID] = pk_column()
    org_id: Mapped[uuid.UUID] = org_fk_column()

    name: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    definition: Mapped[dict[str, Any]] = mapped_column(JSONType, nullable=False)
    enabled: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.true()
    )
    priority: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default="0"
    )
    cooldown_s: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default="0"
    )

    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()

    __table_args__ = (
        sa.UniqueConstraint("org_id", "name", name="rule_name_unique_per_org"),
        sa.Index("ix_rules_org_id_enabled", "org_id", "enabled"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Rule {self.name}>"


# ============================================
# Events — the hot table
# ============================================


class Event(Base):
    """
    A rule-triggered incident. The busiest table in the system.

    **Composite primary key.** ``(id, occurred_at)`` rather than ``id`` alone,
    because PostgreSQL requires the partition key to be part of every unique
    constraint on a partitioned table. Paying that cost now avoids rebuilding a
    live table later — the reason the review insists on partitioning "from day
    one" (ENGINEERING_REVIEW.md §4.3).

    **Partitioning.** ``postgresql_partition_by`` is a dialect-level kwarg: on
    PostgreSQL the table is declared ``PARTITION BY RANGE (occurred_at)`` and
    migration ``0001`` creates the monthly children plus a ``DEFAULT`` partition
    so an insert can never fail for want of one. On SQLite the kwarg is ignored
    and an ordinary table is created, so the tested column shape is identical
    even though the storage layout is not.

    ``camera_id`` and ``rule_id`` are nullable with ``ON DELETE SET NULL``:
    deleting a camera must not erase the history of what it saw.
    """

    __tablename__ = "events"

    id: Mapped[uuid.UUID] = pk_column()

    #: Part of the primary key — see the class docstring.
    occurred_at: Mapped[datetime] = mapped_column(
        TimestampType, primary_key=True, nullable=False, default=utcnow
    )

    org_id: Mapped[uuid.UUID] = org_fk_column()
    camera_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PKType, sa.ForeignKey("cameras.id", ondelete="SET NULL"), nullable=True
    )
    rule_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PKType, sa.ForeignKey("rules.id", ondelete="SET NULL"), nullable=True
    )

    type: Mapped[str] = mapped_column(sa.String(60), nullable=False)
    severity: Mapped[str] = mapped_column(
        sa.String(20), nullable=False, server_default="info"
    )
    message: Mapped[str] = mapped_column(sa.Text, nullable=False, server_default="")

    #: Named ``metadata`` in SQL; ``metadata`` is reserved on the declarative
    #: class, so the Python attribute differs from the column name.
    event_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONType, nullable=False, server_default="{}"
    )

    #: Object-storage key for the evidence clip. Nullable until the clip lands —
    #: the event is recorded first so an upload failure cannot lose the alert.
    clip_url: Mapped[Optional[str]] = mapped_column(sa.String(1024), nullable=True)

    created_at: Mapped[datetime] = created_at_column()

    __table_args__ = (
        # Covers the two V1 read patterns: an org's timeline, and one camera's
        # timeline within an org. Resist adding more until pg_stat_statements
        # asks for them.
        sa.Index("ix_events_org_id_occurred_at", "org_id", sa.text("occurred_at DESC")),
        sa.Index(
            "ix_events_org_id_camera_id_occurred_at",
            "org_id",
            "camera_id",
            sa.text("occurred_at DESC"),
        ),
        {"postgresql_partition_by": "RANGE (occurred_at)"},
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Event {self.type} {self.severity}>"


class EventAction(Base):
    """
    One delivery attempt record for one action of one event — the durable
    half of the outbox pattern.

    This table is why it exists: today a failed action is retried in memory and
    then dropped into an in-process dead-letter deque that a restart erases
    (tracker DEF-013 / DEF-022). For an alerting product, an alert that vanished
    and an alert that was delivered must never be indistinguishable, and only a
    row on disk can tell them apart.

    The foreign key is composite — ``(event_id, event_occurred_at)`` — because
    the parent's primary key is composite. That is the tax on partitioning, and
    it is cheaper than a partition-less events table.

    .. note::
       The event engine does not write this table yet (tracker DEF-022). The
       schema lands first so the writer is not simultaneously inventing a shape
       and a migration.
    """

    __tablename__ = "event_actions"

    id: Mapped[uuid.UUID] = pk_column()
    org_id: Mapped[uuid.UUID] = org_fk_column()

    event_id: Mapped[uuid.UUID] = mapped_column(PKType, nullable=False)
    event_occurred_at: Mapped[datetime] = mapped_column(TimestampType, nullable=False)

    action_type: Mapped[str] = mapped_column(sa.String(60), nullable=False)

    #: ``pending`` → ``sent`` | ``failed`` | ``dead``. ``dead`` means the retry
    #: budget is exhausted and a human must look; it is never a silent state.
    status: Mapped[str] = mapped_column(
        sa.String(20), nullable=False, server_default="pending"
    )
    attempts: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default="0"
    )
    last_error: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)

    scheduled_at: Mapped[Optional[datetime]] = mapped_column(
        TimestampType, nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        TimestampType, nullable=True
    )
    created_at: Mapped[datetime] = created_at_column()

    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["event_id", "event_occurred_at"],
            ["events.id", "events.occurred_at"],
            ondelete="CASCADE",
            name="fk_event_actions_event",
        ),
        sa.Index("ix_event_actions_event_id", "event_id"),
        # The claim query for a delivery worker: "what is owed, oldest first".
        sa.Index("ix_event_actions_status_scheduled_at", "status", "scheduled_at"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<EventAction {self.action_type} {self.status}>"


# ============================================
# Access, audit, governance
# ============================================


class ApiKey(Base):
    """
    A machine credential for an organisation.

    Only ``key_hash`` is stored — the plaintext key is shown once at creation
    and is unrecoverable afterwards. ``prefix`` is the first few visible
    characters, kept so the UI can say *which* key without being able to
    reconstruct it.

    Revocation is a timestamp, not a delete: an audit trail needs to be able to
    say that a key existed and when it stopped working.
    """

    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = pk_column()
    org_id: Mapped[uuid.UUID] = org_fk_column()

    key_hash: Mapped[str] = mapped_column(sa.String(255), nullable=False, unique=True)
    prefix: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    name: Mapped[str] = mapped_column(sa.String(200), nullable=False, server_default="")

    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        TimestampType, nullable=True
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(TimestampType, nullable=True)
    created_at: Mapped[datetime] = created_at_column()

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<ApiKey {self.prefix}…>"


class AuditLog(Base):
    """
    Who did what, to what, when.

    ``actor_id`` is a bare UUID with no foreign key on purpose: the audit trail
    must outlive the user. A ``users`` FK with ``ON DELETE CASCADE`` would erase
    exactly the records an investigation needs, and ``RESTRICT`` would make user
    deletion impossible.
    """

    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = pk_column()
    org_id: Mapped[uuid.UUID] = org_fk_column()

    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(PKType, nullable=True)
    action: Mapped[str] = mapped_column(sa.String(80), nullable=False)
    target: Mapped[str] = mapped_column(
        sa.String(200), nullable=False, server_default=""
    )
    audit_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONType, nullable=False, server_default="{}"
    )
    created_at: Mapped[datetime] = created_at_column()

    __table_args__ = (
        sa.Index("ix_audit_log_org_id_created_at", "org_id", sa.text("created_at DESC")),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<AuditLog {self.action}>"


class GovernanceLog(Base):
    """
    The verdict of the privacy/ethics gate for a single decision.

    Durable because it is evidence. The governance layer currently keeps this
    in an in-memory list that a restart erases (tracker DEF-029), which means
    the one artefact that proves the product blocked a biometric action is also
    the one artefact that does not survive a deploy.
    """

    __tablename__ = "governance_log"

    id: Mapped[uuid.UUID] = pk_column()
    org_id: Mapped[uuid.UUID] = org_fk_column()

    rule_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PKType, sa.ForeignKey("rules.id", ondelete="SET NULL"), nullable=True
    )
    verdict: Mapped[str] = mapped_column(sa.String(20), nullable=False)
    policy_id: Mapped[str] = mapped_column(
        sa.String(80), nullable=False, server_default=""
    )
    reason: Mapped[str] = mapped_column(sa.Text, nullable=False, server_default="")
    created_at: Mapped[datetime] = created_at_column()

    __table_args__ = (
        sa.Index(
            "ix_governance_log_org_id_created_at", "org_id", sa.text("created_at DESC")
        ),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<GovernanceLog {self.verdict}>"


__all__ = [
    "ApiKey",
    "AuditLog",
    "Base",
    "Camera",
    "Event",
    "EventAction",
    "GovernanceLog",
    "Organization",
    "Rule",
    "User",
]
