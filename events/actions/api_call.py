"""
VisionX — API Call Action
========================================
Trigger external REST API calls when events fire.
"""

from __future__ import annotations

from typing import Any, Optional
from loguru import logger


class APICallAction:
    """Event action that calls an external REST API."""

    def __init__(self):
        logger.info("APICallAction initialized")

    async def execute(
        self,
        url: str,
        method: str = "POST",
        payload: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        timeout: float = 10.0,
    ) -> dict:
        """Execute an API call."""
        try:
            import httpx

            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(
                    method=method.upper(),
                    url=url,
                    json=payload,
                    headers=headers or {"Content-Type": "application/json"},
                )
                logger.info(f"API call to {url}: {response.status_code}")
                return {
                    "status": "sent",
                    "status_code": response.status_code,
                    "url": url,
                }

        except Exception as e:
            logger.error(f"API call failed: {e}")
            return {"status": "failed", "error": str(e), "url": url}
