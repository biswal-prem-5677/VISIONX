"""
VisionX — Behavior Analysis Module (Cloud)
==============================================
Analyzes tracking data for suspicious behaviors:
loitering, unusual movement, crowd formation, etc.
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any, Optional

from loguru import logger
from pydantic import BaseModel, Field


class BehaviorAlert(BaseModel):
    """A detected behavior anomaly."""
    track_id: int
    behavior_type: str  # loitering, erratic, crowding, abandoned_object
    confidence: float = 0.0
    duration_seconds: float = 0.0
    zone_id: Optional[str] = None
    message: str = ""


class BehaviorModule:
    """
    Behavior analysis module.

    Monitors tracked objects for suspicious or notable behaviors:
    - Loitering: object stays in same area too long
    - Erratic movement: rapid direction changes
    - Crowd formation: multiple objects clustering
    - Abandoned object: stationary non-person object
    """

    def __init__(
        self,
        loitering_threshold_seconds: float = 300.0,   # 5 minutes
        loitering_radius_px: float = 100.0,             # Pixels
        crowd_threshold: int = 5,                        # Min objects for crowd
        crowd_radius_px: float = 200.0,                  # Clustering radius
    ):
        self._loiter_threshold = loitering_threshold_seconds
        self._loiter_radius = loitering_radius_px
        self._crowd_threshold = crowd_threshold
        self._crowd_radius = crowd_radius_px

        # Track history: track_id -> [(x, y, timestamp)]
        self._positions: dict[int, list[tuple[float, float, float]]] = defaultdict(list)
        self._first_seen: dict[int, float] = {}
        self._alerts_issued: dict[str, float] = {}  # alert_key -> last_time
        self._alert_cooldown = 60.0  # seconds

        logger.info(
            f"Behavior Module initialized "
            f"(loiter: {loitering_threshold_seconds}s, "
            f"crowd: {crowd_threshold})"
        )

    def update(
        self,
        track_id: int,
        center_x: float,
        center_y: float,
        class_name: str = "person",
        timestamp: Optional[float] = None,
    ) -> list[BehaviorAlert]:
        """
        Update track position and check for behaviors.

        Args:
            track_id: The tracking ID
            center_x: Object center X
            center_y: Object center Y
            class_name: Object class ("person", "car", etc.)
            timestamp: Current time

        Returns:
            List of detected behavior alerts
        """
        ts = timestamp or time.time()
        alerts: list[BehaviorAlert] = []

        # Initialize first seen
        if track_id not in self._first_seen:
            self._first_seen[track_id] = ts

        # Store position
        self._positions[track_id].append((center_x, center_y, ts))

        # Trim to last 100 positions
        if len(self._positions[track_id]) > 100:
            self._positions[track_id] = self._positions[track_id][-100:]

        # Check loitering
        if class_name == "person":
            loiter_alert = self._check_loitering(track_id, ts)
            if loiter_alert:
                alerts.append(loiter_alert)

        # Check erratic movement
        erratic_alert = self._check_erratic(track_id)
        if erratic_alert:
            alerts.append(erratic_alert)

        return alerts

    def check_crowd(
        self,
        positions: dict[int, tuple[float, float]],
    ) -> list[BehaviorAlert]:
        """
        Check for crowd formation.

        Args:
            positions: Dict of track_id -> (center_x, center_y)

        Returns:
            List of crowd alerts
        """
        if len(positions) < self._crowd_threshold:
            return []

        alerts = []
        ids = list(positions.keys())

        # Simple clustering: check if N objects are within radius
        for i, id1 in enumerate(ids):
            nearby = 0
            x1, y1 = positions[id1]

            for j, id2 in enumerate(ids):
                if i == j:
                    continue
                x2, y2 = positions[id2]
                dist = ((x2 - x1)**2 + (y2 - y1)**2) ** 0.5

                if dist < self._crowd_radius:
                    nearby += 1

            if nearby >= self._crowd_threshold - 1:
                alert_key = f"crowd_{id1}"
                if self._can_alert(alert_key):
                    alerts.append(
                        BehaviorAlert(
                            track_id=id1,
                            behavior_type="crowding",
                            confidence=min(nearby / self._crowd_threshold, 1.0),
                            message=f"Crowd detected: {nearby + 1} objects clustered",
                        )
                    )
                break  # Only report crowd once

        return alerts

    def _check_loitering(self, track_id: int, now: float) -> Optional[BehaviorAlert]:
        """Check if a track is loitering."""
        positions = self._positions.get(track_id, [])
        if len(positions) < 10:
            return None

        first_seen = self._first_seen.get(track_id, now)
        duration = now - first_seen

        if duration < self._loiter_threshold:
            return None

        # Check if object stayed within radius
        recent = positions[-20:]
        avg_x = sum(p[0] for p in recent) / len(recent)
        avg_y = sum(p[1] for p in recent) / len(recent)

        max_deviation = max(
            ((p[0] - avg_x)**2 + (p[1] - avg_y)**2) ** 0.5
            for p in recent
        )

        if max_deviation < self._loiter_radius:
            alert_key = f"loiter_{track_id}"
            if self._can_alert(alert_key):
                return BehaviorAlert(
                    track_id=track_id,
                    behavior_type="loitering",
                    confidence=min(duration / (self._loiter_threshold * 2), 1.0),
                    duration_seconds=round(duration, 1),
                    message=f"Loitering detected: {duration:.0f}s in same area",
                )

        return None

    def _check_erratic(self, track_id: int) -> Optional[BehaviorAlert]:
        """Check for erratic movement (rapid direction changes)."""
        positions = self._positions.get(track_id, [])
        if len(positions) < 10:
            return None

        recent = positions[-10:]
        direction_changes = 0

        for i in range(2, len(recent)):
            dx1 = recent[i - 1][0] - recent[i - 2][0]
            dy1 = recent[i - 1][1] - recent[i - 2][1]
            dx2 = recent[i][0] - recent[i - 1][0]
            dy2 = recent[i][1] - recent[i - 1][1]

            # Direction changed if dot product is negative
            dot = dx1 * dx2 + dy1 * dy2
            if dot < 0:
                direction_changes += 1

        if direction_changes >= 5:
            alert_key = f"erratic_{track_id}"
            if self._can_alert(alert_key):
                return BehaviorAlert(
                    track_id=track_id,
                    behavior_type="erratic_movement",
                    confidence=min(direction_changes / 8.0, 1.0),
                    message=f"Erratic movement: {direction_changes} direction changes",
                )

        return None

    def _can_alert(self, key: str) -> bool:
        """Check cooldown for an alert."""
        now = time.time()
        last = self._alerts_issued.get(key, 0)
        if now - last >= self._alert_cooldown:
            self._alerts_issued[key] = now
            return True
        return False

    def remove_track(self, track_id: int) -> None:
        """Remove a track from monitoring."""
        self._positions.pop(track_id, None)
        self._first_seen.pop(track_id, None)

    def reset(self) -> None:
        """Reset all behavior tracking."""
        self._positions.clear()
        self._first_seen.clear()
        self._alerts_issued.clear()
