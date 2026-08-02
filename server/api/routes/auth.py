"""
VisionX — Auth Routes
========================
Authentication endpoints: login, register, refresh, current user.

Security notes
--------------
Credentials are stored as bcrypt (or stdlib scrypt) hashes via
``server.auth.password``. This module previously compared passwords in
plaintext against a hardcoded ``admin123`` super-admin.

The user store below is still **in-memory** and therefore resets on restart.
That is a known, tracked gap (ENGINEERING_REVIEW.md §4): it must be replaced by
a Postgres ``users`` table before any real deployment. The hashing and lookup
boundaries are deliberately isolated here so that swap stays small.
"""

from __future__ import annotations

import os
import re
import uuid

from loguru import logger
from pydantic import BaseModel, Field, field_validator

try:
    from fastapi import APIRouter, Depends, HTTPException, status
except ImportError:
    raise

from server.api.dependencies import CurrentUser, get_current_user, jwt_handler
from server.auth.password import generate_password, hash_password, verify_password

router = APIRouter()

# Pragmatic email shape check. Deliberately not RFC 5322 — full validation
# requires the `email-validator` package, which is not in requirements-ci.txt.
# Deliverability is proven by a confirmation email, never by a regex.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")


def _normalize_email(value: str) -> str:
    value = value.strip().lower()
    if not _EMAIL_RE.match(value):
        raise ValueError("Invalid email address")
    return value


# ============================================
# Request / Response Models
# ============================================

class LoginRequest(BaseModel):
    email: str = Field(max_length=320)
    password: str = Field(min_length=1, max_length=512)

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        return _normalize_email(v)


class RegisterRequest(BaseModel):
    email: str = Field(max_length=320)
    password: str = Field(min_length=8, max_length=512)
    name: str = Field(default="", max_length=200)

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        return _normalize_email(v)


class RefreshRequest(BaseModel):
    refresh_token: str


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
# In-memory user store
# TODO(platform): replace with the Postgres `users` table (Phase 1).
# ============================================

_users: dict[str, dict] = {}

#: Constant-work comparison target so login timing does not reveal whether an
#: email is registered. Computed once at import.
_DUMMY_HASH = hash_password("visionx-timing-equalizer")


def _seed_bootstrap_admin() -> None:
    """
    Create the initial admin account from the environment.

    Never ships a hardcoded password. If BOOTSTRAP_ADMIN_PASSWORD is unset we
    generate a random one and log it once, so a fresh dev environment stays
    usable without weakening production.
    """
    email = _normalize_email(os.getenv("BOOTSTRAP_ADMIN_EMAIL", "admin@visionx.ai"))
    password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "")

    if not password:
        password = generate_password()
        logger.warning(
            f"BOOTSTRAP_ADMIN_PASSWORD not set. Generated one-time admin credentials — "
            f"email={email} password={password}"
        )

    _users[email] = {
        "user_id": "admin-001",
        "email": email,
        "password_hash": hash_password(password),
        "name": "Admin",
        "role": "super_admin",
    }


_seed_bootstrap_admin()


# ============================================
# Endpoints
# ============================================

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """Authenticate and receive an access/refresh token pair."""
    user = _users.get(req.email)

    # Always run a verification so an unknown email costs the same as a known one.
    stored_hash = user["password_hash"] if user else _DUMMY_HASH
    password_ok = verify_password(req.password, stored_hash)

    if user is None or not password_ok:
        logger.info(f"Failed login attempt: {req.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    tokens = jwt_handler.create_token_pair(user_id=user["user_id"], role=user["role"])
    logger.info(f"User logged in: {req.email}")

    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(req: RegisterRequest):
    """Register a new standard user."""
    if req.email in _users:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user_id = str(uuid.uuid4())
    _users[req.email] = {
        "user_id": user_id,
        "email": req.email,
        "password_hash": hash_password(req.password),
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
async def get_me(user: CurrentUser = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    for record in _users.values():
        if record["user_id"] == user.user_id:
            return UserResponse(
                user_id=record["user_id"],
                email=record["email"],
                name=record["name"],
                role=record["role"],
            )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found",
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(req: RefreshRequest):
    """
    Exchange a refresh token for a new token pair.

    The token is taken from the request body rather than the Authorization
    header: this endpoint requires a *refresh* token, and accepting it in the
    same header slot as access tokens is what previously allowed the two to be
    used interchangeably.
    """
    payload = jwt_handler.verify_token(req.refresh_token, expected_type="refresh")

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    tokens = jwt_handler.create_token_pair(user_id=payload.sub, role=payload.role)

    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )
