"""
VisionX — ROI Engine
=======================
Region of Interest management for the edge pipeline.
Allows defining polygon zones to focus processing on specific frame areas.
"""

from __future__ import annotations

from typing import Optional

import cv2
import numpy as np
from loguru import logger

from shared.models import BoundingBox, Detection, ROIZone


class ROIEngine:
    """
    Region of Interest engine.
    
    Manages polygon zones on the video frame. Used to:
        - Filter detections to only those within a zone
        - Count objects per zone
        - Trigger zone-specific events (enter/exit)
    """

    def __init__(self):
        self._zones: dict[str, ROIZone] = {}
        logger.info("ROI Engine initialized")

    def add_zone(self, zone: ROIZone) -> None:
        """Add or update a ROI zone."""
        self._zones[zone.id] = zone
        logger.info(f"ROI zone added: {zone.name} ({zone.id})")

    def remove_zone(self, zone_id: str) -> None:
        """Remove a ROI zone."""
        if zone_id in self._zones:
            del self._zones[zone_id]
            logger.info(f"ROI zone removed: {zone_id}")

    def get_zone(self, zone_id: str) -> Optional[ROIZone]:
        """Get a zone by ID."""
        return self._zones.get(zone_id)

    def get_all_zones(self) -> list[ROIZone]:
        """Get all registered zones."""
        return list(self._zones.values())

    def get_enabled_zones(self) -> list[ROIZone]:
        """Get only enabled zones."""
        return [z for z in self._zones.values() if z.enabled]

    def filter_detections(
        self,
        detections: list[Detection],
        zone_id: Optional[str] = None,
    ) -> list[Detection]:
        """
        Filter detections to only those within ROI zones.
        
        Args:
            detections: All detections from the detector
            zone_id: If provided, filter to a specific zone only.
                     If None, filter to any enabled zone.
                     
        Returns:
            Detections whose center falls within the specified zone(s)
        """
        if not self._zones:
            return detections

        if zone_id:
            zones = [self._zones[zone_id]] if zone_id in self._zones else []
        else:
            zones = self.get_enabled_zones()

        if not zones:
            return detections

        filtered = []
        for det in detections:
            cx, cy = det.bbox.center
            for zone in zones:
                if self._point_in_polygon(cx, cy, zone.points):
                    filtered.append(det)
                    break

        return filtered

    def get_zone_for_detection(self, detection: Detection) -> Optional[str]:
        """Return the zone ID that contains this detection, or None."""
        cx, cy = detection.bbox.center
        for zone in self.get_enabled_zones():
            if self._point_in_polygon(cx, cy, zone.points):
                return zone.id
        return None

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

    def create_zone_mask(self, zone: ROIZone, frame_shape: tuple) -> np.ndarray:
        """
        Create a binary mask for a zone (for visualization or masking).
        
        Args:
            zone: The ROI zone
            frame_shape: (height, width, channels) of the frame
            
        Returns:
            Binary mask (0 or 255)
        """
        mask = np.zeros(frame_shape[:2], dtype=np.uint8)
        pts = np.array(zone.points, np.int32)
        cv2.fillPoly(mask, [pts], 255)
        return mask

    def clear(self) -> None:
        """Remove all zones."""
        self._zones.clear()
        logger.info("All ROI zones cleared")

    def get_stats(self) -> dict:
        """Get ROI engine statistics."""
        return {
            "total_zones": len(self._zones),
            "enabled_zones": len(self.get_enabled_zones()),
            "zones": [
                {"id": z.id, "name": z.name, "enabled": z.enabled}
                for z in self._zones.values()
            ],
        }
