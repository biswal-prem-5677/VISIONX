"""
VisionX — Camera Input Engine
===============================
Universal camera input supporting webcam, RTSP, IP cameras, and video files.
Thread-safe frame capture with automatic reconnection.
"""

from __future__ import annotations

import time
from threading import Event, Thread
from typing import Optional

import cv2
import numpy as np
from loguru import logger


class Camera:
    """
    Universal camera input engine.
    
    Supports:
        - USB Webcam: Camera("0") or Camera(0)
        - RTSP Stream: Camera("rtsp://user:pass@ip:554/stream")
        - IP Camera: Camera("http://ip:port/video")
        - Video File: Camera("path/to/video.mp4")
    """

    def __init__(
        self,
        source: str | int = 0,
        width: int = 1280,
        height: int = 720,
        fps: int = 30,
        name: str = "camera_0",
    ):
        self.source = self._parse_source(source)
        self.width = width
        self.height = height
        self.fps = fps
        self.name = name

        self._cap: Optional[cv2.VideoCapture] = None
        self._is_running = False
        self._frame: Optional[np.ndarray] = None
        self._frame_id: int = 0
        self._stop_event = Event()
        self._thread: Optional[Thread] = None
        self._last_frame_time: float = 0.0

        # Stats
        self._actual_fps: float = 0.0
        self._total_frames: int = 0
        self._dropped_frames: int = 0

    @staticmethod
    def _parse_source(source: str | int) -> str | int:
        """Parse source string — convert numeric strings to int for webcam."""
        if isinstance(source, int):
            return source
        if source.isdigit():
            return int(source)
        return source

    def open(self) -> bool:
        """Open the camera connection."""
        logger.info(f"[{self.name}] Opening camera source: {self.source}")

        self._cap = cv2.VideoCapture(self.source)

        if not self._cap.isOpened():
            logger.error(f"[{self.name}] Failed to open camera: {self.source}")
            return False

        # Set properties (only works for webcams, not all RTSP)
        if isinstance(self.source, int):
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self._cap.set(cv2.CAP_PROP_FPS, self.fps)

        # Read actual properties
        actual_w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = self._cap.get(cv2.CAP_PROP_FPS)

        logger.info(
            f"[{self.name}] Camera opened: {actual_w}x{actual_h} @ {actual_fps:.1f} FPS"
        )

        self._is_running = True
        return True

    def start_threaded(self) -> None:
        """Start capturing frames in a background thread."""
        if not self._is_running:
            if not self.open():
                raise RuntimeError(f"Cannot start camera: {self.source}")

        self._stop_event.clear()
        self._thread = Thread(target=self._capture_loop, daemon=True, name=f"cam_{self.name}")
        self._thread.start()
        logger.info(f"[{self.name}] Threaded capture started")

    def _capture_loop(self) -> None:
        """Background thread: continuously read frames."""
        while not self._stop_event.is_set():
            if self._cap is None or not self._cap.isOpened():
                logger.warning(f"[{self.name}] Camera disconnected, attempting reconnect...")
                time.sleep(2.0)
                self.open()
                continue

            ret, frame = self._cap.read()

            if not ret:
                self._dropped_frames += 1
                if self._is_video_file():
                    logger.info(f"[{self.name}] Video file ended")
                    self._stop_event.set()
                    break
                logger.warning(f"[{self.name}] Frame read failed, retrying...")
                time.sleep(0.1)
                continue

            now = time.time()
            if self._last_frame_time > 0:
                dt = now - self._last_frame_time
                self._actual_fps = 1.0 / dt if dt > 0 else 0.0
            self._last_frame_time = now

            self._frame = frame
            self._frame_id += 1
            self._total_frames += 1

    def read(self) -> tuple[bool, Optional[np.ndarray], int]:
        """
        Read the latest frame.
        
        Returns:
            (success, frame, frame_id)
        """
        if self._thread is not None:
            # Threaded mode: return latest frame
            if self._frame is not None:
                return True, self._frame.copy(), self._frame_id
            return False, None, self._frame_id

        # Non-threaded mode: read directly
        if self._cap is None or not self._cap.isOpened():
            return False, None, self._frame_id

        ret, frame = self._cap.read()
        if ret:
            self._frame_id += 1
            self._total_frames += 1
            self._frame = frame
        return ret, frame, self._frame_id

    def _is_video_file(self) -> bool:
        """Check if source is a video file (not a live stream)."""
        if isinstance(self.source, int):
            return False
        return any(self.source.lower().endswith(ext) for ext in [".mp4", ".avi", ".mkv", ".mov", ".wmv"])

    @property
    def is_running(self) -> bool:
        return self._is_running and not self._stop_event.is_set()

    @property
    def actual_fps(self) -> float:
        return self._actual_fps

    @property
    def frame_count(self) -> int:
        return self._total_frames

    @property
    def resolution(self) -> tuple[int, int]:
        if self._cap and self._cap.isOpened():
            w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            return (w, h)
        return (0, 0)

    def get_stats(self) -> dict:
        """Get camera statistics."""
        return {
            "name": self.name,
            "source": str(self.source),
            "is_running": self.is_running,
            "resolution": self.resolution,
            "actual_fps": round(self._actual_fps, 1),
            "total_frames": self._total_frames,
            "dropped_frames": self._dropped_frames,
        }

    def stop(self) -> None:
        """Stop the camera and release resources."""
        logger.info(f"[{self.name}] Stopping camera...")
        self._stop_event.set()
        self._is_running = False

        if self._thread is not None:
            self._thread.join(timeout=3.0)
            self._thread = None

        if self._cap is not None:
            self._cap.release()
            self._cap = None

        logger.info(f"[{self.name}] Camera stopped (total frames: {self._total_frames})")

    def __del__(self):
        self.stop()

    def __repr__(self) -> str:
        return f"Camera(source={self.source}, name={self.name}, running={self.is_running})"
