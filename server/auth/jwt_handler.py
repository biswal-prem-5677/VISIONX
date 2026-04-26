"""
VisionX — JWT Authentication Handler
========================================
JWT token creation, verification, and management.
Supports access tokens and refresh tokens.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from loguru import logger
from pydantic import BaseModel


class TokenPayload(BaseModel):
    """JWT token payload."""
    sub: str  # Subject (user_id)
    role: str = "user"
    exp: Optional[datetime] = None
    iat: Optional[datetime] = None
    jti: Optional[str] = None  # JWT ID for revocation


class TokenPair(BaseModel):
    """Access + Refresh token pair."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600  # seconds


class JWTHandler:
    """
    JWT token management.

    Creates and verifies JWT tokens for authentication.
    Supports access tokens (short-lived) and refresh tokens (long-lived).
    """

    def __init__(
        self,
        secret_key: str = "",
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 60,
        refresh_token_expire_days: int = 30,
    ):
        self.secret_key = secret_key or os.getenv(
            "JWT_SECRET_KEY", "visionx-dev-secret-change-in-production"
        )
        self.algorithm = algorithm
        self.access_expire = timedelta(minutes=access_token_expire_minutes)
        self.refresh_expire = timedelta(days=refresh_token_expire_days)
        self._revoked_tokens: set[str] = set()

        logger.info(
            f"JWT Handler initialized "
            f"(access: {access_token_expire_minutes}min, "
            f"refresh: {refresh_token_expire_days}d)"
        )

    def create_access_token(
        self,
        user_id: str,
        role: str = "user",
        extra_claims: dict[str, Any] | None = None,
    ) -> str:
        """Create a short-lived access token."""
        return self._create_token(
            subject=user_id,
            role=role,
            expires_delta=self.access_expire,
            extra_claims=extra_claims,
        )

    def create_refresh_token(self, user_id: str) -> str:
        """Create a long-lived refresh token."""
        return self._create_token(
            subject=user_id,
            expires_delta=self.refresh_expire,
            token_type="refresh",
        )

    def create_token_pair(
        self,
        user_id: str,
        role: str = "user",
    ) -> TokenPair:
        """Create both access and refresh tokens."""
        access = self.create_access_token(user_id, role)
        refresh = self.create_refresh_token(user_id)

        return TokenPair(
            access_token=access,
            refresh_token=refresh,
            expires_in=int(self.access_expire.total_seconds()),
        )

    def verify_token(self, token: str) -> Optional[TokenPayload]:
        """
        Verify and decode a JWT token.

        Returns:
            TokenPayload if valid, None if invalid/expired
        """
        try:
            import jwt

            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )

            # Check revocation
            jti = payload.get("jti")
            if jti and jti in self._revoked_tokens:
                logger.warning(f"Revoked token used: {jti}")
                return None

            return TokenPayload(
                sub=payload["sub"],
                role=payload.get("role", "user"),
                exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc) if "exp" in payload else None,
                iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc) if "iat" in payload else None,
                jti=jti,
            )

        except Exception as e:
            logger.debug(f"Token verification failed: {e}")
            return None

    def revoke_token(self, jti: str) -> None:
        """Revoke a token by its JTI."""
        self._revoked_tokens.add(jti)
        logger.info(f"Token revoked: {jti}")

    def _create_token(
        self,
        subject: str,
        expires_delta: timedelta,
        role: str = "user",
        token_type: str = "access",
        extra_claims: dict[str, Any] | None = None,
    ) -> str:
        """Create a JWT token."""
        import uuid

        try:
            import jwt
        except ImportError:
            logger.error("PyJWT not installed. Install with: pip install PyJWT")
            return ""

        now = datetime.now(timezone.utc)
        payload = {
            "sub": subject,
            "role": role,
            "type": token_type,
            "iat": now,
            "exp": now + expires_delta,
            "jti": str(uuid.uuid4()),
        }

        if extra_claims:
            payload.update(extra_claims)

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
