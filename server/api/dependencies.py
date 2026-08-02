"""
VisionX — Shared API Dependencies
=====================================
FastAPI dependency-injection helpers for authentication and authorization.

Why this module exists
----------------------
Route handlers previously each did ``authorization.replace("Bearer ", "")`` by
hand and re-implemented token verification. That pattern guarantees that some
route will eventually forget the check — and it made the fully-implemented
RBAC module (``server/auth/rbac.py``) dead code, since no handler ever called it.

Every protected endpoint should now depend on :func:`get_current_user`, and
every permission-gated endpoint on :func:`require_permission`.
"""

from __future__ import annotations

from typing import Optional

from loguru import logger
from pydantic import BaseModel

try:
    from fastapi import Depends, Header, HTTPException, status
except ImportError:  # pragma: no cover
    raise

from server.auth.jwt_handler import JWTHandler
from server.auth.rbac import Permission, RBACChecker

# Single shared handler so revocation state is consistent across routes.
jwt_handler = JWTHandler()


class CurrentUser(BaseModel):
    """Authenticated principal resolved from a bearer token."""

    user_id: str
    role: str

    def has(self, permission: Permission) -> bool:
        return RBACChecker.has_permission(self.role, permission)


def _extract_bearer(authorization: str) -> Optional[str]:
    """Parse an ``Authorization: Bearer <token>`` header. Case-insensitive scheme."""
    if not authorization:
        return None
    parts = authorization.split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1].strip()
    return token or None


async def get_current_user(
    authorization: str = Header("", alias="Authorization"),
) -> CurrentUser:
    """
    Resolve and validate the caller's access token.

    Raises 401 if the header is missing, malformed, expired, revoked, or is a
    refresh token being used as an access token.
    """
    token = _extract_bearer(authorization)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = jwt_handler.verify_token(token, expected_type="access")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return CurrentUser(user_id=payload.sub, role=payload.role)


async def get_optional_user(
    authorization: str = Header("", alias="Authorization"),
) -> Optional[CurrentUser]:
    """Resolve the caller if a valid token is present, else None. Never raises."""
    try:
        return await get_current_user(authorization)
    except HTTPException:
        return None


def require_permission(permission: Permission):
    """
    Build a dependency enforcing a single RBAC permission.

    Usage::

        @router.get("/devices", dependencies=[Depends(require_permission(Permission.MANAGE_DEVICES))])
        async def list_devices(): ...

    Or, when the handler needs the principal::

        async def list_devices(user: CurrentUser = Depends(require_permission(Permission.MANAGE_DEVICES))):
            ...
    """

    async def _dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not RBACChecker.has_permission(user.role, permission):
            logger.warning(
                f"Permission denied: user={user.user_id} role={user.role} "
                f"needs={permission.value}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires permission: {permission.value}",
            )
        return user

    return _dependency
