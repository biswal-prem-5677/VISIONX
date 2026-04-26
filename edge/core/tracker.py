"""
VisionX — Object Tracker
==========================
Simple IoU-based multi-object tracker with Kalman filter prediction.
Assigns persistent IDs, handles occlusion, and tracks movement.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Optional

import numpy as np
from loguru import logger

from shared.constants import TRACKER_IOU_THRESHOLD, TRACKER_MAX_AGE, TRACKER_MIN_HITS
from shared.models import BoundingBox, Detection, Track, TrackState


def _iou(box_a: BoundingBox, box_b: BoundingBox) -> float:
    """Compute Intersection over Union between two bounding boxes."""
    x1 = max(box_a.x1, box_b.x1)
    y1 = max(box_a.y1, box_b.y1)
    x2 = min(box_a.x2, box_b.x2)
    y2 = min(box_a.y2, box_b.y2)

    inter_area = max(0, x2 - x1) * max(0, y2 - y1)
    area_a = box_a.area
    area_b = box_b.area
    union_area = area_a + area_b - inter_area

    if union_area <= 0:
        return 0.0
    return inter_area / union_area


class _KalmanBoxTracker:
    """Internal Kalman filter tracker for a single object."""

    _id_counter = 0

    def __init__(self, bbox: BoundingBox, class_name: str):
        _KalmanBoxTracker._id_counter += 1
        self.id = _KalmanBoxTracker._id_counter
        self.class_name = class_name
        self.bbox = bbox
        self.hits = 1
        self.age = 0
        self.time_since_update = 0
        self.state = TrackState.TENTATIVE
        self._history: list[BoundingBox] = [bbox]
        self._velocity = (0.0, 0.0)

    def update(self, bbox: BoundingBox) -> None:
        """Update tracker with a matched detection."""
        # Calculate velocity from center point movement
        old_cx, old_cy = self.bbox.center
        new_cx, new_cy = bbox.center
        self._velocity = (new_cx - old_cx, new_cy - old_cy)

        self.bbox = bbox
        self.hits += 1
        self.time_since_update = 0
        self._history.append(bbox)

        # Keep history bounded
        if len(self._history) > 100:
            self._history = self._history[-100:]

    def predict(self) -> BoundingBox:
        """Predict next position using simple velocity model."""
        self.age += 1
        self.time_since_update += 1

        vx, vy = self._velocity
        predicted = BoundingBox(
            x1=self.bbox.x1 + vx,
            y1=self.bbox.y1 + vy,
            x2=self.bbox.x2 + vx,
            y2=self.bbox.y2 + vy,
        )
        return predicted

    @property
    def velocity(self) -> tuple[float, float]:
        return self._velocity

    def to_track(self) -> Track:
        return Track(
            track_id=self.id,
            class_name=self.class_name,
            bbox=self.bbox,
            state=self.state,
            age=self.age,
            hits=self.hits,
            time_since_update=self.time_since_update,
            velocity=self._velocity,
        )


class Tracker:
    """
    Multi-object tracker using IoU matching with Kalman prediction.

    Assigns persistent unique IDs to detected objects and maintains
    tracks across frames, handling temporary occlusion.
    """

    def __init__(
        self,
        max_age: int = TRACKER_MAX_AGE,
        min_hits: int = TRACKER_MIN_HITS,
        iou_threshold: float = TRACKER_IOU_THRESHOLD,
    ):
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold

        self._trackers: list[_KalmanBoxTracker] = []
        self._frame_count: int = 0

        # Statistics
        self._total_tracks_created: int = 0
        self._total_tracks_deleted: int = 0
        self._active_track_classes: dict[str, int] = defaultdict(int)

    def update(self, detections: list[Detection]) -> list[Detection]:
        """
        Update tracker with new detections and return detections with track IDs.

        Args:
            detections: List of Detection objects from the detector

        Returns:
            Same detections with track_id assigned
        """
        self._frame_count += 1

        # Predict new positions for existing trackers
        for trk in self._trackers:
            trk.predict()

        # Build IoU cost matrix
        matched, unmatched_dets, unmatched_trks = self._match_detections(detections)

        # Update matched trackers and capture track IDs before any removal
        matched_track_ids: dict[int, int] = {}  # det_idx -> track_id
        for det_idx, trk_idx in matched:
            self._trackers[trk_idx].update(detections[det_idx].bbox)
            self._trackers[trk_idx].class_name = detections[det_idx].class_name
            matched_track_ids[det_idx] = self._trackers[trk_idx].id

        # Create new trackers for unmatched detections
        for det_idx in unmatched_dets:
            det = detections[det_idx]
            trk = _KalmanBoxTracker(det.bbox, det.class_name)
            self._trackers.append(trk)
            self._total_tracks_created += 1

        # Update track states and remove dead tracks
        active_trackers = []
        for trk in self._trackers:
            if trk.time_since_update > self.max_age:
                trk.state = TrackState.DELETED
                self._total_tracks_deleted += 1
                continue

            if trk.hits >= self.min_hits:
                trk.state = TrackState.CONFIRMED

            active_trackers.append(trk)

        self._trackers = active_trackers

        # Assign track IDs to detections (using saved IDs, not list indices)
        tracked_detections = []
        for det_idx, trk_idx in matched:
            det = detections[det_idx].model_copy()
            det.track_id = matched_track_ids[det_idx]
            tracked_detections.append(det)

        # Unmatched detections get temporary track IDs from new trackers
        for det_idx in unmatched_dets:
            det = detections[det_idx].model_copy()
            # Find the newly created tracker for this detection
            for trk in self._trackers:
                if trk.hits == 1 and _iou(trk.bbox, det.bbox) > 0.9:
                    det.track_id = trk.id
                    break
            tracked_detections.append(det)

        # Update class counts
        self._active_track_classes.clear()
        for trk in self._trackers:
            if trk.state == TrackState.CONFIRMED:
                self._active_track_classes[trk.class_name] += 1

        return tracked_detections

    def _match_detections(
        self,
        detections: list[Detection],
    ) -> tuple[list[tuple[int, int]], list[int], list[int]]:
        """Match detections to existing trackers using IoU."""
        if not self._trackers or not detections:
            return [], list(range(len(detections))), list(range(len(self._trackers)))

        n_dets = len(detections)
        n_trks = len(self._trackers)

        # Compute IoU matrix
        iou_matrix = np.zeros((n_dets, n_trks))
        for d in range(n_dets):
            for t in range(n_trks):
                iou_matrix[d, t] = _iou(detections[d].bbox, self._trackers[t].bbox)

        # Greedy matching (simple but effective)
        matched = []
        used_dets = set()
        used_trks = set()

        while True:
            if iou_matrix.size == 0:
                break
            max_iou = iou_matrix.max()
            if max_iou < self.iou_threshold:
                break

            d_idx, t_idx = np.unravel_index(iou_matrix.argmax(), iou_matrix.shape)
            matched.append((int(d_idx), int(t_idx)))
            used_dets.add(int(d_idx))
            used_trks.add(int(t_idx))

            # Zero out matched row and column
            iou_matrix[d_idx, :] = 0
            iou_matrix[:, t_idx] = 0

        unmatched_dets = [d for d in range(n_dets) if d not in used_dets]
        unmatched_trks = [t for t in range(n_trks) if t not in used_trks]

        return matched, unmatched_dets, unmatched_trks

    def get_active_tracks(self) -> list[Track]:
        """Get all confirmed active tracks."""
        return [
            trk.to_track()
            for trk in self._trackers
            if trk.state == TrackState.CONFIRMED
        ]

    def get_track_count(self, class_name: Optional[str] = None) -> int:
        """Count active confirmed tracks, optionally filtered by class."""
        if class_name:
            return self._active_track_classes.get(class_name, 0)
        return sum(self._active_track_classes.values())

    def reset(self) -> None:
        """Reset all tracks."""
        self._trackers.clear()
        self._frame_count = 0
        _KalmanBoxTracker._id_counter = 0
        logger.info("Tracker reset")

    def get_stats(self) -> dict:
        return {
            "active_tracks": len(self._trackers),
            "confirmed_tracks": self.get_track_count(),
            "total_created": self._total_tracks_created,
            "total_deleted": self._total_tracks_deleted,
            "class_counts": dict(self._active_track_classes),
            "frame_count": self._frame_count,
        }
