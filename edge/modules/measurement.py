"""
VisionX — Measurement Module
================================
Distance estimation and area calculation from bounding boxes.
Uses pixel-to-real-world calibration for approximate measurements.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from loguru import logger

from shared.models import Detection


@dataclass
class CalibrationConfig:
    """
    Calibration parameters for pixel-to-world conversion.

    Attributes:
        focal_length_px: Focal length in pixels (camera-dependent)
        known_width_m: Known real-world width of reference object in meters
        sensor_height_px: Frame height in pixels
    """
    focal_length_px: float = 700.0       # Default estimate for typical webcam
    known_width_m: float = 0.5           # Default: average shoulder width ~0.5m
    reference_class: str = "person"       # Class used for auto-calibration
    sensor_height_px: int = 720


class Measurement:
    """
    Distance & area estimation from detected bounding boxes.

    Features:
        - Estimate distance from camera to detected object
        - Calculate bounding box area in pixels
        - Estimate real-world area (with calibration)
        - Measure distance between two detected objects
    """

    def __init__(self, config: Optional[CalibrationConfig] = None):
        self.config = config or CalibrationConfig()
        logger.info("Measurement module initialized")

    def estimate_distance(self, detection: Detection) -> float:
        """
        Estimate distance from camera to detected object (meters).

        Uses the pinhole camera model:
            distance = (known_width * focal_length) / perceived_width_px

        Args:
            detection: A Detection object

        Returns:
            Estimated distance in meters
        """
        perceived_width = detection.bbox.width

        if perceived_width <= 0:
            return 0.0

        distance = (self.config.known_width_m * self.config.focal_length_px) / perceived_width
        return round(distance, 2)

    def estimate_distance_between(
        self,
        det_a: Detection,
        det_b: Detection,
    ) -> float:
        """
        Estimate the distance between two detected objects in meters.

        This is a rough pixel-space estimate, not true 3D distance.

        Args:
            det_a: First detection
            det_b: Second detection

        Returns:
            Estimated distance in meters
        """
        cx_a, cy_a = det_a.bbox.center
        cx_b, cy_b = det_b.bbox.center

        pixel_dist = math.sqrt((cx_a - cx_b) ** 2 + (cy_a - cy_b) ** 2)

        # Use average bbox width as scale reference
        avg_width = (det_a.bbox.width + det_b.bbox.width) / 2
        if avg_width <= 0:
            return 0.0

        # Approximate: scale pixel distance using known width ratio
        scale = self.config.known_width_m / avg_width
        return round(pixel_dist * scale, 2)

    def pixel_area(self, detection: Detection) -> float:
        """Calculate bounding box area in pixels."""
        return detection.bbox.area

    def estimated_real_area(self, detection: Detection) -> float:
        """
        Estimate real-world bounding box area in square meters.

        Uses the distance estimate to scale pixel area.
        """
        distance = self.estimate_distance(detection)
        if distance <= 0:
            return 0.0

        # Scale factor: real_size / pixel_size at estimated distance
        scale = (distance * self.config.known_width_m) / (
            self.config.focal_length_px * detection.bbox.width
        ) if detection.bbox.width > 0 else 0.0

        pixel_area = detection.bbox.area
        return round(pixel_area * scale * scale, 4)

    def measure_all(self, detections: list[Detection]) -> list[dict]:
        """
        Run all measurements on a list of detections.

        Returns:
            List of measurement dicts per detection
        """
        results = []

        for det in detections:
            results.append({
                "track_id": det.track_id,
                "class_name": det.class_name,
                "distance_m": self.estimate_distance(det),
                "pixel_area": self.pixel_area(det),
                "bbox_width_px": det.bbox.width,
                "bbox_height_px": det.bbox.height,
            })

        return results

    def get_stats(self) -> dict:
        """Get measurement config info."""
        return {
            "focal_length_px": self.config.focal_length_px,
            "known_width_m": self.config.known_width_m,
            "reference_class": self.config.reference_class,
        }
