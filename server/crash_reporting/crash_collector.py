"""
VisionX — Crash Reporting
=============================
Collects and analyzes crash reports from clients.
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any

from loguru import logger
from pydantic import BaseModel, Field


class CrashEntry(BaseModel):
    """A crash report entry."""
    crash_id: str
    error_message: str
    stack_trace: str = ""
    user_id: str = ""
    device_info: dict[str, Any] = Field(default_factory=dict)
    app_version: str = ""
    severity: str = "error"
    timestamp: float = Field(default_factory=time.time)


class CrashCollector:
    """
    Crash report collector and analyzer.

    Collects crash reports, groups by error signature,
    and provides aggregated crash analytics.
    """

    def __init__(self):
        self._reports: list[CrashEntry] = []
        self._error_groups: dict[str, list[CrashEntry]] = defaultdict(list)
        self._max_reports = 10000

        logger.info("Crash Collector initialized")

    def submit(self, crash: CrashEntry) -> str:
        """Submit a crash report."""
        self._reports.append(crash)

        # Group by error message (signature)
        signature = crash.error_message[:100]
        self._error_groups[signature].append(crash)

        # Trim
        if len(self._reports) > self._max_reports:
            self._reports = self._reports[-self._max_reports:]

        logger.warning(
            f"Crash reported: {crash.error_message[:80]} "
            f"(user: {crash.user_id})"
        )

        return crash.crash_id

    def get_top_crashes(self, limit: int = 10) -> list[dict]:
        """Get most frequent crash groups."""
        sorted_groups = sorted(
            self._error_groups.items(),
            key=lambda x: len(x[1]),
            reverse=True,
        )

        return [
            {
                "error": sig,
                "count": len(reports),
                "last_seen": max(r.timestamp for r in reports),
                "affected_users": len(set(r.user_id for r in reports)),
            }
            for sig, reports in sorted_groups[:limit]
        ]

    def get_recent(self, limit: int = 50) -> list[CrashEntry]:
        """Get recent crash reports."""
        return self._reports[-limit:]

    def get_stats(self) -> dict:
        """Get crash statistics."""
        return {
            "total_reports": len(self._reports),
            "unique_errors": len(self._error_groups),
            "reports_today": sum(
                1 for r in self._reports
                if r.timestamp > time.time() - 86400
            ),
        }
