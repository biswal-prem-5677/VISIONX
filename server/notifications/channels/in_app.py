"""
VisionX — In-App Notification Channel
========================================
In-app notifications stored in DB, surfaced via bell icon.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4
from pydantic import BaseModel
from loguru import logger


class InAppNotification(BaseModel):
    id: str
    user_id: str
    type: str = "info"  # info, success, warning, danger
    title: str
    message: str
    action_url: Optional[str] = None
    read: bool = False
    created_at: datetime


class InAppChannel:
    """In-app notification channel — stored in memory/DB, served via REST API."""

    def __init__(self):
        self._notifications: dict[str, list[InAppNotification]] = {}
        logger.info("InAppChannel initialized")

    async def send(
        self,
        user_id: str,
        title: str,
        message: str,
        type: str = "info",
        action_url: Optional[str] = None,
    ) -> InAppNotification:
        """Create an in-app notification for a user."""
        notification = InAppNotification(
            id=str(uuid4()),
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            action_url=action_url,
            created_at=datetime.now(timezone.utc),
        )

        if user_id not in self._notifications:
            self._notifications[user_id] = []
        self._notifications[user_id].append(notification)

        logger.debug(f"In-app notification created for {user_id}: {title}")
        return notification

    async def get_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50,
    ) -> list[InAppNotification]:
        """Get notifications for a user."""
        notifications = self._notifications.get(user_id, [])
        if unread_only:
            notifications = [n for n in notifications if not n.read]
        return sorted(notifications, key=lambda n: n.created_at, reverse=True)[:limit]

    async def mark_read(self, user_id: str, notification_id: str) -> bool:
        """Mark a notification as read."""
        for n in self._notifications.get(user_id, []):
            if n.id == notification_id:
                n.read = True
                return True
        return False

    async def get_unread_count(self, user_id: str) -> int:
        """Get unread notification count for badge display."""
        return sum(1 for n in self._notifications.get(user_id, []) if not n.read)
