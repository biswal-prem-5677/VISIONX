"""
VisionX — Database Package
==============================
Schema, session management, and tenant-scoped access.

Importing this package registers every model on ``Base.metadata``. That import
side effect is load-bearing: ``Base.metadata`` is empty until the model module
is executed, so anything that reflects over the schema — ``create_all``,
Alembic autogenerate, the tenancy audit in ``tests/test_db.py`` — would
otherwise see zero tables and cheerfully report success.

Reading order:

- :mod:`server.db.base` — declarative base, portable column types
- :mod:`server.db.models` — the nine V1 tables
- :mod:`server.db.session` — engine, session factory, FastAPI dependency
- :mod:`server.db.tenancy` — Row-Level Security plumbing
- :mod:`server.db.repositories` — the only sanctioned query surface
"""

from server.db.base import Base, tenant_tables
from server.db.models import (  # noqa: F401 - registers tables on Base.metadata
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
    "tenant_tables",
]
