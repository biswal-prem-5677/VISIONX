"""
VisionX — Usage Tracking Service
====================================
Track feature usage across the platform for analytics.
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any

from loguru import logger
from pydantic import BaseModel, Field


class UsageRecord(BaseModel):
    """A single usage tracking record."""
    user_id: str
    feature: str
    action: str  # click, view, toggle, etc.
    duration_ms: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)


class UsageTracker:
    """
    Feature usage tracking and analytics.

    Records every feature interaction for:
    - Product analytics (which features are popular)
    - User behavior understanding
    - A/B testing metrics
    - Billing usage tracking
    """

    def __init__(self):
        self._records: list[UsageRecord] = []
        self._feature_counts: dict[str, int] = defaultdict(int)
        self._user_features: dict[str, dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        self._max_records = 50000

        logger.info("Usage Tracker initialized")

    def track(self, record: UsageRecord) -> None:
        """Record a usage event."""
        self._records.append(record)
        self._feature_counts[record.feature] += 1
        self._user_features[record.user_id][record.feature] += 1

        # Trim
        if len(self._records) > self._max_records:
            self._records = self._records[-self._max_records:]

    def get_top_features(self, limit: int = 20) -> list[dict]:
        """Get most used features."""
        sorted_features = sorted(
            self._feature_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        return [
            {"feature": f, "count": c}
            for f, c in sorted_features[:limit]
        ]

    def get_user_usage(self, user_id: str) -> dict[str, int]:
        """Get feature usage for a specific user."""
        return dict(self._user_features.get(user_id, {}))

    def get_feature_usage_over_time(
        self,
        feature: str,
        last_hours: int = 24,
    ) -> list[dict]:
        """Get hourly usage for a feature."""
        cutoff = time.time() - (last_hours * 3600)
        hourly: dict[str, int] = defaultdict(int)

        for record in self._records:
            if record.feature == feature and record.timestamp > cutoff:
                from datetime import datetime
                hour = datetime.fromtimestamp(record.timestamp).strftime("%H:00")
                hourly[hour] += 1

        return [
            {"hour": h, "count": c}
            for h, c in sorted(hourly.items())
        ]

    def get_stats(self) -> dict:
        """Get tracking statistics."""
        return {
            "total_records": len(self._records),
            "unique_features": len(self._feature_counts),
            "unique_users": len(self._user_features),
        }
