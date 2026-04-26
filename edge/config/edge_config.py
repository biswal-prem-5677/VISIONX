"""
VisionX — Edge Configuration
==============================
Performance modes and runtime configuration for the edge engine.
Supports Lite (mobile), Balanced (laptop), and Max (GPU server) modes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from shared.constants import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    DEFAULT_MODEL,
    DEFAULT_NMS_THRESHOLD,
    PERFORMANCE_CONFIGS,
    PerformanceMode,
    TRACKER_IOU_THRESHOLD,
    TRACKER_MAX_AGE,
    TRACKER_MIN_HITS,
)


@dataclass
class EdgeConfig:
    """
    Runtime configuration for the edge processing engine.
    Controls what runs, how fast, and with what quality.
    """

    # --- Performance ---
    mode: str = PerformanceMode.BALANCED
    input_size: int = 640
    skip_frames: int = 0
    precision: str = "FP16"
    batch_size: int = 1
    max_fps: int = 30

    # --- Detection ---
    model_path: str = DEFAULT_MODEL
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
    nms_threshold: float = DEFAULT_NMS_THRESHOLD
    target_classes: Optional[list[str]] = None  # None = detect all

    # --- Tracking ---
    tracking_enabled: bool = True
    tracker_max_age: int = TRACKER_MAX_AGE
    tracker_min_hits: int = TRACKER_MIN_HITS
    tracker_iou_threshold: float = TRACKER_IOU_THRESHOLD

    # --- Modules (enable/disable) ---
    detection_enabled: bool = True
    counting_enabled: bool = True
    measurement_enabled: bool = False
    roi_enabled: bool = False

    # --- Camera ---
    camera_source: str = "0"          # Webcam index, RTSP URL, or file path
    camera_width: int = 1280
    camera_height: int = 720
    camera_fps: int = 30

    # --- Visualization ---
    show_preview: bool = True
    show_bounding_boxes: bool = True
    show_labels: bool = True
    show_track_ids: bool = True
    show_fps: bool = True
    show_confidence: bool = True

    # --- Threading ---
    use_threading: bool = True
    capture_queue_size: int = 30
    result_queue_size: int = 30

    def apply_performance_mode(self, mode: str) -> None:
        """Apply a performance preset (lite/balanced/max)."""
        if mode not in PERFORMANCE_CONFIGS:
            raise ValueError(f"Unknown performance mode: {mode}. Use: {list(PERFORMANCE_CONFIGS.keys())}")

        self.mode = mode
        config = PERFORMANCE_CONFIGS[mode]
        self.input_size = config["input_size"]
        self.skip_frames = config["skip_frames"]
        self.precision = config["precision"]
        self.batch_size = config["batch_size"]
        self.max_fps = config["max_fps"]

    @classmethod
    def lite(cls) -> EdgeConfig:
        """Create a Lite config (mobile / Raspberry Pi)."""
        cfg = cls()
        cfg.apply_performance_mode(PerformanceMode.LITE)
        return cfg

    @classmethod
    def balanced(cls) -> EdgeConfig:
        """Create a Balanced config (laptop / desktop)."""
        cfg = cls()
        cfg.apply_performance_mode(PerformanceMode.BALANCED)
        return cfg

    @classmethod
    def max_performance(cls) -> EdgeConfig:
        """Create a Max config (cloud GPU / Jetson AGX)."""
        cfg = cls()
        cfg.apply_performance_mode(PerformanceMode.MAX)
        return cfg

    def to_dict(self) -> dict:
        """Serialize config for API / debugging."""
        return {
            "mode": self.mode,
            "input_size": self.input_size,
            "skip_frames": self.skip_frames,
            "precision": self.precision,
            "batch_size": self.batch_size,
            "max_fps": self.max_fps,
            "model_path": self.model_path,
            "confidence_threshold": self.confidence_threshold,
            "detection_enabled": self.detection_enabled,
            "tracking_enabled": self.tracking_enabled,
            "counting_enabled": self.counting_enabled,
            "camera_source": self.camera_source,
        }
