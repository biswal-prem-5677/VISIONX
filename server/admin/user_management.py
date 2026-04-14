"""
VisionX — User Management Service
========================================
Admin-level user CRUD, ban, and role management.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, EmailStr
from loguru import logger


class UserProfile(BaseModel):
    user_id: str
    email: str
    display_name: str = ""
    role: str = "user"
    plan_tier: str = "free"
    is_active: bool = True
    is_banned: bool = False
    ban_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None


class UserManagement:
    """Admin-level user management service."""

    def __init__(self):
        self._users: dict[str, UserProfile] = {}
        logger.info("UserManagement service initialized")

    async def list_users(
        self,
        page: int = 1,
        per_page: int = 50,
        role_filter: Optional[str] = None,
    ) -> dict:
        """List all users with pagination and filtering."""
        users = list(self._users.values())
        if role_filter:
            users = [u for u in users if u.role == role_filter]
        start = (page - 1) * per_page
        return {
            "users": users[start : start + per_page],
            "total": len(users),
            "page": page,
            "per_page": per_page,
        }

    async def get_user(self, user_id: str) -> Optional[UserProfile]:
        """Get a specific user by ID."""
        return self._users.get(user_id)

    async def update_role(self, user_id: str, new_role: str) -> bool:
        """Update a user's role (user, moderator, admin)."""
        if user_id in self._users:
            self._users[user_id].role = new_role
            logger.info(f"User {user_id} role updated to {new_role}")
            return True
        return False

    async def ban_user(self, user_id: str, reason: str) -> bool:
        """Ban a user with reason."""
        if user_id in self._users:
            self._users[user_id].is_banned = True
            self._users[user_id].ban_reason = reason
            self._users[user_id].is_active = False
            logger.warning(f"User {user_id} banned: {reason}")
            return True
        return False

    async def unban_user(self, user_id: str) -> bool:
        """Unban a user."""
        if user_id in self._users:
            self._users[user_id].is_banned = False
            self._users[user_id].ban_reason = None
            self._users[user_id].is_active = True
            logger.info(f"User {user_id} unbanned")
            return True
        return False

    async def deactivate_user(self, user_id: str) -> bool:
        """Soft-delete / deactivate a user."""
        if user_id in self._users:
            self._users[user_id].is_active = False
            logger.info(f"User {user_id} deactivated")
            return True
        return False
