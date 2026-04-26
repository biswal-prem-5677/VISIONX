"""
VisionX — Admin Dashboard Service
=====================================
Aggregates system-wide data for admin god-mode dashboard.
"""

from __future__ import annotations

import time

from loguru import logger
from pydantic import BaseModel


class SystemHealth(BaseModel):
    """System health snapshot."""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_percent: float = 0.0
    active_devices: int = 0
    active_users: int = 0
    events_per_minute: float = 0.0
    api_latency_ms: float = 0.0
    uptime_hours: float = 0.0


class AdminDashboardService:
    """
    Admin dashboard data aggregation.

    Provides system-wide metrics, user stats,
    and health monitoring for the admin dashboard.
    """

    def __init__(self):
        self._start_time = time.time()
        self._request_count = 0
        self._error_count = 0

        logger.info("Admin Dashboard Service initialized")

    def get_health(self) -> SystemHealth:
        """Get current system health."""
        try:
            import psutil

            return SystemHealth(
                cpu_percent=psutil.cpu_percent(),
                memory_percent=psutil.virtual_memory().percent,
                disk_percent=psutil.disk_usage("/").percent,
                uptime_hours=round(
                    (time.time() - self._start_time) / 3600, 2
                ),
            )
        except ImportError:
            return SystemHealth(
                uptime_hours=round(
                    (time.time() - self._start_time) / 3600, 2
                ),
            )

    def record_request(self) -> None:
        """Record an API request."""
        self._request_count += 1

    def record_error(self) -> None:
        """Record an API error."""
        self._error_count += 1

    def get_stats(self) -> dict:
        """Get admin stats."""
        return {
            "total_requests": self._request_count,
            "total_errors": self._error_count,
            "error_rate": (
                self._error_count / self._request_count
                if self._request_count > 0
                else 0.0
            ),
            "uptime_seconds": round(time.time() - self._start_time, 1),
        }
