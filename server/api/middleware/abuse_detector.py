"""
VisionX — Abuse Detection Middleware
========================================
Detects and blocks suspicious API usage patterns.
"""

from __future__ import annotations

import time
from collections import defaultdict

from loguru import logger


class AbuseDetector:
    """
    Anti-abuse detection system.

    Monitors API usage for suspicious patterns:
    - Rapid-fire requests (brute force)
    - Unusual endpoint access patterns
    - Repeated authentication failures
    """

    def __init__(
        self,
        max_auth_failures: int = 5,
        auth_lockout_minutes: int = 15,
        suspicious_threshold: int = 100,
    ):
        self._max_auth_failures = max_auth_failures
        self._lockout_duration = auth_lockout_minutes * 60
        self._suspicious_threshold = suspicious_threshold

        self._auth_failures: dict[str, list[float]] = defaultdict(list)
        self._blocked_keys: dict[str, float] = {}  # key -> blocked_until
        self._request_patterns: dict[str, dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )

        logger.info(
            f"Abuse Detector initialized "
            f"(max_failures: {max_auth_failures}, "
            f"lockout: {auth_lockout_minutes}min)"
        )

    def is_blocked(self, key: str) -> bool:
        """Check if a key is currently blocked."""
        blocked_until = self._blocked_keys.get(key, 0)
        if time.time() < blocked_until:
            return True

        # Clean expired block
        if key in self._blocked_keys:
            del self._blocked_keys[key]

        return False

    def record_auth_failure(self, key: str) -> bool:
        """
        Record an authentication failure.

        Returns:
            True if the key is now blocked
        """
        now = time.time()
        window_start = now - 300  # 5-minute window

        self._auth_failures[key].append(now)
        self._auth_failures[key] = [
            ts for ts in self._auth_failures[key] if ts > window_start
        ]

        if len(self._auth_failures[key]) >= self._max_auth_failures:
            self._blocked_keys[key] = now + self._lockout_duration
            logger.warning(
                f"ABUSE: Key blocked for auth failures: {key} "
                f"({len(self._auth_failures[key])} failures)"
            )
            return True

        return False

    def record_request(self, key: str, endpoint: str) -> bool:
        """
        Record a request and check for suspicious patterns.

        Returns:
            True if pattern is suspicious
        """
        self._request_patterns[key][endpoint] += 1

        total = sum(self._request_patterns[key].values())
        if total > self._suspicious_threshold:
            logger.warning(f"ABUSE: Suspicious request volume from {key}: {total}")
            return True

        return False

    def get_blocked_keys(self) -> list[str]:
        """Get currently blocked keys."""
        now = time.time()
        return [k for k, v in self._blocked_keys.items() if v > now]

    def unblock(self, key: str) -> None:
        """Manually unblock a key."""
        self._blocked_keys.pop(key, None)
        self._auth_failures.pop(key, None)
        logger.info(f"Key unblocked: {key}")
