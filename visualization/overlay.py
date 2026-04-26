"""
VisionX — Visualization Overlay
=================================
Draws bounding boxes, labels, track IDs, FPS, and status on frames.
Used for both local preview and stream output.
"""

from __future__ import annotations

from typing import Optional

try:
    import cv2
except ImportError:
    cv2 = None  # type: ignore[assignment]
import numpy as np

from shared.constants import COLORS
from shared.models import Detection, FrameResult, ROIZone


class Overlay:
    """
    Visualization overlay renderer.

    Draws:
        - Bounding boxes (color-coded by class)
        - Class labels + confidence scores
        - Track IDs
        - FPS counter
        - ROI zones
        - Status messages
    """

    def __init__(
        self,
        show_boxes: bool = True,
        show_labels: bool = True,
        show_track_ids: bool = True,
        show_confidence: bool = True,
        show_fps: bool = True,
        box_thickness: int = 2,
        font_scale: float = 0.6,
        font_thickness: int = 1,
    ):
        self.show_boxes = show_boxes
        self.show_labels = show_labels
        self.show_track_ids = show_track_ids
        self.show_confidence = show_confidence
        self.show_fps = show_fps
        self.box_thickness = box_thickness
        self.font_scale = font_scale
        self.font_thickness = font_thickness
        self._font = cv2.FONT_HERSHEY_SIMPLEX

    def draw(
        self,
        frame: np.ndarray,
        result: FrameResult,
        roi_zones: Optional[list[ROIZone]] = None,
        status_text: Optional[str] = None,
    ) -> np.ndarray:
        """
        Draw all overlays on a frame.

        Args:
            frame: BGR image to draw on
            result: FrameResult with detections
            roi_zones: Optional ROI zones to display
            status_text: Optional status message

        Returns:
            Frame with overlays drawn
        """
        output = frame.copy()

        # Draw ROI zones first (background)
        if roi_zones:
            self._draw_roi_zones(output, roi_zones)

        # Draw detections
        for det in result.detections:
            self._draw_detection(output, det)

        # Draw FPS
        if self.show_fps:
            self._draw_fps(output, result.fps, result.processing_time_ms)

        # Draw detection count
        self._draw_count(output, result.detection_count)

        # Draw status text
        if status_text:
            self._draw_status(output, status_text)

        return output

    def _draw_detection(self, frame: np.ndarray, det: Detection) -> None:
        """Draw a single detection box with label."""
        bbox = det.bbox
        x1, y1 = int(bbox.x1), int(bbox.y1)
        x2, y2 = int(bbox.x2), int(bbox.y2)

        # Get color for this class
        color = COLORS.get(det.class_name, COLORS["default"])

        # Draw bounding box
        if self.show_boxes:
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, self.box_thickness)

            # Draw corner accents (premium look)
            corner_len = min(20, min(x2 - x1, y2 - y1) // 4)
            t = self.box_thickness + 1
            # Top-left
            cv2.line(frame, (x1, y1), (x1 + corner_len, y1), color, t)
            cv2.line(frame, (x1, y1), (x1, y1 + corner_len), color, t)
            # Top-right
            cv2.line(frame, (x2, y1), (x2 - corner_len, y1), color, t)
            cv2.line(frame, (x2, y1), (x2, y1 + corner_len), color, t)
            # Bottom-left
            cv2.line(frame, (x1, y2), (x1 + corner_len, y2), color, t)
            cv2.line(frame, (x1, y2), (x1, y2 - corner_len), color, t)
            # Bottom-right
            cv2.line(frame, (x2, y2), (x2 - corner_len, y2), color, t)
            cv2.line(frame, (x2, y2), (x2, y2 - corner_len), color, t)

        # Build label text
        if self.show_labels:
            parts = [det.class_name]
            if self.show_confidence:
                parts.append(f"{det.confidence:.0%}")
            if self.show_track_ids and det.track_id is not None:
                parts.insert(0, f"ID:{det.track_id}")
            label = " | ".join(parts)

            # Draw label background
            (tw, th), baseline = cv2.getTextSize(label, self._font, self.font_scale, self.font_thickness)
            label_y = max(y1 - 10, th + 4)
            cv2.rectangle(frame, (x1, label_y - th - 4), (x1 + tw + 8, label_y + 4), color, -1)
            cv2.putText(frame, label, (x1 + 4, label_y), self._font, self.font_scale, (0, 0, 0), self.font_thickness)

    def _draw_fps(self, frame: np.ndarray, fps: float, proc_ms: float) -> None:
        """Draw FPS and processing time in top-left corner."""
        h, w = frame.shape[:2]
        text = f"FPS: {fps:.1f} | Proc: {proc_ms:.0f}ms"

        # Background bar
        (tw, th), _ = cv2.getTextSize(text, self._font, 0.5, 1)
        cv2.rectangle(frame, (0, 0), (tw + 16, th + 16), (0, 0, 0), -1)
        cv2.putText(frame, text, (8, th + 8), self._font, 0.5, (0, 255, 128), 1)

    def _draw_count(self, frame: np.ndarray, count: int) -> None:
        """Draw detection count in top-right corner."""
        h, w = frame.shape[:2]
        text = f"Objects: {count}"
        (tw, th), _ = cv2.getTextSize(text, self._font, 0.5, 1)
        x = w - tw - 16
        cv2.rectangle(frame, (x, 0), (w, th + 16), (0, 0, 0), -1)
        cv2.putText(frame, text, (x + 8, th + 8), self._font, 0.5, (255, 200, 0), 1)

    def _draw_status(self, frame: np.ndarray, text: str) -> None:
        """Draw status message at bottom."""
        h, w = frame.shape[:2]
        (tw, th), _ = cv2.getTextSize(text, self._font, 0.5, 1)
        y = h - 8
        cv2.rectangle(frame, (0, y - th - 8), (tw + 16, h), (0, 0, 100), -1)
        cv2.putText(frame, text, (8, y), self._font, 0.5, (255, 255, 255), 1)

    def _draw_roi_zones(self, frame: np.ndarray, zones: list[ROIZone]) -> None:
        """Draw ROI zone polygons."""
        for zone in zones:
            if not zone.enabled:
                continue
            pts = np.array(zone.points, np.int32)
            # Semi-transparent fill
            overlay = frame.copy()
            cv2.fillPoly(overlay, [pts], zone.color)
            cv2.addWeighted(overlay, 0.15, frame, 0.85, 0, frame)
            # Border
            cv2.polylines(frame, [pts], True, zone.color, 2)
            # Label
            if zone.points:
                cv2.putText(frame, zone.name, tuple(zone.points[0]), self._font, 0.5, zone.color, 1)
