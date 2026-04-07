"""
VisionX — OAuth2 Integration
================================
OAuth2 provider management for Google, GitHub, etc.
"""

from __future__ import annotations

import os
from typing import Any, Optional

from loguru import logger
from pydantic import BaseModel


class OAuthProvider(BaseModel):
    """Configuration for an OAuth2 provider."""
    name: str
    client_id: str
    client_secret: str
    authorize_url: str
    token_url: str
    userinfo_url: str
    scopes: list[str] = []


class OAuthUser(BaseModel):
    """User info from OAuth provider."""
    provider: str
    provider_id: str
    email: str
    name: str = ""
    avatar_url: str = ""


# Pre-configured providers
PROVIDERS: dict[str, OAuthProvider] = {
    "google": OAuthProvider(
        name="google",
        client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
        authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        userinfo_url="https://www.googleapis.com/oauth2/v2/userinfo",
        scopes=["openid", "email", "profile"],
    ),
    "github": OAuthProvider(
        name="github",
        client_id=os.getenv("GITHUB_CLIENT_ID", ""),
        client_secret=os.getenv("GITHUB_CLIENT_SECRET", ""),
        authorize_url="https://github.com/login/oauth/authorize",
        token_url="https://github.com/login/oauth/access_token",
        userinfo_url="https://api.github.com/user",
        scopes=["read:user", "user:email"],
    ),
}


class OAuthManager:
    """
    OAuth2 authentication manager.

    Handles authorization URL generation and token exchange
    for configured OAuth providers.
    """

    def __init__(self):
        self._providers = dict(PROVIDERS)
        logger.info(
            f"OAuth Manager initialized "
            f"(providers: {list(self._providers.keys())})"
        )

    def get_authorize_url(
        self,
        provider_name: str,
        redirect_uri: str,
        state: str = "",
    ) -> Optional[str]:
        """Generate OAuth authorization URL."""
        provider = self._providers.get(provider_name)
        if not provider or not provider.client_id:
            logger.warning(f"OAuth provider not configured: {provider_name}")
            return None

        params = {
            "client_id": provider.client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(provider.scopes),
            "response_type": "code",
            "state": state,
        }

        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{provider.authorize_url}?{query}"

    async def exchange_code(
        self,
        provider_name: str,
        code: str,
        redirect_uri: str,
    ) -> Optional[OAuthUser]:
        """
        Exchange authorization code for user info.

        Args:
            provider_name: OAuth provider name
            code: Authorization code
            redirect_uri: Redirect URI used in auth

        Returns:
            OAuthUser if successful, None otherwise
        """
        provider = self._providers.get(provider_name)
        if not provider:
            return None

        try:
            import httpx

            # Exchange code for token
            async with httpx.AsyncClient() as client:
                token_response = await client.post(
                    provider.token_url,
                    data={
                        "client_id": provider.client_id,
                        "client_secret": provider.client_secret,
                        "code": code,
                        "redirect_uri": redirect_uri,
                        "grant_type": "authorization_code",
                    },
                    headers={"Accept": "application/json"},
                )

                token_data = token_response.json()
                access_token = token_data.get("access_token")

                if not access_token:
                    logger.error(f"OAuth token exchange failed: {token_data}")
                    return None

                # Get user info
                user_response = await client.get(
                    provider.userinfo_url,
                    headers={"Authorization": f"Bearer {access_token}"},
                )

                user_data = user_response.json()

                return self._parse_user(provider_name, user_data)

        except Exception as e:
            logger.error(f"OAuth exchange error ({provider_name}): {e}")
            return None

    @staticmethod
    def _parse_user(provider: str, data: dict) -> OAuthUser:
        """Parse provider-specific user data into OAuthUser."""
        if provider == "google":
            return OAuthUser(
                provider=provider,
                provider_id=str(data.get("id", "")),
                email=data.get("email", ""),
                name=data.get("name", ""),
                avatar_url=data.get("picture", ""),
            )
        elif provider == "github":
            return OAuthUser(
                provider=provider,
                provider_id=str(data.get("id", "")),
                email=data.get("email", ""),
                name=data.get("login", ""),
                avatar_url=data.get("avatar_url", ""),
            )
        else:
            return OAuthUser(
                provider=provider,
                provider_id=str(data.get("id", "")),
                email=data.get("email", ""),
            )
