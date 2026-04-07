"""
VisionX — Speed Estimation Module (Cloud)
=============================================
Estimates object movement speed using tracking data and
camera calibration (pixels-per-meter conversion).
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any, Optional

from loguru import logger
from pydantic import BaseModel, Field


class SpeedResult(BaseModel):
    """Speed estimation result for a tracked object."""
    track_id: int
    speed_px_per_sec: float = 0.0   # Speed in pixels/second
    speed_mps: float = 0.0          # Speed in meters/second
    speed_kmph: float = 0.0         # Speed in km/h
    direction: str = "unknown"      # N, S, E, W, NE, NW, SE, SW


class SpeedModule:
    """
    Speed estimation module.

    Tracks object positions over time and calculates speed.
    Requires pixels_per_meter calibration for real-world units.
    """

    def __init__(self, pixels_per_meter: float = 50.0, fps: float = 30.0):
        self._ppm = pixels_per_meter  # Pixels per meter (camera calibration)
        self._fps = fps
        self._history: dict[int, list[tuple[float, float, float]]] = defaultdict(list)
        # track_id -> [(x, y, timestamp), ...]
        self._max_history = 30  # Keep last N positions

        logger.info(
            f"Speed Module initialized "
            f"(ppm: {pixels_per_meter}, fps: {fps})"
        )

    def update(
        self,
        track_id: int,
        center_x: float,
        center_y: float,
        timestamp: Optional[float] = None,
    ) -> SpeedResult:
        """
        Update track position and calculate speed.

        Args:
            track_id: The tracking ID
            center_x: Object center X position (pixels)
            center_y: Object center Y position (pixels)
            timestamp: Current time (defaults to time.time())

        Returns:
            SpeedResult with calculated speed
        """
        ts = timestamp or time.time()

        # Store position
        self._history[track_id].append((center_x, center_y, ts))

        # Trim history
        if len(self._history[track_id]) > self._max_history:
            self._history[track_id] = self._history[track_id][-self._max_history:]

        # Need at least 2 positions to calculate speed
        history = self._history[track_id]
        if len(history) < 2:
            return SpeedResult(track_id=track_id)

        # Calculate speed using last N positions for smoothing
        window = min(10, len(history))
        positions = history[-window:]

        total_dist_px = 0.0
        for i in range(1, len(positions)):
            dx = positions[i][0] - positions[i - 1][0]
            dy = positions[i][1] - positions[i - 1][1]
            total_dist_px += (dx**2 + dy**2) ** 0.5

        time_elapsed = positions[-1][2] - positions[0][2]

        if time_elapsed <= 0:
            return SpeedResult(track_id=track_id)

        # Pixels per second
        speed_px = total_dist_px / time_elapsed

        # Real-world speed
        speed_mps = speed_px / self._ppm
        speed_kmph = speed_mps * 3.6

        # Direction (from first to last position in window)
        direction = self._calculate_direction(
            positions[0][0], positions[0][1],
            positions[-1][0], positions[-1][1],
        )

        return SpeedResult(
            track_id=track_id,
            speed_px_per_sec=round(speed_px, 2),
            speed_mps=round(speed_mps, 2),
            speed_kmph=round(speed_kmph, 2),
            direction=direction,
        )

    @staticmethod
    def _calculate_direction(x1: float, y1: float, x2: float, y2: float) -> str:
        """Calculate direction of movement."""
        import math

        dx = x2 - x1
        dy = y2 - y1

        if abs(dx) < 5 and abs(dy) < 5:
            return "stationary"

        angle = math.degrees(math.atan2(-dy, dx))  # -dy because screen Y is inverted
        angle = (angle + 360) % 360

        directions = [
            (337.5, 360, "E"), (0, 22.5, "E"),
            (22.5, 67.5, "NE"), (67.5, 112.5, "N"),
            (112.5, 157.5, "NW"), (157.5, 202.5, "W"),
            (202.5, 247.5, "SW"), (247.5, 292.5, "S"),
            (292.5, 337.5, "SE"),
        ]

        for low, high, d in directions:
            if low <= angle < high:
                return d

        return "unknown"

    def remove_track(self, track_id: int) -> None:
        """Remove a track from history."""
        self._history.pop(track_id, None)

    def reset(self) -> None:
        """Clear all tracking data."""
        self._history.clear()

    def set_calibration(self, pixels_per_meter: float) -> None:
        """Update camera calibration."""
        self._ppm = pixels_per_meter
        logger.info(f"Speed calibration updated: {pixels_per_meter} px/m")
