"""
VisionX — Master Processing Pipeline
========================================
The heart of the edge engine. Wires together:
    Camera → Preprocessor → Detector → Tracker → Counter → Overlay → Display

Run directly:
    python -m edge.core.pipeline
"""

from __future__ import annotations

import time
from typing import Optional

import cv2
import numpy as np
from loguru import logger

from edge.config.edge_config import EdgeConfig
from edge.core.camera import Camera
from edge.core.preprocessor import Preprocessor, PreprocessConfig, PreprocessStep
from edge.core.threading_engine import ThreadingEngine
from edge.core.tracker import Tracker
from edge.modules.counting import Counter
from edge.modules.detection import Detector
from edge.modules.tracking import TrackingModule
from edge.roi.roi_engine import ROIEngine
from shared.models import Detection, FrameResult, ROIZone
from visualization.overlay import Overlay
from decision.engine import DecisionEngine
from events.event_engine import EventEngine


class Pipeline:
    """
    Master processing pipeline for the VisionX edge engine.
    
    Orchestrates all components in the correct order:
        1. Camera capture
        2. Preprocessing (CLAHE, denoise, resize)
        3. Detection (YOLO)
        4. Tracking (IoU + velocity)
        5. Counting (global + per-zone)
        6. Visualization overlay
        7. Output display
    """

    def __init__(self, config: Optional[EdgeConfig] = None):
        self.config = config or EdgeConfig()

        # --- Core Components ---
        self._camera: Optional[Camera] = None
        self._preprocessor: Optional[Preprocessor] = None
        self._detector: Optional[Detector] = None
        self._tracking: Optional[TrackingModule] = None
        self._counter: Optional[Counter] = None
        self._roi_engine: Optional[ROIEngine] = None
        self._overlay: Optional[Overlay] = None
        self._decision_engine: Optional[DecisionEngine] = None
        self._event_engine: Optional[EventEngine] = None
        self._threading_engine: Optional[ThreadingEngine] = None

        # --- State ---
        self._is_running = False
        self._fps: float = 0.0
        self._frame_count: int = 0
        self._last_result: Optional[FrameResult] = None

    def initialize(self) -> None:
        """Initialize all pipeline components based on config."""
        logger.info("Initializing VisionX pipeline...")

        # Camera
        self._camera = Camera(
            source=self.config.camera_source,
            width=self.config.camera_width,
            height=self.config.camera_height,
            fps=self.config.camera_fps,
            name="pipeline_cam",
        )

        # Preprocessor
        preprocess_steps = [PreprocessStep.RESIZE]
        target_size = (self.config.input_size, self.config.input_size)
        self._preprocessor = Preprocessor(
            PreprocessConfig(target_size=target_size, steps=preprocess_steps)
        )

        # Detector
        if self.config.detection_enabled:
            self._detector = Detector(
                model_path=self.config.model_path,
                confidence=self.config.confidence_threshold,
                nms_threshold=self.config.nms_threshold,
                target_classes=self.config.target_classes,
            )

        # Tracking
        if self.config.tracking_enabled:
            self._tracking = TrackingModule(
                max_age=self.config.tracker_max_age,
                min_hits=self.config.tracker_min_hits,
                iou_threshold=self.config.tracker_iou_threshold,
            )

        # Counting
        if self.config.counting_enabled:
            self._counter = Counter()

        # ROI Engine
        if self.config.roi_enabled:
            self._roi_engine = ROIEngine()

        # Overlay
        self._overlay = Overlay(
            show_boxes=self.config.show_bounding_boxes,
            show_labels=self.config.show_labels,
            show_track_ids=self.config.show_track_ids,
            show_confidence=self.config.show_confidence,
            show_fps=self.config.show_fps,
        )

        # Decision + Event engines
        self._decision_engine = DecisionEngine()
        self._event_engine = EventEngine()

        logger.info("Pipeline initialized successfully")

    def _process_frame(self, frame: np.ndarray, frame_id: int) -> dict:
        """
        Process a single frame through the full AI pipeline.
        
        Args:
            frame: Raw BGR frame from camera
            frame_id: Sequential frame identifier
            
        Returns:
            Processing result dict
        """
        start = time.perf_counter()

        # 1. Preprocess
        processed = self._preprocessor.process(frame) if self._preprocessor else frame

        # 2. Detect
        detections: list[Detection] = []
        if self._detector:
            detections = self._detector.detect(processed)

            # Scale bounding boxes back to original frame size if resized
            if self._preprocessor and self.config.input_size:
                h_orig, w_orig = frame.shape[:2]
                h_proc, w_proc = processed.shape[:2]
                if (w_orig, h_orig) != (w_proc, h_proc):
                    detections = self._scale_detections(
                        detections, w_proc, h_proc, w_orig, h_orig
                    )

        # 3. Track
        if self._tracking and detections:
            detections = self._tracking.update(detections)

        # 4. ROI Filter
        roi_zones = []
        if self._roi_engine:
            roi_zones = self._roi_engine.get_enabled_zones()
            if roi_zones:
                detections = self._roi_engine.filter_detections(detections)

        # 5. Count
        count_summary = {}
        if self._counter:
            count_summary = self._counter.count(detections, roi_zones or None)

        # Build result
        elapsed_ms = (time.perf_counter() - start) * 1000
        self._frame_count += 1

        result = FrameResult(
            frame_id=frame_id,
            detections=detections,
            fps=self._camera.actual_fps if self._camera else 0.0,
            processing_time_ms=round(elapsed_ms, 1),
            metadata={"counts": count_summary},
        )

        self._last_result = result

        # 6. Evaluate decision rules
        if self._decision_engine:
            triggered_rules = self._decision_engine.evaluate(result)
            if triggered_rules and self._event_engine:
                events = self._event_engine.process_rule_results(
                    triggered_rules,
                    frame_context={"frame_id": frame_id, "detections": len(detections)},
                )
                if events:
                    result.metadata["events"] = [
                        {"type": e.event_type, "severity": e.severity, "message": e.message}
                        for e in events
                    ]

        return result

    def _output_frame(self, frame: np.ndarray, result: dict) -> None:
        """Render overlays and display the frame."""
        if not self.config.show_preview:
            return

        # Get ROI zones for overlay
        roi_zones = None
        if self._roi_engine:
            roi_zones = self._roi_engine.get_enabled_zones()

        # Draw overlay
        output = self._overlay.draw(frame, result, roi_zones=roi_zones)

        # Display
        cv2.imshow("VisionX", output)

        # Check if window was closed via X button
        if cv2.getWindowProperty("VisionX", cv2.WND_PROP_VISIBLE) < 1:
            self._is_running = False
            return

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            self._is_running = False
        elif key == ord("r"):
            # Reset tracking
            if self._tracking:
                self._tracking.reset()
            if self._counter:
                self._counter.reset()
            logger.info("Pipeline state reset by user")

    @staticmethod
    def _scale_detections(
        detections: list[Detection],
        from_w: int,
        from_h: int,
        to_w: int,
        to_h: int,
    ) -> list[Detection]:
        """Scale detection bounding boxes from processed size to original size."""
        sx = to_w / from_w
        sy = to_h / from_h

        scaled = []
        for det in detections:
            new_det = det.model_copy()
            new_det.bbox.x1 *= sx
            new_det.bbox.y1 *= sy
            new_det.bbox.x2 *= sx
            new_det.bbox.y2 *= sy
            scaled.append(new_det)

        return scaled

    def run(self) -> None:
        """
        Run the pipeline (blocking).
        
        This is the main entry point. Starts camera capture,
        runs the processing loop, and handles graceful shutdown.
        """
        self.initialize()

        # Open camera
        if not self._camera.open():
            logger.error("Failed to open camera. Exiting.")
            return

        self._is_running = True
        logger.info(
            f"VisionX pipeline running | Mode: {self.config.mode} | "
            f"Source: {self.config.camera_source} | "
            f"Press 'q' to quit, 'r' to reset tracking"
        )

        if self.config.use_threading:
            self._run_threaded()
        else:
            self._run_sequential()

    def _run_threaded(self) -> None:
        """Run pipeline with multi-threaded capture/process/output."""
        self._camera.start_threaded()

        self._threading_engine = ThreadingEngine(
            capture_fn=self._camera.read,
            process_fn=self._process_frame,
            output_fn=self._output_frame,
            skip_frames=self.config.skip_frames,
        )
        self._threading_engine.start()

        # Keep main thread alive until stopped
        try:
            while self._is_running and self._threading_engine.is_running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received")
        finally:
            self.stop()

    def _run_sequential(self) -> None:
        """Run pipeline in a single thread (simpler, for debugging)."""
        try:
            while self._is_running:
                success, frame, frame_id = self._camera.read()

                if not success or frame is None:
                    time.sleep(0.01)
                    continue

                # Skip frames if configured
                if self.config.skip_frames > 0:
                    if frame_id % (self.config.skip_frames + 1) != 0:
                        continue

                result = self._process_frame(frame, frame_id)
                self._output_frame(frame, result)

        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received")
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop all components and release resources."""
        logger.info("Stopping VisionX pipeline...")
        self._is_running = False

        if self._threading_engine:
            self._threading_engine.stop()

        if self._camera:
            self._camera.stop()

        cv2.destroyAllWindows()
        logger.info(f"Pipeline stopped (total frames processed: {self._frame_count})")

    def get_stats(self) -> dict:
        """Get complete pipeline statistics."""
        stats = {
            "is_running": self._is_running,
            "frame_count": self._frame_count,
            "config": self.config.to_dict(),
        }

        if self._camera:
            stats["camera"] = self._camera.get_stats()
        if self._detector:
            stats["detector"] = self._detector.get_stats()
        if self._tracking:
            stats["tracking"] = self._tracking.get_stats()
        if self._counter:
            stats["counter"] = self._counter.get_summary()
        if self._roi_engine:
            stats["roi"] = self._roi_engine.get_stats()
        if self._threading_engine:
            stats["threading"] = self._threading_engine.get_stats()

        return stats


# ============================================
# Direct execution entry point
# ============================================
def main():
    """Run the VisionX pipeline with default settings."""
    import sys

    logger.info("=== VisionX Edge Engine ===")

    # Parse simple CLI args
    config = EdgeConfig()

    # Check for --source arg
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--source" and i < len(sys.argv) - 1:
            config.camera_source = sys.argv[i + 1]
        elif arg == "--mode" and i < len(sys.argv) - 1:
            config.apply_performance_mode(sys.argv[i + 1])
        elif arg == "--no-preview":
            config.show_preview = False
        elif arg == "--no-threading":
            config.use_threading = False

    pipeline = Pipeline(config)
    pipeline.run()


if __name__ == "__main__":
    main()
