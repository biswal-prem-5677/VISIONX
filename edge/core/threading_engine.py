"""
VisionX — Threading Engine
=============================
Multi-threaded frame processing with separate capture, processing, and output threads.
Uses queues for thread-safe communication.
"""

from __future__ import annotations

import time
from queue import Empty, Full, Queue
from threading import Event, Thread
from typing import Callable, Optional

import numpy as np
from loguru import logger

from shared.constants import MAX_FRAME_QUEUE_SIZE, MAX_RESULT_QUEUE_SIZE


class ThreadingEngine:
    """
    Multi-threaded processing engine with 3 threads:
        1. Capture Thread — reads frames from camera
        2. Processing Thread — runs AI inference
        3. Output Thread — handles results (display, API, etc.)

    Threads communicate via thread-safe queues.
    """

    def __init__(
        self,
        capture_fn: Callable[[], tuple[bool, Optional[np.ndarray], int]],
        process_fn: Callable[[np.ndarray, int], dict],
        output_fn: Callable[[np.ndarray, dict], None],
        frame_queue_size: int = MAX_FRAME_QUEUE_SIZE,
        result_queue_size: int = MAX_RESULT_QUEUE_SIZE,
        skip_frames: int = 0,
    ):
        self.capture_fn = capture_fn
        self.process_fn = process_fn
        self.output_fn = output_fn
        self.skip_frames = skip_frames

        self._frame_queue: Queue = Queue(maxsize=frame_queue_size)
        self._result_queue: Queue = Queue(maxsize=result_queue_size)
        self._stop_event = Event()

        self._capture_thread: Optional[Thread] = None
        self._process_thread: Optional[Thread] = None
        self._output_thread: Optional[Thread] = None

        # Stats
        self._frames_captured = 0
        self._frames_processed = 0
        self._frames_skipped = 0
        self._frames_dropped = 0

    def start(self) -> None:
        """Start all three processing threads."""
        self._stop_event.clear()

        self._capture_thread = Thread(
            target=self._capture_loop,
            daemon=True,
            name="vx_capture",
        )
        self._process_thread = Thread(
            target=self._process_loop,
            daemon=True,
            name="vx_process",
        )
        self._output_thread = Thread(
            target=self._output_loop,
            daemon=True,
            name="vx_output",
        )

        self._capture_thread.start()
        self._process_thread.start()
        self._output_thread.start()

        logger.info("Threading engine started (capture + process + output)")

    def _capture_loop(self) -> None:
        """Continuously capture frames and push to frame queue."""
        frame_counter = 0

        while not self._stop_event.is_set():
            success, frame, frame_id = self.capture_fn()

            if not success or frame is None:
                time.sleep(0.01)
                continue

            frame_counter += 1
            self._frames_captured += 1

            # Frame skipping
            if self.skip_frames > 0 and frame_counter % (self.skip_frames + 1) != 0:
                self._frames_skipped += 1
                continue

            # Non-blocking put — drop oldest frame if queue is full
            try:
                self._frame_queue.put_nowait((frame, frame_id))
            except Full:
                try:
                    self._frame_queue.get_nowait()  # Drop oldest
                    self._frames_dropped += 1
                except Empty:
                    pass
                self._frame_queue.put_nowait((frame, frame_id))

    def _process_loop(self) -> None:
        """Take frames from queue, process them, push results."""
        while not self._stop_event.is_set():
            try:
                frame, frame_id = self._frame_queue.get(timeout=0.1)
            except Empty:
                continue

            try:
                result = self.process_fn(frame, frame_id)
                self._frames_processed += 1

                try:
                    self._result_queue.put_nowait((frame, result))
                except Full:
                    try:
                        self._result_queue.get_nowait()
                    except Empty:
                        pass
                    self._result_queue.put_nowait((frame, result))

            except Exception as e:
                logger.error(f"Processing error on frame {frame_id}: {e}")

    def _output_loop(self) -> None:
        """Take results from queue and pass to output handler."""
        while not self._stop_event.is_set():
            try:
                frame, result = self._result_queue.get(timeout=0.1)
            except Empty:
                continue

            try:
                self.output_fn(frame, result)
            except Exception as e:
                logger.error(f"Output error: {e}")

    def stop(self) -> None:
        """Stop all threads gracefully."""
        logger.info("Stopping threading engine...")
        self._stop_event.set()

        for t in [self._capture_thread, self._process_thread, self._output_thread]:
            if t is not None:
                t.join(timeout=3.0)

        logger.info(
            f"Threading engine stopped. "
            f"Captured: {self._frames_captured}, "
            f"Processed: {self._frames_processed}, "
            f"Skipped: {self._frames_skipped}, "
            f"Dropped: {self._frames_dropped}"
        )

    @property
    def is_running(self) -> bool:
        return not self._stop_event.is_set()

    def get_stats(self) -> dict:
        return {
            "is_running": self.is_running,
            "frames_captured": self._frames_captured,
            "frames_processed": self._frames_processed,
            "frames_skipped": self._frames_skipped,
            "frames_dropped": self._frames_dropped,
            "frame_queue_size": self._frame_queue.qsize(),
            "result_queue_size": self._result_queue.qsize(),
        }
