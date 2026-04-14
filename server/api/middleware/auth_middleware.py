"""
VisionX — Auth Middleware
========================================
FastAPI dependency for JWT authentication on protected routes.
"""

from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from server.auth.jwt_handler import JWTHandler, TokenPayload

security = HTTPBearer(auto_error=False)
jwt_handler = JWTHandler()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> TokenPayload:
    """
    Extract and verify JWT from Authorization header.
    Raises 401 if missing or invalid.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = jwt_handler.verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def require_admin(
    user: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    """Require admin role."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


async def require_role(required_role: str):
    """Factory for role-based access control."""
    async def _check(user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
        if user.role != required_role and user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required",
            )
        return user
    return _check
""", "Description": "JWT auth middleware for protecting FastAPI routes", "IsArtifact": false, "Overwrite": false, "TargetFile": "c:\\เอกสาร\\VISIONX\\server\\api\\middleware\\auth_middleware.py"}
