"""
VisionX — Analytics Engine (Cloud)
======================================
Aggregates detection, tracking, and event data into
meaningful analytics: counts over time, heatmaps, trends.
"""

from __future__ import annotations

import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Optional

from loguru import logger
from pydantic import BaseModel, Field


class TimeSeriesPoint(BaseModel):
    """A single data point in a time series."""
    timestamp: datetime
    value: float
    label: str = ""


class HeatmapCell(BaseModel):
    """A single cell in a spatial heatmap."""
    x: int
    y: int
    intensity: float


class AnalyticsSummary(BaseModel):
    """Summary analytics for a time period."""
    period_start: datetime
    period_end: datetime
    total_detections: int = 0
    total_events: int = 0
    detection_by_class: dict[str, int] = Field(default_factory=dict)
    peak_count: int = 0
    peak_time: Optional[datetime] = None
    average_count: float = 0.0
    zone_activity: dict[str, int] = Field(default_factory=dict)


class AnalyticsEngine:
    """
    Analytics aggregation engine.

    Collects detection and event data over time and produces:
    - Object counts over time (time series)
    - Spatial heatmaps (activity density)
    - Peak/average/trend analysis
    - Per-class and per-zone breakdowns
    """

    def __init__(self, heatmap_resolution: int = 50):
        self._heatmap_res = heatmap_resolution  # Grid cell size in pixels
        self._count_history: list[tuple[float, dict[str, int]]] = []
        self._heatmap_data: dict[tuple[int, int], int] = defaultdict(int)
        self._event_counts: dict[str, int] = defaultdict(int)
        self._hourly_counts: dict[str, dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        self._total_frames: int = 0
        self._start_time: float = time.time()

        logger.info(
            f"Analytics Engine initialized "
            f"(heatmap grid: {heatmap_resolution}px)"
        )

    def record_frame(
        self,
        detections: list[dict[str, Any]],
        timestamp: Optional[float] = None,
    ) -> None:
        """
        Record detections from a processed frame.

        Args:
            detections: List of detection dicts with keys:
                        class_name, center_x, center_y, confidence
            timestamp: Frame timestamp
        """
        ts = timestamp or time.time()
        self._total_frames += 1

        # Count by class
        class_counts: dict[str, int] = defaultdict(int)
        for det in detections:
            cls = det.get("class_name", "unknown")
            class_counts[cls] += 1

            # Update heatmap
            cx = det.get("center_x", 0)
            cy = det.get("center_y", 0)
            grid_x = int(cx // self._heatmap_res)
            grid_y = int(cy // self._heatmap_res)
            self._heatmap_data[(grid_x, grid_y)] += 1

        # Store count snapshot
        self._count_history.append((ts, dict(class_counts)))

        # Update hourly breakdown
        hour_key = datetime.fromtimestamp(ts).strftime("%Y-%m-%d_%H")
        for cls, count in class_counts.items():
            self._hourly_counts[hour_key][cls] += count

        # Trim history (keep last 10,000 frames)
        if len(self._count_history) > 10000:
            self._count_history = self._count_history[-10000:]

    def record_event(self, event_type: str) -> None:
        """Record an event occurrence."""
        self._event_counts[event_type] += 1

    def get_count_timeseries(
        self,
        class_name: str = "person",
        last_n_seconds: float = 300,
    ) -> list[TimeSeriesPoint]:
        """
        Get object count time series.

        Args:
            class_name: Class to get counts for
            last_n_seconds: Time window in seconds

        Returns:
            List of TimeSeriesPoint objects
        """
        now = time.time()
        cutoff = now - last_n_seconds

        points = []
        for ts, counts in self._count_history:
            if ts >= cutoff:
                points.append(
                    TimeSeriesPoint(
                        timestamp=datetime.fromtimestamp(ts),
                        value=float(counts.get(class_name, 0)),
                        label=class_name,
                    )
                )

        return points

    def get_heatmap(
        self,
        frame_width: int = 1280,
        frame_height: int = 720,
    ) -> list[HeatmapCell]:
        """
        Get spatial activity heatmap.

        Returns:
            List of HeatmapCell objects with normalized intensities
        """
        if not self._heatmap_data:
            return []

        max_intensity = max(self._heatmap_data.values())
        if max_intensity == 0:
            return []

        cells = []
        for (gx, gy), count in self._heatmap_data.items():
            cells.append(
                HeatmapCell(
                    x=gx * self._heatmap_res,
                    y=gy * self._heatmap_res,
                    intensity=count / max_intensity,
                )
            )

        return sorted(cells, key=lambda c: c.intensity, reverse=True)

    def get_summary(
        self,
        last_n_seconds: float = 3600,
    ) -> AnalyticsSummary:
        """
        Get analytics summary for a time period.

        Args:
            last_n_seconds: Time window in seconds (default: 1 hour)

        Returns:
            AnalyticsSummary object
        """
        now = time.time()
        cutoff = now - last_n_seconds

        total = 0
        class_totals: dict[str, int] = defaultdict(int)
        peak_count = 0
        peak_time = None
        count_snapshots = []

        for ts, counts in self._count_history:
            if ts >= cutoff:
                frame_total = sum(counts.values())
                total += frame_total
                count_snapshots.append(frame_total)

                for cls, c in counts.items():
                    class_totals[cls] += c

                if frame_total > peak_count:
                    peak_count = frame_total
                    peak_time = datetime.fromtimestamp(ts)

        avg_count = (
            sum(count_snapshots) / len(count_snapshots)
            if count_snapshots
            else 0.0
        )

        return AnalyticsSummary(
            period_start=datetime.fromtimestamp(cutoff),
            period_end=datetime.fromtimestamp(now),
            total_detections=total,
            total_events=sum(self._event_counts.values()),
            detection_by_class=dict(class_totals),
            peak_count=peak_count,
            peak_time=peak_time,
            average_count=round(avg_count, 2),
        )

    def get_stats(self) -> dict:
        """Get engine statistics."""
        elapsed = time.time() - self._start_time
        return {
            "total_frames_analyzed": self._total_frames,
            "uptime_seconds": round(elapsed, 1),
            "heatmap_cells": len(self._heatmap_data),
            "event_counts": dict(self._event_counts),
            "history_size": len(self._count_history),
        }

    def reset(self) -> None:
        """Reset all analytics data."""
        self._count_history.clear()
        self._heatmap_data.clear()
        self._event_counts.clear()
        self._hourly_counts.clear()
        self._total_frames = 0
        self._start_time = time.time()
        logger.info("Analytics engine reset")
