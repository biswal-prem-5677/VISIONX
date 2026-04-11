"""
VisionX — Shared Detection Schemas
======================================
Pydantic models for detection pipeline data interchange.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class BBox(BaseModel):
    """Bounding box coordinates."""
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)

    @property
    def area(self) -> float:
        return self.width * self.height


class Detection(BaseModel):
    """Single object detection result."""
    class_id: int
    class_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: BBox
    track_id: Optional[int] = None
    metadata: dict = Field(default_factory=dict)


class FrameResult(BaseModel):
    """Complete result for one processed frame."""
    frame_id: int
    timestamp: float
    detections: list[Detection] = Field(default_factory=list)
    fps: float = 0.0
    latency_ms: float = 0.0
    resolution: tuple[int, int] = (0, 0)


class CameraInfo(BaseModel):
    """Camera metadata."""
    name: str
    source: str
    is_running: bool = False
    resolution: tuple[int, int] = (0, 0)
    actual_fps: float = 0.0
    total_frames: int = 0


class EventPayload(BaseModel):
    """Event trigger payload."""
    event_type: str
    severity: str = "info"  # info, warning, danger
    message: str
    camera: str = ""
    detections: list[Detection] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
