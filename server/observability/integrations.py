"""
VisionX — Observability Integration
========================================
Sentry error tracking + PostHog product analytics.
Initialized once at startup, used globally.
"""

from __future__ import annotations

import os
from typing import Any, Optional
from loguru import logger


class SentryIntegration:
    """Sentry error tracking and performance monitoring."""

    def __init__(self, dsn: str = ""):
        self.dsn = dsn or os.getenv("SENTRY_DSN", "")
        self._initialized = False

        if self.dsn:
            try:
                import sentry_sdk
                from sentry_sdk.integrations.fastapi import FastApiIntegration
                from sentry_sdk.integrations.logging import LoggingIntegration

                sentry_sdk.init(
                    dsn=self.dsn,
                    traces_sample_rate=0.2,
                    profiles_sample_rate=0.1,
                    environment=os.getenv("VISIONX_ENV", "development"),
                    release=os.getenv("VISIONX_VERSION", "0.1.0"),
                    integrations=[
                        FastApiIntegration(transaction_style="endpoint"),
                        LoggingIntegration(level=None, event_level="ERROR"),
                    ],
                    before_send=self._before_send,
                )
                self._initialized = True
                logger.info("Sentry initialized")
            except ImportError:
                logger.warning("sentry-sdk not installed — error tracking disabled")
        else:
            logger.info("Sentry DSN not configured — error tracking disabled")

    def capture_exception(self, error: Exception, context: Optional[dict] = None) -> None:
        """Capture an exception to Sentry."""
        if not self._initialized:
            return
        try:
            import sentry_sdk
            if context:
                sentry_sdk.set_context("visionx", context)
            sentry_sdk.capture_exception(error)
        except Exception:
            pass

    def capture_message(self, message: str, level: str = "info") -> None:
        """Capture a message to Sentry."""
        if not self._initialized:
            return
        try:
            import sentry_sdk
            sentry_sdk.capture_message(message, level=level)
        except Exception:
            pass

    def set_user(self, user_id: str, email: str = "", role: str = "") -> None:
        """Set the current user context for Sentry."""
        if not self._initialized:
            return
        try:
            import sentry_sdk
            sentry_sdk.set_user({"id": user_id, "email": email, "role": role})
        except Exception:
            pass

    @staticmethod
    def _before_send(event: dict, hint: dict) -> Optional[dict]:
        """Scrub PII before sending to Sentry."""
        # Remove sensitive fields
        if "request" in event and "headers" in event["request"]:
            headers = event["request"]["headers"]
            for sensitive in ("authorization", "cookie", "x-api-key"):
                if sensitive in headers:
                    headers[sensitive] = "[REDACTED]"
        return event


class PostHogIntegration:
    """PostHog product analytics — feature flags, funnels, session replay."""

    def __init__(self, api_key: str = "", host: str = ""):
        self.api_key = api_key or os.getenv("POSTHOG_API_KEY", "")
        self.host = host or os.getenv("POSTHOG_HOST", "https://app.posthog.com")
        self._initialized = False
        self._client: Any = None

        if self.api_key:
            try:
                from posthog import Posthog
                self._client = Posthog(
                    project_api_key=self.api_key,
                    host=self.host,
                )
                self._initialized = True
                logger.info("PostHog initialized")
            except ImportError:
                logger.warning("posthog not installed — analytics disabled")
        else:
            logger.info("PostHog API key not configured — analytics disabled")

    def capture(self, distinct_id: str, event: str, properties: Optional[dict] = None) -> None:
        """Track a user event."""
        if not self._initialized or not self._client:
            return
        try:
            self._client.capture(distinct_id, event, properties or {})
        except Exception as e:
            logger.debug(f"PostHog capture failed: {e}")

    def identify(self, distinct_id: str, properties: Optional[dict] = None) -> None:
        """Identify a user with properties."""
        if not self._initialized or not self._client:
            return
        try:
            self._client.identify(distinct_id, properties or {})
        except Exception as e:
            logger.debug(f"PostHog identify failed: {e}")

    def is_feature_enabled(self, distinct_id: str, flag: str) -> bool:
        """Check if a feature flag is enabled for a user."""
        if not self._initialized or not self._client:
            return False
        try:
            return bool(self._client.is_feature_enabled(flag, distinct_id))
        except Exception:
            return False

    def shutdown(self) -> None:
        """Flush and shutdown PostHog client."""
        if self._client:
            try:
                self._client.shutdown()
            except Exception:
                pass


# ─── Global Singletons ──────────────────────────────────────────────────

sentry = SentryIntegration()
posthog = PostHogIntegration()
