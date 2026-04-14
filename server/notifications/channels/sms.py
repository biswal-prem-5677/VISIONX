"""
VisionX — SMS Notification Channel
========================================
SMS delivery via Twilio API.
"""

from __future__ import annotations

import os
from typing import Optional
from loguru import logger


class SMSChannel:
    """SMS notification channel using Twilio API."""

    def __init__(
        self,
        account_sid: str = "",
        auth_token: str = "",
        from_number: str = "",
    ):
        self.account_sid = account_sid or os.getenv("TWILIO_ACCOUNT_SID", "")
        self.auth_token = auth_token or os.getenv("TWILIO_AUTH_TOKEN", "")
        self.from_number = from_number or os.getenv("TWILIO_FROM_NUMBER", "")
        logger.info("SMSChannel initialized")

    async def send(self, to_number: str, message: str) -> bool:
        """Send an SMS notification."""
        if not all([self.account_sid, self.auth_token, self.from_number]):
            logger.warning("Twilio credentials not configured — SMS not sent")
            return False

        try:
            # In production: use twilio.rest.Client
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json",
                    auth=(self.account_sid, self.auth_token),
                    data={
                        "From": self.from_number,
                        "To": to_number,
                        "Body": message,
                    },
                )
                if response.status_code in (200, 201):
                    logger.info(f"SMS sent to {to_number}")
                    return True
                else:
                    logger.error(f"SMS send failed: {response.status_code}")
                    return False

        except Exception as e:
            logger.error(f"SMS send error: {e}")
            return False
