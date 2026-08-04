"""
VisionX — Admin Routes
=========================
Admin god-mode API endpoints.

Authorization
-------------
Every route here requires ``Permission.ADMIN_DASHBOARD``, enforced through the
shared :func:`server.api.dependencies.require_permission` dependency.

This module previously built its *own* ``JWTHandler()`` instance and parsed the
Authorization header by hand with ``authorization.replace("Bearer ", "")``. Two
real bugs followed from that:

1. It called ``verify_token()`` without ``expected_type``, so a 30-day **refresh**
   token was accepted as an admin access token.
2. Revocation state lives on the handler instance. A token revoked through the
   shared handler stayed valid here, because this module held a different one.
"""

from __future__ import annotations

try:
    from fastapi import APIRouter, Depends
except ImportError:
    raise

from server.api.dependencies import CurrentUser, require_permission
from server.auth.rbac import Permission
from server.db.session import database

router = APIRouter(
    dependencies=[Depends(require_permission(Permission.ADMIN_DASHBOARD))],
)


@router.get("/health")
async def admin_health():
    """
    Get system health (admin only).

    Reports only what this process can verify. Both entries were once hardcoded
    to ``"up"`` — a health check that lies is worse than no health check.

    ``database`` is now a real ``SELECT 1`` against the configured engine.
    ``redis`` stays ``not_configured`` because nothing in the application
    connects to it yet, so any other value would be invented (tracker DEF-024).
    """
    database_up = await database.ping()

    return {
        "status": "healthy" if database_up else "degraded",
        "services": {
            "api": "up",
            "database": "up" if database_up else "down",
            "redis": "not_configured",
        },
    }


@router.get("/users")
async def admin_list_users():
    """List all users (admin only)."""
    return {
        "users": [],
        "total": 0,
    }


@router.get("/stats")
async def admin_stats(
    user: CurrentUser = Depends(require_permission(Permission.ADMIN_DASHBOARD)),
):
    """Get system-wide statistics (admin only)."""
    return {
        "requested_by": user.user_id,
        "total_users": 0,
        "active_devices": 0,
        "total_events": 0,
        "total_rules": 0,
        "api_requests_today": 0,
    }
