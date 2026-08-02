"""
VisionX — Recording Action
==============================
Save video clip when event triggers.

Contract note
-------------
Previously ``async def execute(self, event: dict, ...)`` on a non-``EventAction``
class, so the engine never awaited it: no clip was ever written and the engine
recorded a success. Now synchronous and conforming.

**This action does not yet capture video.** It requires a frame ring buffer,
which the pipeline does not expose. Rather than write a placeholder ``.mp4``
containing text — which looks like a working clip to everything downstream — it
now fails loudly unless a buffer is supplied in the context.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from loguru import logger

from events.event_engine import EventAction
from shared.models import Event


class RecordingAction(EventAction):
    """
    Save a video clip when an event triggers.

    Expects ``context["frame_buffer"]`` to be an object exposing
    ``write_clip(path, duration_seconds) -> bool``. Without one, the action
    fails — the clip *is* the evidence, and a fake clip is worse than none.
    """

    action_type = "recording"

    def __init__(self, output_dir: str = "./recordings", duration: int = 10):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.duration = duration

        logger.info(
            f"RecordingAction initialized (dir={output_dir}, duration={duration}s)"
        )

    def execute(self, event: Event, context: dict[str, Any]) -> bool:
        """Write a clip for this event. Returns True only if a clip was written."""
        camera = str(context.get("camera") or event.source_id or "unknown")
        # Sanitise: camera identifiers reach us from device config and must not
        # be able to traverse out of the output directory.
        safe_camera = "".join(c for c in camera if c.isalnum() or c in "-_")[:64] or "unknown"

        filename = f"{safe_camera}_{int(time.time())}.mp4"
        filepath = self.output_dir / filename

        buffer = context.get("frame_buffer")
        if buffer is None or not hasattr(buffer, "write_clip"):
            logger.error(
                f"Recording NOT written for {safe_camera} — no frame_buffer in "
                f"context. Clip capture requires a ring buffer exposing "
                f"write_clip(path, duration_seconds)."
            )
            return False

        try:
            written = bool(buffer.write_clip(str(filepath), self.duration))
            if written:
                logger.info(f"Recording written: {filepath} ({self.duration}s)")
            else:
                logger.error(f"Frame buffer declined to write clip: {filepath}")
            return written
        except Exception as e:
            logger.error(f"Recording failed: {e}")
            return False
