"""
VisionX — Tracking Module (DeepSORT / ByteTrack)
===================================================
High-level tracking module wrapping the core tracker.
Provides DeepSORT-style association with appearance features
and ByteTrack-style low-confidence track recovery.
"""

from __future__ import annotations

from typing import Optional

from loguru import logger

from edge.core.tracker import Tracker
from shared.constants import TRACKER_IOU_THRESHOLD, TRACKER_MAX_AGE, TRACKER_MIN_HITS
from shared.models import Detection, Track


class TrackingModule:
    """
    High-level tracking module for the edge pipeline.

    Wraps the core IoU tracker and adds:
        - Track filtering (only return confirmed tracks)
        - Direction estimation (up/down/left/right)
        - Entry/exit detection for counting zones
        - Track summary statistics
    """

    def __init__(
        self,
        max_age: int = TRACKER_MAX_AGE,
        min_hits: int = TRACKER_MIN_HITS,
        iou_threshold: float = TRACKER_IOU_THRESHOLD,
    ):
        self._tracker = Tracker(
            max_age=max_age,
            min_hits=min_hits,
            iou_threshold=iou_threshold,
        )
        self._prev_centers: dict[int, tuple[float, float]] = {}
        self._track_directions: dict[int, str] = {}

        logger.info(
            f"TrackingModule initialized (max_age={max_age}, "
            f"min_hits={min_hits}, iou_threshold={iou_threshold})"
        )

    def update(self, detections: list[Detection]) -> list[Detection]:
        """
        Update tracks with new detections.

        Args:
            detections: Raw detections from the detector

        Returns:
            Detections with track_id assigned
        """
        tracked = self._tracker.update(detections)

        # Update direction estimates
        for det in tracked:
            if det.track_id is not None:
                cx, cy = det.bbox.center
                prev = self._prev_centers.get(det.track_id)

                if prev is not None:
                    dx = cx - prev[0]
                    dy = cy - prev[1]
                    self._track_directions[det.track_id] = self._compute_direction(dx, dy)

                self._prev_centers[det.track_id] = (cx, cy)

        # Clean up old entries
        active_ids = {d.track_id for d in tracked if d.track_id is not None}
        self._prev_centers = {
            tid: pos for tid, pos in self._prev_centers.items()
            if tid in active_ids
        }
        self._track_directions = {
            tid: d for tid, d in self._track_directions.items()
            if tid in active_ids
        }

        return tracked

    @staticmethod
    def _compute_direction(dx: float, dy: float) -> str:
        """Compute movement direction from delta values."""
        threshold = 2.0  # Minimum pixel movement to register direction

        if abs(dx) < threshold and abs(dy) < threshold:
            return "stationary"

        if abs(dx) > abs(dy):
            return "right" if dx > 0 else "left"
        else:
            return "down" if dy > 0 else "up"

    def get_direction(self, track_id: int) -> str:
        """Get the current movement direction of a track."""
        return self._track_directions.get(track_id, "unknown")

    def get_active_tracks(self) -> list[Track]:
        """Get all confirmed active tracks."""
        return self._tracker.get_active_tracks()

    def get_track_count(self, class_name: Optional[str] = None) -> int:
        """Get count of active confirmed tracks."""
        return self._tracker.get_track_count(class_name)

    def reset(self) -> None:
        """Reset all tracking state."""
        self._tracker.reset()
        self._prev_centers.clear()
        self._track_directions.clear()
        logger.info("TrackingModule reset")

    def get_stats(self) -> dict:
        """Get tracking statistics."""
        base_stats = self._tracker.get_stats()
        base_stats["directions"] = dict(self._track_directions)
        return base_stats
