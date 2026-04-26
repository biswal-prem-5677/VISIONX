"""
VisionX — Rate Limiter Middleware
====================================
Redis-based rate limiting for API endpoints.
"""

from __future__ import annotations

import time

from loguru import logger


class RateLimiter:
    """
    Token bucket rate limiter.

    Limits requests per user/IP using a sliding window.
    Uses Redis for distributed rate limiting when available,
    falls back to in-memory for development.
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
    ):
        self._rpm = requests_per_minute
        self._rph = requests_per_hour
        self._counters: dict[str, list[float]] = {}  # key -> [timestamps]

        logger.info(
            f"Rate Limiter initialized "
            f"({requests_per_minute}/min, {requests_per_hour}/hr)"
        )

    def check(self, key: str) -> tuple[bool, dict[str, int]]:
        """
        Check if a request is allowed.

        Args:
            key: The rate limit key (user_id, IP, etc.)

        Returns:
            Tuple of (allowed: bool, headers: dict)
        """
        now = time.time()

        if key not in self._counters:
            self._counters[key] = []

        # Clean expired timestamps
        minute_ago = now - 60
        hour_ago = now - 3600
        self._counters[key] = [
            ts for ts in self._counters[key] if ts > hour_ago
        ]

        timestamps = self._counters[key]

        # Count requests in windows
        minute_count = sum(1 for ts in timestamps if ts > minute_ago)
        hour_count = len(timestamps)

        # Check limits
        allowed = minute_count < self._rpm and hour_count < self._rph

        headers = {
            "X-RateLimit-Limit-Minute": self._rpm,
            "X-RateLimit-Remaining-Minute": max(0, self._rpm - minute_count),
            "X-RateLimit-Limit-Hour": self._rph,
            "X-RateLimit-Remaining-Hour": max(0, self._rph - hour_count),
        }

        if allowed:
            self._counters[key].append(now)

        return allowed, headers

    def reset(self, key: str) -> None:
        """Reset rate limit for a key."""
        self._counters.pop(key, None)
