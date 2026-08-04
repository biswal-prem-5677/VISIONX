"""
VisionX — SQLAlchemy Declarative Base
=========================================
Shared metadata, naming conventions, and portable column types.

Why portability matters here
----------------------------
Production is PostgreSQL — that decision is not in question (JSONB, RLS,
partitioning). But CI runs with no database server, so the test suite executes
against SQLite. Any type that only exists on one dialect would split the schema
in two and let the tested shape drift from the deployed one.

Every type below therefore renders natively on PostgreSQL and degrades to a
working equivalent elsewhere:

======================  =====================  ======================
Alias                   PostgreSQL             SQLite
======================  =====================  ======================
``PKType``              ``UUID``               ``CHAR(32)``
``JSONType``            ``JSONB``              ``JSON`` (TEXT)
``TimestampType``       ``TIMESTAMPTZ``        ``DATETIME``
``EmailType``           ``VARCHAR(320)``       ``VARCHAR(320)``
======================  =====================  ======================

``EmailType`` is a plain string rather than ``citext``: case-insensitivity is
enforced by normalising to lower case at the application boundary
(``_normalize_email``), which behaves identically on both dialects. A ``citext``
column would silently stop being case-insensitive under SQLite and the tests
would not notice.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import DeclarativeBase, mapped_column

# ============================================
# Portable column types
# ============================================

#: Primary/foreign key type. ``sa.Uuid`` renders native ``UUID`` on PostgreSQL
#: and ``CHAR(32)`` elsewhere, while always presenting ``uuid.UUID`` in Python.
PKType = sa.Uuid(as_uuid=True)

#: Variable-shape document columns (``rules.definition``, ``events.metadata``).
#: JSONB on PostgreSQL for indexing and containment operators; JSON elsewhere.
JSONType = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")

#: All timestamps are timezone-aware. Storing naive local time is how audit
#: trails become unreadable after the first daylight-saving transition.
TimestampType = sa.DateTime(timezone=True)

#: RFC-ish upper bound on an address; see module docstring on case handling.
EmailType = sa.String(320)


def new_uuid() -> uuid.UUID:
    """Generate a primary key. Client-side so the ID is known before INSERT."""
    return uuid.uuid4()


def utcnow() -> datetime:
    """Timezone-aware 'now'. Used as a Python-side column default."""
    return datetime.now(timezone.utc)


# ============================================
# Declarative base
# ============================================

#: Deterministic constraint names.
#:
#: Without this, SQLAlchemy lets the database invent names for unnamed
#: constraints and indexes. Alembic then cannot generate a ``DROP CONSTRAINT``
#: for them, and SQLite's batch-migration mode — which rebuilds a table by copy
#: — cannot reproduce them. Both failures surface only once a migration needs to
#: *change* something, i.e. months after the mistake.
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Declarative base for every VisionX table."""

    metadata = sa.MetaData(naming_convention=NAMING_CONVENTION)


# ============================================
# Column factories
# ============================================

def pk_column():
    """Standard primary key column."""
    return mapped_column(PKType, primary_key=True, default=new_uuid)


def org_fk_column(*, index: bool = True):
    """
    The tenancy column.

    Every tenant-owned table carries this, and it is ``NOT NULL`` on all of
    them. A nullable ``org_id`` is a row that belongs to nobody, which means
    every tenant-scoped query has to decide what to do with it — and one of
    them will decide wrong.

    ``ON DELETE CASCADE`` makes "delete this organisation" a single statement,
    which is what a GDPR erasure request actually needs.
    """
    return mapped_column(
        PKType,
        sa.ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=index,
    )


def created_at_column():
    """Creation timestamp, defaulted on both the Python and SQL side."""
    return mapped_column(
        TimestampType,
        nullable=False,
        default=utcnow,
        server_default=sa.func.now(),
    )


def updated_at_column():
    """Last-modification timestamp, refreshed by the ORM on UPDATE."""
    return mapped_column(
        TimestampType,
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
        server_default=sa.func.now(),
    )


# ============================================
# Tenancy registry
# ============================================

def tenant_tables() -> list[str]:
    """
    Names of every table carrying ``org_id``, in dependency order.

    Used by the migration to enable Row-Level Security and by
    ``tests/test_db.py`` to assert that a newly added table cannot quietly skip
    tenancy. The list is derived from the metadata rather than hardcoded, so a
    new table is covered the moment it is defined.
    """
    return [
        name
        for name, table in Base.metadata.tables.items()
        if "org_id" in table.columns
    ]
