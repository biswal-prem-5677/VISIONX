"""
VisionX — Admin Routes
=========================
Admin god-mode API endpoints.
"""

from __future__ import annotations

try:
    from fastapi import APIRouter, HTTPException, Header
except ImportError:
    raise

from server.auth.jwt_handler import JWTHandler
from server.auth.rbac import RBACChecker, Permission

router = APIRouter()
jwt_handler = JWTHandler()


def _require_admin(authorization: str) -> dict:
    """Verify admin access."""
    token = authorization.replace("Bearer ", "")
    payload = jwt_handler.verify_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    if not RBACChecker.has_permission(payload.role, Permission.ADMIN_DASHBOARD):
        raise HTTPException(status_code=403, detail="Admin access required")

    return {"user_id": payload.sub, "role": payload.role}


@router.get("/health")
async def admin_health(authorization: str = Header("")):
    """Get system health (admin only)."""
    _require_admin(authorization)

    return {
        "status": "healthy",
        "services": {
            "api": "up",
            "database": "up",
            "redis": "up",
        },
    }


@router.get("/users")
async def admin_list_users(authorization: str = Header("")):
    """List all users (admin only)."""
    _require_admin(authorization)

    return {
        "users": [],
        "total": 0,
    }


@router.get("/stats")
async def admin_stats(authorization: str = Header("")):
    """Get system-wide statistics (admin only)."""
    _require_admin(authorization)

    return {
        "total_users": 0,
        "active_devices": 0,
        "total_events": 0,
        "total_rules": 0,
        "api_requests_today": 0,
    }
