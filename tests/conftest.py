"""
VisionX — Shared Test Fixtures
==================================
Database fixtures for the suite.

Why a temporary file and not ``:memory:``
-----------------------------------------
Alembic runs its migrations over a *synchronous* connection, while the
application uses an async one. Two connections cannot share a SQLite in-memory
database — each would get its own empty one — so ``TestMigrationParity`` would
migrate one database and then inspect a different, empty one and report that
the schemas match. A file on disk is visible to both.

Each fixture gets its own file under ``tmp_path`` and therefore its own
database. Tests never share state, so they can be reordered or run in parallel
without a cleanup step that someone will eventually forget to write.

``DATABASE_URL`` is also pointed at the temporary file for the duration of a
test, because :data:`server.db.session.database` is a process-wide instance
constructed at import time — leaving it unset would let a stray call write to
``./visionx-dev.db`` in the developer's checkout.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import AsyncIterator, Iterator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

# ---------------------------------------------------------------------------
# This runs before anything else in the suite, and it has to.
#
# ``server.db.session`` builds a process-wide ``Database`` at *import* time, so
# whichever test module imports it first fixes the URL for the whole run. With
# DATABASE_URL unset that is the development fallback — and the application
# lifespan then opens ``./visionx-dev.db`` in the developer's checkout, sharing
# one file between the test run and whatever they are doing in another window.
#
# Setting it in a test module is too late: conftest is imported before any of
# them, and only here is the ordering guaranteed. Assigned before the imports
# below for the same reason.
# ---------------------------------------------------------------------------
os.environ.setdefault(
    "DATABASE_URL",
    f"sqlite+aiosqlite:///{Path(tempfile.mkdtemp(prefix='visionx-suite-')) / 'suite.db'}",
)

from server.db.session import Database  # noqa: E402 - must follow the line above


@pytest.fixture
def sqlite_path(tmp_path) -> Iterator[str]:
    """A filesystem path for one test's database. The file need not exist yet."""
    yield str(tmp_path / "visionx-test.db")


@pytest.fixture
def sqlite_url(sqlite_path: str) -> Iterator[str]:
    """
    An async SQLite URL for one test, exported as ``DATABASE_URL``.

    The environment variable is restored afterwards so a test that resolves the
    URL from the environment cannot influence the next one.
    """
    url = f"sqlite+aiosqlite:///{sqlite_path}"
    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = url
    try:
        yield url
    finally:
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous


@pytest_asyncio.fixture
async def db(sqlite_url: str) -> AsyncIterator[Database]:
    """
    A connected :class:`Database` with the schema created from the models.

    Uses ``create_all`` rather than Alembic because it is roughly an order of
    magnitude faster per test. That the two agree is not assumed — it is the
    single thing ``TestMigrationParity`` exists to prove.
    """
    database = Database(sqlite_url)
    await database.connect()
    await database.create_all()
    try:
        yield database
    finally:
        await database.disconnect()


@pytest_asyncio.fixture
async def session(db: Database) -> AsyncIterator[AsyncSession]:
    """
    A transactional session against the per-test database.

    Ends in a rollback rather than a commit — deliberately, and not merely
    because the database file is thrown away afterwards. Several tests assert
    that a constraint fires by provoking an ``IntegrityError``, which leaves the
    transaction aborted; a fixture that committed on the way out would turn
    every one of those passing tests into a teardown error and obscure the
    result they were written to show.

    ``Database.session()``'s own commit-and-rollback behaviour is therefore not
    exercised here. It is covered directly by
    ``tests/test_db.py::TestSessionLifecycle``.
    """
    factory = async_sessionmaker(db.engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        try:
            yield s
        finally:
            await s.rollback()


@pytest.fixture(autouse=True)
def _clear_production_env() -> Iterator[None]:
    """
    Guarantee tests run as "development" unless one opts in.

    :func:`server.db.session.resolve_database_url` refuses SQLite when
    ``VISIONX_ENV`` says production. A developer with that exported in their
    shell would otherwise see every database test fail with an unrelated error.
    """
    saved = {k: os.environ.get(k) for k in ("VISIONX_ENV", "APP_ENV")}
    for key in saved:
        os.environ.pop(key, None)
    try:
        yield
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
