"""
VisionX — Database Session Management
=========================================
Engine construction, URL resolution, and the FastAPI session dependency.

Fail-closed URL resolution
--------------------------
This module mirrors the pattern established in
:mod:`server.auth.jwt_handler`: development gets a convenient default,
production gets a startup crash. A deployment that forgets ``DATABASE_URL``
must not boot onto a throwaway local file and quietly accept writes that
nobody will ever read back.

Development / CI default
------------------------
``sqlite+aiosqlite:///./visionx-dev.db`` — a real file, so state survives a
restart on a laptop exactly as it does in production. CI overrides it with a
temporary path (``tests/conftest.py``).

SQLite is a *test and development* target only. PostgreSQL-specific behaviour
that SQLite cannot express — Row-Level Security, range partitioning, JSONB
operators — is applied by the Alembic migration and is therefore **not
exercised by the test suite**. That gap is recorded as tracker DEF-034 rather
than papered over.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

import sqlalchemy as sa
from loguru import logger
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from server.db.base import Base

#: Used when nothing is configured and we are not in production.
_DEV_FALLBACK_URL = "sqlite+aiosqlite:///./visionx-dev.db"


def _is_production() -> bool:
    """
    True when the process is running in a production-like environment.

    Duplicated from :mod:`server.auth.jwt_handler` rather than imported: the
    database layer must not depend on the auth layer, and this is four lines.
    """
    env = (
        os.getenv("VISIONX_ENV") or os.getenv("APP_ENV") or "development"
    ).strip().lower()
    return env in {"production", "prod", "staging"}


def resolve_database_url(explicit: str = "") -> str:
    """
    Resolve the database URL, refusing to guess in production.

    Args:
        explicit: Overrides the environment. Used by tests.

    Returns:
        A SQLAlchemy async URL.

    Raises:
        RuntimeError: In production when ``DATABASE_URL`` is unset, or when it
            points at SQLite. Both are configuration mistakes that would
            otherwise surface as data loss rather than as a failed deploy.
    """
    url = (explicit or os.getenv("DATABASE_URL", "")).strip()

    if not _is_production():
        if not url:
            logger.warning(
                f"DATABASE_URL not set — falling back to {_DEV_FALLBACK_URL}. "
                f"This is refused when VISIONX_ENV=production."
            )
            return _DEV_FALLBACK_URL
        return _normalize_url(url)

    # --- Production: fail closed ---
    if not url:
        raise RuntimeError(
            "DATABASE_URL is required in production and is not set. "
            "Expected a PostgreSQL URL, e.g. "
            "postgresql+asyncpg://user:pass@host:5432/visionx"
        )

    normalized = _normalize_url(url)

    if normalized.startswith("sqlite"):
        raise RuntimeError(
            "DATABASE_URL points at SQLite, which is a development-only target. "
            "It has no Row-Level Security, so multi-tenant isolation would rest "
            "on application code alone. Refusing to start in production."
        )

    return normalized


def _normalize_url(url: str) -> str:
    """
    Upgrade a sync driver URL to its async equivalent.

    Managed Postgres providers hand out ``postgresql://…`` URLs. Passing one to
    an async engine fails with a driver error that reads like a network problem,
    so translate instead of making every operator learn the distinction.
    """
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://"):]
    if url.startswith("postgres://"):  # Heroku-style
        return "postgresql+asyncpg://" + url[len("postgres://"):]
    if url.startswith("sqlite://") and "+aiosqlite" not in url:
        return "sqlite+aiosqlite://" + url[len("sqlite://"):]
    return url


class Database:
    """
    Owns the async engine and session factory for one process.

    Constructed at import time so a misconfigured production deployment fails
    during startup rather than on the first request that needs a row.
    """

    def __init__(self, url: str = "") -> None:
        self._url = resolve_database_url(url)
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    # -- lifecycle ---------------------------------------------------------

    async def connect(self) -> None:
        """Create the engine and session factory. Idempotent."""
        if self._engine is not None:
            return

        kwargs: dict = {"echo": False, "future": True}

        if self.is_sqlite:
            # An in-memory SQLite database is per-connection, so a pooled engine
            # would hand different requests different empty databases.
            if ":memory:" in self._url:
                from sqlalchemy.pool import StaticPool

                kwargs["poolclass"] = StaticPool
                kwargs["connect_args"] = {"check_same_thread": False}
        else:
            kwargs["pool_size"] = int(os.getenv("DB_POOL_SIZE", "10"))
            kwargs["max_overflow"] = int(os.getenv("DB_MAX_OVERFLOW", "20"))
            kwargs["pool_pre_ping"] = True

        self._engine = create_async_engine(self._url, **kwargs)

        if self.is_sqlite:
            _enable_sqlite_foreign_keys(self._engine)

        self._session_factory = async_sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False
        )

        logger.info(f"Database engine ready ({self.safe_url})")

    async def disconnect(self) -> None:
        """Dispose of the connection pool."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Database engine disposed")

    async def create_all(self) -> None:
        """
        Create tables directly from the models.

        **Development and tests only.** PostgreSQL is migrated with Alembic
        (``alembic upgrade head``); ``create_all`` skips the Row-Level Security
        policies and range partitions that live in migration ``0001``, so using
        it against Postgres would produce a schema that looks right and isolates
        nothing.

        ``tests/test_db.py::TestMigrationParity`` asserts that the two paths
        agree on tables and columns, so this convenience cannot drift into a
        second, divergent schema definition.
        """
        if not self.is_sqlite:
            raise RuntimeError(
                "create_all() is development-only. Run 'alembic upgrade head' "
                "against PostgreSQL — create_all omits RLS policies and "
                "partitions, which is not a schema you want in production."
            )

        assert self._engine is not None, "connect() must be called first"
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.debug("SQLite development schema created from models")

    # -- access ------------------------------------------------------------

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """
        Yield a session inside a transaction, committing on success.

        Rolls back and re-raises on any exception — a half-applied write is
        worse than a failed one.
        """
        if self._session_factory is None:
            raise RuntimeError("Database is not connected. Call connect() first.")

        session = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def ping(self) -> bool:
        """
        True if the database answers a trivial query.

        Used by ``/health``. A health check that reports healthy without
        touching its dependencies is worse than no health check, because an
        orchestrator will keep routing traffic to a process that cannot serve it.
        """
        if self._engine is None:
            return False
        try:
            async with self._engine.connect() as conn:
                await conn.execute(sa.text("SELECT 1"))
            return True
        except Exception as e:  # noqa: BLE001 - a probe must not raise
            logger.warning(f"Database ping failed: {type(e).__name__}: {e}")
            return False

    # -- introspection -----------------------------------------------------

    @property
    def url(self) -> str:
        return self._url

    @property
    def safe_url(self) -> str:
        """The URL with any password removed, for logs and error messages."""
        try:
            return sa.engine.make_url(self._url).render_as_string(hide_password=True)
        except Exception:  # noqa: BLE001 - never let logging raise
            return "<unparseable database url>"

    @property
    def is_sqlite(self) -> bool:
        return self._url.startswith("sqlite")

    @property
    def is_connected(self) -> bool:
        return self._engine is not None

    @property
    def engine(self) -> AsyncEngine:
        if self._engine is None:
            raise RuntimeError("Database is not connected. Call connect() first.")
        return self._engine


def _enable_sqlite_foreign_keys(engine: AsyncEngine) -> None:
    """
    Turn on SQLite foreign-key enforcement.

    SQLite ignores foreign keys unless asked, per connection. Without this the
    test suite would happily insert a user into a nonexistent organisation and
    every cascade test would pass for the wrong reason.
    """
    from sqlalchemy import event

    @event.listens_for(engine.sync_engine, "connect")
    def _set_pragma(dbapi_connection, _record):  # pragma: no cover - driver hook
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# ============================================
# Process-wide instance + FastAPI dependency
# ============================================

#: Shared instance. Constructing it here means URL resolution — and therefore
#: the production fail-closed check — happens at import, not at first request.
database = Database()


async def get_db() -> AsyncIterator[AsyncSession]:
    """
    FastAPI dependency yielding a transactional session.

    Usage::

        @router.get("/things")
        async def list_things(db: AsyncSession = Depends(get_db)): ...
    """
    async with database.session() as session:
        yield session
