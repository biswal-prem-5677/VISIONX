"""
VisionX — Email Notification Channel
========================================
Email delivery via Resend API.
"""

from __future__ import annotations

import os
from typing import Optional
from loguru import logger


class EmailChannel:
    """Email notification channel using Resend API."""

    def __init__(self, api_key: str = "", from_email: str = ""):
        self.api_key = api_key or os.getenv("RESEND_API_KEY", "")
        self.from_email = from_email or os.getenv("RESEND_FROM_EMAIL", "noreply@visionx.ai")
        logger.info(f"EmailChannel initialized (from: {self.from_email})")

    async def send(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> bool:
        """Send an email notification."""
        if not self.api_key:
            logger.warning("Resend API key not configured — email not sent")
            return False

        try:
            # In production: use resend.Emails.send()
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.resend.com/emails",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "from": self.from_email,
                        "to": [to_email],
                        "subject": subject,
                        "html": html_body,
                        "text": text_body or "",
                    },
                )
                if response.status_code == 200:
                    logger.info(f"Email sent to {to_email}: {subject}")
                    return True
                else:
                    logger.error(f"Email send failed: {response.status_code}")
                    return False

        except Exception as e:
            logger.error(f"Email send error: {e}")
            return False
