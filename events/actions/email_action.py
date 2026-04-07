"""
VisionX — Email Action
=========================
Send email notifications when events are triggered.
Uses Resend API for delivery.
"""

from __future__ import annotations

import os
from typing import Any

from loguru import logger

from events.event_engine import EventAction
from shared.models import Event


class EmailAction(EventAction):
    """Send email notification via Resend API."""

    action_type = "email"

    def __init__(
        self,
        to_email: str = "",
        from_email: str = "alerts@visionx.ai",
        api_key: str = "",
    ):
        self.to_email = to_email or os.getenv("ALERT_EMAIL", "")
        self.from_email = from_email
        self.api_key = api_key or os.getenv("RESEND_API_KEY", "")

    def execute(self, event: Event, context: dict[str, Any]) -> bool:
        """Send email alert."""
        if not self.to_email:
            logger.warning("Email action: no recipient configured")
            return False

        if not self.api_key:
            # Log instead of sending if no API key
            logger.info(
                f"[EMAIL] Would send to {self.to_email}: "
                f"[{event.severity}] {event.message}"
            )
            return True

        try:
            import requests

            response = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": self.from_email,
                    "to": [self.to_email],
                    "subject": f"[VisionX {event.severity.upper()}] {event.message}",
                    "html": self._build_html(event),
                },
                timeout=10,
            )

            if response.status_code == 200:
                logger.info(f"Email sent to {self.to_email}")
                return True
            else:
                logger.error(f"Email failed: {response.status_code} {response.text}")
                return False

        except Exception as e:
            logger.error(f"Email error: {e}")
            return False

    @staticmethod
    def _build_html(event: Event) -> str:
        """Build HTML email body."""
        metadata = event.metadata or {}
        conditions = metadata.get("matched_conditions", [])

        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #1a1a2e; color: white; padding: 20px; border-radius: 12px 12px 0 0;">
                <h2 style="margin: 0;">🧠 VisionX Alert</h2>
            </div>
            <div style="background: #16213e; color: #e0e0e0; padding: 20px;">
                <p><strong>Severity:</strong> {event.severity}</p>
                <p><strong>Message:</strong> {event.message}</p>
                <p><strong>Source:</strong> {event.source}</p>
                <p><strong>Time:</strong> {event.timestamp}</p>
                {"<p><strong>Conditions:</strong> " + ", ".join(conditions) + "</p>" if conditions else ""}
            </div>
            <div style="background: #0f3460; color: #aaa; padding: 12px; border-radius: 0 0 12px 12px; text-align: center;">
                <small>VisionX — Detect. Understand. Decide. Act.</small>
            </div>
        </div>
        """
