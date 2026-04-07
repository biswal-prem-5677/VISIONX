"""
VisionX — Counting Module
============================
People & object counting with optional ROI-based zone counting
and directional (in/out) line-crossing detection.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Optional

import numpy as np
from loguru import logger

from shared.models import Detection, ROIZone


class Counter:
    """
    Object counting engine.
    
    Features:
        - Global object count by class
        - Per-ROI zone counting
        - Directional counting via virtual line crossing
    """

    def __init__(self):
        # Current frame counts
        self._current_counts: dict[str, int] = defaultdict(int)
        
        # Cumulative counts per class
        self._total_counts: dict[str, int] = defaultdict(int)
        
        # Per-zone counts
        self._zone_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        # Line crossing state
        self._line_crossings: dict[str, int] = {"in": 0, "out": 0}
        self._prev_positions: dict[int, tuple[float, float]] = {}

        logger.info("Counter initialized")

    def count(
        self,
        detections: list[Detection],
        roi_zones: Optional[list[ROIZone]] = None,
    ) -> dict:
        """
        Count objects in the current frame.
        
        Args:
            detections: List of detections (with or without track_id)
            roi_zones: Optional ROI zones for zone-based counting
            
        Returns:
            Count summary dict
        """
        # Reset current-frame counts
        self._current_counts.clear()

        for det in detections:
            self._current_counts[det.class_name] += 1

        # Update total counts
        for cls, count in self._current_counts.items():
            self._total_counts[cls] = max(self._total_counts[cls], count)

        # Zone-based counting
        if roi_zones:
            self._count_zones(detections, roi_zones)

        return self.get_summary()

    def _count_zones(
        self,
        detections: list[Detection],
        zones: list[ROIZone],
    ) -> None:
        """Count objects within each ROI zone."""
        # Reset zone counts for this frame
        for zone in zones:
            self._zone_counts[zone.id] = defaultdict(int)

        for det in detections:
            cx, cy = det.bbox.center
            for zone in zones:
                if not zone.enabled:
                    continue
                if self._point_in_polygon(cx, cy, zone.points):
                    self._zone_counts[zone.id][det.class_name] += 1

    @staticmethod
    def _point_in_polygon(x: float, y: float, polygon: list[tuple[int, int]]) -> bool:
        """Ray-casting algorithm to check if point is inside polygon."""
        n = len(polygon)
        inside = False

        j = n - 1
        for i in range(n):
            xi, yi = polygon[i]
            xj, yj = polygon[j]

            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            j = i

        return inside

    def count_line_crossing(
        self,
        detections: list[Detection],
        line_y: int,
    ) -> dict[str, int]:
        """
        Count directional line crossings (up = out, down = in).
        
        Args:
            detections: Tracked detections (must have track_id)
            line_y: Y-coordinate of the counting line
            
        Returns:
            {"in": count, "out": count}
        """
        for det in detections:
            if det.track_id is None:
                continue

            cx, cy = det.bbox.center
            prev = self._prev_positions.get(det.track_id)

            if prev is not None:
                prev_y = prev[1]
                # Crossed downward (in)
                if prev_y < line_y <= cy:
                    self._line_crossings["in"] += 1
                # Crossed upward (out)
                elif prev_y > line_y >= cy:
                    self._line_crossings["out"] += 1

            self._prev_positions[det.track_id] = (cx, cy)

        # Clean up old track positions
        active_ids = {d.track_id for d in detections if d.track_id is not None}
        self._prev_positions = {
            tid: pos for tid, pos in self._prev_positions.items()
            if tid in active_ids
        }

        return dict(self._line_crossings)

    def get_count(self, class_name: Optional[str] = None) -> int:
        """Get current frame count for a class (or total)."""
        if class_name:
            return self._current_counts.get(class_name, 0)
        return sum(self._current_counts.values())

    def get_zone_count(self, zone_id: str, class_name: Optional[str] = None) -> int:
        """Get count within a specific ROI zone."""
        zone = self._zone_counts.get(zone_id, {})
        if class_name:
            return zone.get(class_name, 0)
        return sum(zone.values())

    def get_summary(self) -> dict:
        """Get complete count summary."""
        return {
            "current": dict(self._current_counts),
            "total_objects": sum(self._current_counts.values()),
            "by_zone": {
                zid: dict(counts) for zid, counts in self._zone_counts.items()
            },
            "line_crossings": dict(self._line_crossings),
        }

    def reset(self) -> None:
        """Reset all counts."""
        self._current_counts.clear()
        self._total_counts.clear()
        self._zone_counts.clear()
        self._line_crossings = {"in": 0, "out": 0}
        self._prev_positions.clear()
        logger.info("Counter reset")
