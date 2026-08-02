"""
VisionX — Webhook Action
============================
Trigger external webhooks when events fire.

The destination URL comes from user configuration, so it is validated against
the SSRF policy in :mod:`shared.url_safety` before every request.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from events.event_engine import EventAction
from shared.models import Event
from shared.url_safety import UnsafeURLError, validate_outbound_url


class WebhookAction(EventAction):
    """Send HTTP POST to an external webhook URL."""

    action_type = "webhook"

    def __init__(
        self,
        url: str = "",
        headers: dict[str, str] | None = None,
        timeout: float = 10.0,
    ):
        self.url = url
        self.headers = headers or {"Content-Type": "application/json"}
        self.timeout = timeout

    def execute(self, event: Event, context: dict[str, Any]) -> bool:
        """POST event data to webhook URL."""
        if not self.url:
            logger.warning("Webhook action: no URL configured")
            return False

        try:
            validate_outbound_url(self.url)
        except UnsafeURLError as e:
            logger.error(f"Webhook blocked by URL policy: {e}")
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
                timeout=self.timeout,
                # A webhook that 302s to an internal address would bypass the
                # pre-flight check entirely.
                allow_redirects=False,
            )

            if response.status_code < 300:
                logger.info(f"Webhook sent to {self.url} ({response.status_code})")
                return True

            logger.warning(f"Webhook failed: {response.status_code}")
            return False

        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return False
