"""
VisionX — Multi-Camera Pipeline
========================================
Multiplexes N camera sources through the detection pipeline.
Each camera gets its own processing thread with shared model inference.
"""

from __future__ import annotations

import asyncio
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

import numpy as np
from loguru import logger


class CameraStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    DISCONNECTED = "disconnected"
    INITIALIZING = "initializing"


@dataclass
class CameraSource:
    """A single camera source within the multi-pipeline."""
    camera_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = "Camera"
    source: str = "0"  # 0=webcam, rtsp://..., http://..., file path
    source_type: str = "usb"  # usb, rtsp, http, file
    resolution: tuple[int, int] = (640, 480)
    target_fps: int = 30
    status: CameraStatus = CameraStatus.INITIALIZING
    roi_zones: list[dict] = field(default_factory=list)
    enabled_modules: list[str] = field(default_factory=lambda: ["detection", "tracking"])
    priority: int = 5  # 1=highest processing priority

    # Runtime stats
    actual_fps: float = 0.0
    frame_count: int = 0
    detection_count: int = 0
    last_frame_at: Optional[datetime] = None
    error_message: str = ""
    latency_ms: float = 0.0


@dataclass
class PipelineResult:
    """Result from processing a single frame from one camera."""
    camera_id: str
    frame_number: int
    detections: list[dict] = field(default_factory=list)
    tracks: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    processing_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class MultiPipeline:
    """
    Multi-camera processing pipeline.

    Architecture:
    - Each camera has its own capture thread
    - Frame processing uses a shared thread pool
    - Model inference is batched across cameras when possible
    - Results are pushed to a shared output queue
    - Supports dynamic add/remove cameras at runtime
    """

    def __init__(
        self,
        max_cameras: int = 16,
        max_workers: int = 4,
        batch_inference: bool = True,
    ):
        self.max_cameras = max_cameras
        self.max_workers = max_workers
        self.batch_inference = batch_inference

        self._cameras: dict[str, CameraSource] = {}
        self._results_queue: list[PipelineResult] = []
        self._running = False
        self._threads: dict[str, threading.Thread] = {}
        self._lock = threading.Lock()
        self._frame_callbacks: list[Any] = []

        logger.info(
            f"MultiPipeline initialized "
            f"(max_cameras={max_cameras}, workers={max_workers}, "
            f"batch={'on' if batch_inference else 'off'})"
        )

    # ─── Camera Management ───────────────────────────────────────────────

    def add_camera(self, camera: CameraSource) -> CameraSource:
        """Add a camera to the pipeline."""
        if len(self._cameras) >= self.max_cameras:
            raise RuntimeError(f"Max cameras ({self.max_cameras}) reached")

        self._cameras[camera.camera_id] = camera
        camera.status = CameraStatus.ACTIVE

        # Start capture thread if pipeline is running
        if self._running:
            self._start_camera_thread(camera)

        logger.info(f"Camera added: {camera.name} ({camera.source})")
        return camera

    def remove_camera(self, camera_id: str) -> bool:
        """Remove a camera from the pipeline."""
        camera = self._cameras.pop(camera_id, None)
        if not camera:
            return False

        camera.status = CameraStatus.DISCONNECTED

        # Stop capture thread
        thread = self._threads.pop(camera_id, None)
        if thread and thread.is_alive():
            camera.status = CameraStatus.DISCONNECTED  # Signal thread to stop

        logger.info(f"Camera removed: {camera.name} ({camera_id[:8]})")
        return True

    def pause_camera(self, camera_id: str) -> bool:
        """Pause processing for a camera (keeps connection)."""
        camera = self._cameras.get(camera_id)
        if camera:
            camera.status = CameraStatus.PAUSED
            logger.info(f"Camera paused: {camera.name}")
            return True
        return False

    def resume_camera(self, camera_id: str) -> bool:
        """Resume a paused camera."""
        camera = self._cameras.get(camera_id)
        if camera and camera.status == CameraStatus.PAUSED:
            camera.status = CameraStatus.ACTIVE
            logger.info(f"Camera resumed: {camera.name}")
            return True
        return False

    def get_camera(self, camera_id: str) -> Optional[CameraSource]:
        """Get camera info by ID."""
        return self._cameras.get(camera_id)

    def list_cameras(self, active_only: bool = False) -> list[CameraSource]:
        """List all cameras."""
        cameras = list(self._cameras.values())
        if active_only:
            cameras = [c for c in cameras if c.status == CameraStatus.ACTIVE]
        return cameras

    # ─── Pipeline Control ────────────────────────────────────────────────

    def start(self) -> None:
        """Start processing all cameras."""
        self._running = True
        for camera in self._cameras.values():
            if camera.status != CameraStatus.DISCONNECTED:
                self._start_camera_thread(camera)
        logger.info(f"MultiPipeline started ({len(self._cameras)} cameras)")

    def stop(self) -> None:
        """Stop all pipeline processing."""
        self._running = False
        for camera in self._cameras.values():
            camera.status = CameraStatus.DISCONNECTED

        # Wait for threads
        for thread in self._threads.values():
            if thread.is_alive():
                thread.join(timeout=5.0)

        self._threads.clear()
        logger.info("MultiPipeline stopped")

    def on_frame(self, callback: Any) -> None:
        """Register a callback for processed frames."""
        self._frame_callbacks.append(callback)

    # ─── Processing ──────────────────────────────────────────────────────

    def process_frame(self, camera_id: str, frame: np.ndarray) -> PipelineResult:
        """Process a single frame from a camera."""
        camera = self._cameras.get(camera_id)
        if not camera:
            return PipelineResult(camera_id=camera_id, frame_number=0)

        start_time = time.perf_counter()
        camera.frame_count += 1

        # Run detection (in production: actual model inference)
        detections: list[dict] = []
        tracks: list[dict] = []

        processing_time = (time.perf_counter() - start_time) * 1000
        camera.latency_ms = processing_time
        camera.last_frame_at = datetime.now(timezone.utc)
        camera.detection_count += len(detections)

        result = PipelineResult(
            camera_id=camera_id,
            frame_number=camera.frame_count,
            detections=detections,
            tracks=tracks,
            processing_time_ms=round(processing_time, 2),
            metadata={
                "camera_name": camera.name,
                "resolution": camera.resolution,
                "modules": camera.enabled_modules,
            },
        )

        # Push to output queue
        with self._lock:
            self._results_queue.append(result)
            if len(self._results_queue) > 1000:
                self._results_queue = self._results_queue[-500:]

        # Fire callbacks
        for cb in self._frame_callbacks:
            try:
                cb(result)
            except Exception as e:
                logger.error(f"Frame callback error: {e}")

        return result

    def get_results(self, camera_id: Optional[str] = None, limit: int = 50) -> list[PipelineResult]:
        """Get recent results, optionally filtered by camera."""
        with self._lock:
            results = list(self._results_queue)
        if camera_id:
            results = [r for r in results if r.camera_id == camera_id]
        return results[-limit:]

    # ─── Stats ───────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Get pipeline-wide statistics."""
        cameras = list(self._cameras.values())
        return {
            "total_cameras": len(cameras),
            "active_cameras": sum(1 for c in cameras if c.status == CameraStatus.ACTIVE),
            "total_frames": sum(c.frame_count for c in cameras),
            "total_detections": sum(c.detection_count for c in cameras),
            "avg_latency_ms": round(
                sum(c.latency_ms for c in cameras) / max(len(cameras), 1), 2
            ),
            "cameras": [
                {
                    "id": c.camera_id[:8],
                    "name": c.name,
                    "status": c.status.value,
                    "fps": round(c.actual_fps, 1),
                    "frames": c.frame_count,
                    "detections": c.detection_count,
                    "latency_ms": round(c.latency_ms, 2),
                }
                for c in cameras
            ],
        }

    # ─── Internal ────────────────────────────────────────────────────────

    def _start_camera_thread(self, camera: CameraSource) -> None:
        """Start a capture thread for a camera."""
        thread = threading.Thread(
            target=self._camera_loop,
            args=(camera,),
            name=f"cam-{camera.camera_id[:8]}",
            daemon=True,
        )
        self._threads[camera.camera_id] = thread
        thread.start()

    def _camera_loop(self, camera: CameraSource) -> None:
        """Main capture loop for a single camera."""
        frame_interval = 1.0 / camera.target_fps
        fps_timer = time.perf_counter()
        fps_frames = 0

        while self._running and camera.status in (CameraStatus.ACTIVE, CameraStatus.PAUSED):
            try:
                if camera.status == CameraStatus.PAUSED:
                    time.sleep(0.5)
                    continue

                # Capture frame (in production: cv2.VideoCapture)
                frame = np.zeros((*camera.resolution[::-1], 3), dtype=np.uint8)

                self.process_frame(camera.camera_id, frame)
                fps_frames += 1

                # Calculate FPS
                elapsed = time.perf_counter() - fps_timer
                if elapsed >= 1.0:
                    camera.actual_fps = fps_frames / elapsed
                    fps_frames = 0
                    fps_timer = time.perf_counter()

                time.sleep(frame_interval)

            except Exception as e:
                camera.status = CameraStatus.ERROR
                camera.error_message = str(e)
                logger.error(f"Camera loop error ({camera.name}): {e}")
                time.sleep(1.0)
