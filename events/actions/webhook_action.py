"""
VisionX — Webhook Action
============================
Trigger external webhooks when events fire.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from events.event_engine import EventAction
from shared.models import Event


class WebhookAction(EventAction):
    """Send HTTP POST to an external webhook URL."""

    action_type = "webhook"

    def __init__(self, url: str = "", headers: dict[str, str] | None = None):
        self.url = url
        self.headers = headers or {"Content-Type": "application/json"}

    def execute(self, event: Event, context: dict[str, Any]) -> bool:
        """POST event data to webhook URL."""
        if not self.url:
            logger.warning("Webhook action: no URL configured")
            return False

        try:
            import requests

            payload = {
                "event_type": event.event_type,
                "source": event.source,
                "message": event.message,
                "severity": event.severity,
                "timestamp": event.timestamp.isoformat() if event.timestamp else None,
                "metadata": event.metadata,
            }

            response = requests.post(
                self.url,
                json=payload,
                headers=self.headers,
                timeout=10,
            )

            if response.status_code < 300:
                logger.info(f"Webhook sent to {self.url} ({response.status_code})")
                return True
            else:
                logger.warning(f"Webhook failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return False
