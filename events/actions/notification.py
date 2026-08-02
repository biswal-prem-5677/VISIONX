"""
VisionX — Notification Action
========================================
Trigger push/in-app notifications from event engine.

Contract note
-------------
Previously ``async def execute(self, user_id, title, message, ...)`` on a
non-``EventAction`` class: never awaited by the engine, and the wrong signature
for dispatch. Recipient and channels are now configured in ``__init__``.

Delivery note
-------------
Only the ``in_app`` channel is implemented (an in-memory inbox). ``push``,
``email``, and ``sms`` have no transport wired, so requesting them fails rather
than logging "sent" — this action previously reported every channel as
``"sent"`` unconditionally, including ones that do not exist.
"""

from __future__ import annotations

from collections import deque
from typing import Any

from loguru import logger

from events.event_engine import EventAction
from shared.models import Event

#: Channels this action can actually deliver on today.
IMPLEMENTED_CHANNELS = frozenset({"in_app"})


class NotificationAction(EventAction):
    """Event action that sends notifications via configured channels."""

    action_type = "notification"

    def __init__(
        self,
        user_id: str = "",
        channels: list[str] | None = None,
        max_inbox: int = 500,
    ):
        self.user_id = user_id
        self.channels = list(channels or ["in_app"])
        # Bounded, per EXECUTION_RULES R8.
        self._inbox: deque[dict[str, Any]] = deque(maxlen=max_inbox)

        unsupported = set(self.channels) - IMPLEMENTED_CHANNELS
        if unsupported:
            logger.warning(
                f"NotificationAction configured with unimplemented channels: "
                f"{sorted(unsupported)}. Those deliveries will fail."
            )

        logger.info(f"NotificationAction initialized (channels={self.channels})")

    def execute(self, event: Event, context: dict[str, Any]) -> bool:
        """
        Deliver the event to every configured channel.

        Returns True only if **all** configured channels delivered. A partial
        delivery is a failure so the engine retries and, if it keeps failing,
        dead-letters it.
        """
        recipient = self.user_id or str(context.get("user_id") or "")
        if not recipient:
            logger.error("Notification NOT sent — no recipient configured")
            return False

        all_ok = True

        for channel in self.channels:
            if channel not in IMPLEMENTED_CHANNELS:
                logger.error(
                    f"Notification channel '{channel}' is not implemented — "
                    f"'{event.message}' was NOT delivered to {recipient}"
                )
                all_ok = False
                continue

            try:
                self._inbox.append({
                    "user_id": recipient,
                    "event_id": str(event.id),
                    "severity": event.severity,
                    "title": event.event_type,
                    "message": event.message,
                    "timestamp": event.timestamp.isoformat() if event.timestamp else None,
                })
                logger.info(f"Notification [in_app] to {recipient}: {event.message}")
            except Exception as e:
                logger.error(f"Notification [{channel}] failed: {e}")
                all_ok = False

        return all_ok

    def get_inbox(self, limit: int = 50) -> list[dict[str, Any]]:
        """Read recent in-app notifications, newest last."""
        return list(self._inbox)[-limit:]
