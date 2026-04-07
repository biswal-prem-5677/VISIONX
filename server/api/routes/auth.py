"""
VisionX — Auth Routes
========================
Authentication endpoints: login, register, refresh, OAuth.
"""

from __future__ import annotations

from typing import Any, Optional

from loguru import logger
from pydantic import BaseModel, Field

try:
    from fastapi import APIRouter, HTTPException, Header
except ImportError:
    raise

from server.auth.jwt_handler import JWTHandler
from server.auth.rbac import RBACChecker, Permission

router = APIRouter()
jwt_handler = JWTHandler()


# ============================================
# Request / Response Models
# ============================================

class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str = ""


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


class UserResponse(BaseModel):
    user_id: str
    email: str
    name: str
    role: str


# ============================================
# In-memory user store (replaced by DB in production)
# ============================================

_users: dict[str, dict] = {
    "admin@visionx.ai": {
        "user_id": "admin-001",
        "email": "admin@visionx.ai",
        "password": "admin123",  # Hashed in production
        "name": "Admin",
        "role": "super_admin",
    },
}


# ============================================
# Endpoints
# ============================================

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """Authenticate and get JWT tokens."""
    user = _users.get(req.email)
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    tokens = jwt_handler.create_token_pair(
        user_id=user["user_id"],
        role=user["role"],
    )

    logger.info(f"User logged in: {req.email}")

    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )


@router.post("/register", response_model=UserResponse)
async def register(req: RegisterRequest):
    """Register a new user."""
    if req.email in _users:
        raise HTTPException(status_code=409, detail="Email already registered")

    import uuid

    user_id = str(uuid.uuid4())
    _users[req.email] = {
        "user_id": user_id,
        "email": req.email,
        "password": req.password,
        "name": req.name,
        "role": "user",
    }

    logger.info(f"User registered: {req.email}")

    return UserResponse(
        user_id=user_id,
        email=req.email,
        name=req.name,
        role="user",
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(authorization: str = Header("")):
    """Get current user info from JWT."""
    token = authorization.replace("Bearer ", "")
    payload = jwt_handler.verify_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Find user
    for user in _users.values():
        if user["user_id"] == payload.sub:
            return UserResponse(
                user_id=user["user_id"],
                email=user["email"],
                name=user["name"],
                role=user["role"],
            )

    raise HTTPException(status_code=404, detail="User not found")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(authorization: str = Header("")):
    """Refresh access token."""
    token = authorization.replace("Bearer ", "")
    payload = jwt_handler.verify_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    tokens = jwt_handler.create_token_pair(
        user_id=payload.sub,
        role=payload.role,
    )

    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )
