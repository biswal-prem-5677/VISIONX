"""
VisionX — API Call Action
========================================
Trigger external REST API calls when events fire.

Contract note
-------------
Previously ``async def execute(self, url, method, payload, ...)`` on a
non-``EventAction`` class. Two problems: the engine never awaited it (so it
never ran), and its signature did not match the ``(event, context)`` dispatch
contract, so it could not have been called correctly even if awaited. The
request is now configured in ``__init__`` like every other action.

Overlaps heavily with :class:`~events.actions.webhook_action.WebhookAction`;
kept for callers that need a non-POST method or a custom body template.
"""

from __future__ import annotations

from typing import Any, Optional

from loguru import logger

from events.event_engine import EventAction
from shared.models import Event
from shared.url_safety import UnsafeURLError, validate_outbound_url


class APICallAction(EventAction):
    """Event action that calls an external REST API."""

    action_type = "api_call"

    def __init__(
        self,
        url: str = "",
        method: str = "POST",
        headers: Optional[dict[str, str]] = None,
        timeout: float = 10.0,
        extra_payload: Optional[dict[str, Any]] = None,
    ):
        self.url = url
        self.method = method.upper()
        self.headers = headers or {"Content-Type": "application/json"}
        self.timeout = timeout
        self.extra_payload = extra_payload or {}

        logger.info(f"APICallAction initialized ({self.method} {url or '<unset>'})")

    def execute(self, event: Event, context: dict[str, Any]) -> bool:
        """Call the configured endpoint with the event as the body."""
        if not self.url:
            logger.warning("API call action: no URL configured")
            return False

        try:
            validate_outbound_url(self.url)
        except UnsafeURLError as e:
            logger.error(f"API call blocked by URL policy: {e}")
            return False

        try:
            import requests

            payload = {
                **self.extra_payload,
                "event_type": event.event_type,
                "source": event.source,
                "message": event.message,
                "severity": event.severity,
                "timestamp": event.timestamp.isoformat() if event.timestamp else None,
                "metadata": event.metadata,
            }

            response = requests.request(
                method=self.method,
                url=self.url,
                json=payload,
                headers=self.headers,
                timeout=self.timeout,
                allow_redirects=False,
            )

            if response.status_code < 300:
                logger.info(f"API call to {self.url}: {response.status_code}")
                return True

            logger.warning(f"API call failed: {response.status_code}")
            return False

        except Exception as e:
            logger.error(f"API call failed: {e}")
            return False
