"""
Alembic migration environment for VisionX.

Two deliberate choices
----------------------
**Migrations run synchronously.** The application uses an async engine; this
does not. Migrations are a serial, one-at-a-time operational task, so async
buys nothing and costs an event loop inside a CLI. The async URL is translated
to its sync driver equivalent by :func:`_sync_url`.

**The URL comes from the application, not from alembic.ini.** Reusing
``resolve_database_url()`` means ``alembic upgrade head`` obeys the same
fail-closed rule the server does: in production, an unset ``DATABASE_URL`` is
an error rather than a silent connection to a local database that nobody
intended to migrate.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Registers every model on Base.metadata — see server/db/__init__.py.
from server.db import Base
from server.db.session import resolve_database_url

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _sync_url() -> str:
    """
    Resolve the database URL and swap the async driver for a sync one.

    An explicit ``-x url=...`` wins over everything else; the test suite uses it
    to migrate a throwaway SQLite file.
    """
    override = context.get_x_argument(as_dictionary=True).get("url")
    url = override or resolve_database_url()

    return (
        url.replace("+asyncpg", "+psycopg2")
        .replace("sqlite+aiosqlite:", "sqlite:")
    )


def run_migrations_offline() -> None:
    """Emit SQL to stdout without connecting — ``alembic upgrade head --sql``."""
    context.configure(
        url=_sync_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Connect and run migrations in a transaction."""
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = _sync_url()

    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            # SQLite cannot ALTER most things; batch mode rebuilds the table
            # instead. Harmless on PostgreSQL, essential for the test path.
            render_as_batch=connection.dialect.name == "sqlite",
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
