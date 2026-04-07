"""
VisionX — Shared Data Models
==============================
Pydantic models used across edge, cloud, and platform layers.
These are the universal data contracts of the system.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ============================================
# Detection Models
# ============================================

class BoundingBox(BaseModel):
    """A single detected object's bounding box."""
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
    """A single detection result from the AI engine."""
    class_id: int
    class_name: str
    confidence: float
    bbox: BoundingBox
    track_id: Optional[int] = None  # Assigned by tracker
    metadata: dict[str, Any] = Field(default_factory=dict)


class FrameResult(BaseModel):
    """Complete result for a single processed frame."""
    frame_id: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    detections: list[Detection] = Field(default_factory=list)
    fps: float = 0.0
    processing_time_ms: float = 0.0
    source_id: str = "default"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def detection_count(self) -> int:
        return len(self.detections)

    def get_by_class(self, class_name: str) -> list[Detection]:
        return [d for d in self.detections if d.class_name == class_name]

    def get_person_count(self) -> int:
        return len(self.get_by_class("person"))


# ============================================
# Track Models
# ============================================

class TrackState(str, Enum):
    TENTATIVE = "tentative"
    CONFIRMED = "confirmed"
    DELETED = "deleted"


class Track(BaseModel):
    """A tracked object across multiple frames."""
    track_id: int
    class_name: str
    bbox: BoundingBox
    state: TrackState = TrackState.TENTATIVE
    age: int = 0            # Frames since creation
    hits: int = 0           # Total matched detections
    time_since_update: int = 0  # Frames since last match
    velocity: tuple[float, float] = (0.0, 0.0)


# ============================================
# Event Models
# ============================================

class EventSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class EventAction(BaseModel):
    """An action to execute when an event triggers."""
    action_type: str    # "email", "webhook", "iot", "notification", etc.
    config: dict[str, Any] = Field(default_factory=dict)


class Rule(BaseModel):
    """A decision rule: IF condition THEN actions."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    condition: dict[str, Any]   # e.g., {"field": "person_count", "op": ">", "value": 5}
    actions: list[EventAction]
    enabled: bool = True
    cooldown_seconds: int = 60  # Prevent repeated triggers


class Event(BaseModel):
    """A triggered event from the decision engine."""
    id: UUID = Field(default_factory=uuid4)
    event_type: str
    severity: str = "info"
    title: str = ""
    message: str = ""
    source: str = ""
    rule_id: Optional[UUID] = None
    source_id: str = "default"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    image_url: Optional[str] = None
    actions_executed: list[str] = Field(default_factory=list)


# ============================================
# Device Models
# ============================================

class DeviceStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class Device(BaseModel):
    """A registered camera/device."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    source_type: str    # "webcam", "rtsp", "ip_camera", "video_file"
    source_uri: str     # 0, "rtsp://...", "http://...", "video.mp4"
    status: DeviceStatus = DeviceStatus.INACTIVE
    last_seen: Optional[datetime] = None
    config: dict[str, Any] = Field(default_factory=dict)


# ============================================
# ROI Models
# ============================================

class ROIZone(BaseModel):
    """A Region of Interest zone defined by polygon points."""
    id: str
    name: str
    points: list[tuple[int, int]]   # [(x1,y1), (x2,y2), ...]
    enabled: bool = True
    color: tuple[int, int, int] = (0, 255, 255)  # BGR


# ============================================
# Crash Report Models
# ============================================

class CrashReport(BaseModel):
    """A crash report from a client."""
    crash_id: UUID = Field(default_factory=uuid4)
    user_id: Optional[UUID] = None
    session_id: Optional[UUID] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error_message: str
    stack_trace: str = ""
    breadcrumbs: list[str] = Field(default_factory=list)
    device_info: dict[str, Any] = Field(default_factory=dict)
    app_state: dict[str, Any] = Field(default_factory=dict)
    severity: EventSeverity = EventSeverity.ERROR


# ============================================
# Usage Tracking Models
# ============================================

class UsageEvent(BaseModel):
    """A feature usage tracking event."""
    user_id: Optional[UUID] = None
    feature: str
    action: str
    device_type: str = "web"
    ip: Optional[str] = None
    session_id: Optional[UUID] = None
    duration_ms: Optional[int] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
