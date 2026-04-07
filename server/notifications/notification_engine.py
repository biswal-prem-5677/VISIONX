"""
VisionX — Notification Engine
=================================
Central notification dispatcher — routes notifications
through configured channels (push, email, in-app, SMS).
"""

from __future__ import annotations

import time
from typing import Any, Optional

from loguru import logger
from pydantic import BaseModel, Field


class Notification(BaseModel):
    """A notification to send."""
    id: str = ""
    user_id: str
    title: str
    message: str
    channel: str = "in_app"  # in_app, email, push, sms
    priority: str = "normal"  # low, normal, high, urgent
    data: dict[str, Any] = Field(default_factory=dict)
    read: bool = False
    created_at: float = Field(default_factory=time.time)


class NotificationEngine:
    """
    Central notification dispatcher.

    Routes notifications through appropriate channels
    based on user preferences and priority.
    """

    def __init__(self):
        self._channels: dict[str, Any] = {}
        self._history: dict[str, list[Notification]] = {}  # user_id -> [notifs]
        self._preferences: dict[str, dict[str, bool]] = {}  # user_id -> channel prefs
        self._counter = 0

        logger.info("Notification Engine initialized")

    def register_channel(self, name: str, handler: Any) -> None:
        """Register a notification channel handler."""
        self._channels[name] = handler
        logger.info(f"Notification channel registered: {name}")

    async def send(self, notification: Notification) -> bool:
        """Send a notification through the specified channel."""
        self._counter += 1
        notification.id = f"notif_{self._counter}"

        # Store in history
        if notification.user_id not in self._history:
            self._history[notification.user_id] = []
        self._history[notification.user_id].append(notification)

        # Check user preference
        prefs = self._preferences.get(notification.user_id, {})
        if not prefs.get(notification.channel, True):
            logger.debug(f"Notification skipped (user pref): {notification.channel}")
            return True  # Silently skip

        # Dispatch to channel
        handler = self._channels.get(notification.channel)
        if handler:
            try:
                return await handler.send(notification)
            except Exception as e:
                logger.error(f"Notification send error: {e}")
                return False
        else:
            # Default: just log it
            logger.info(
                f"[NOTIF] {notification.user_id}: "
                f"{notification.title} — {notification.message}"
            )
            return True

    def get_unread(self, user_id: str) -> list[Notification]:
        """Get unread notifications for a user."""
        history = self._history.get(user_id, [])
        return [n for n in history if not n.read]

    def mark_read(self, user_id: str, notification_id: str) -> None:
        """Mark a notification as read."""
        for n in self._history.get(user_id, []):
            if n.id == notification_id:
                n.read = True
                break

    def mark_all_read(self, user_id: str) -> None:
        """Mark all notifications as read for a user."""
        for n in self._history.get(user_id, []):
            n.read = True

    def set_preferences(
        self, user_id: str, preferences: dict[str, bool]
    ) -> None:
        """Set notification channel preferences for a user."""
        self._preferences[user_id] = preferences

    def get_unread_count(self, user_id: str) -> int:
        """Get unread notification count."""
        return len(self.get_unread(user_id))
