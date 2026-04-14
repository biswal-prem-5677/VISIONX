"""
VisionX — Event Templates
========================================
Pre-built event rule templates for common use cases.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EventTemplate:
    """Pre-built event rule template."""
    id: str
    name: str
    description: str
    category: str
    trigger_type: str
    trigger_config: dict = field(default_factory=dict)
    actions: list[dict] = field(default_factory=list)


# ─── Template Registry ───────────────────────────────────────────────────────

EVENT_TEMPLATES = [
    EventTemplate(
        id="crowd_alert",
        name="Crowd Alert",
        description="Alert when person count exceeds threshold",
        category="security",
        trigger_type="threshold",
        trigger_config={"metric": "person_count", "operator": ">", "value": 10},
        actions=[
            {"type": "notification", "channels": ["in_app", "push"]},
            {"type": "email", "template": "crowd_alert"},
        ],
    ),
    EventTemplate(
        id="helmet_violation",
        name="Helmet Violation",
        description="Detect when person is not wearing a helmet",
        category="safety",
        trigger_type="detection",
        trigger_config={"label": "no_helmet", "confidence_min": 0.7},
        actions=[
            {"type": "notification", "channels": ["in_app", "push"]},
            {"type": "log", "level": "warning"},
        ],
    ),
    EventTemplate(
        id="intrusion_detection",
        name="Intrusion Detection",
        description="Alert when person enters restricted zone",
        category="security",
        trigger_type="zone_entry",
        trigger_config={"zone": "restricted", "object_class": "person"},
        actions=[
            {"type": "notification", "channels": ["in_app", "push", "email", "sms"]},
            {"type": "recording", "duration": 30},
            {"type": "alarm", "level": "high"},
        ],
    ),
    EventTemplate(
        id="vehicle_speed",
        name="Speed Violation",
        description="Alert when vehicle exceeds speed limit",
        category="traffic",
        trigger_type="threshold",
        trigger_config={"metric": "speed_kmh", "operator": ">", "value": 60},
        actions=[
            {"type": "log", "level": "warning"},
            {"type": "recording", "duration": 10},
        ],
    ),
    EventTemplate(
        id="loitering_alert",
        name="Loitering Detection",
        description="Alert when person stays in area too long",
        category="security",
        trigger_type="duration",
        trigger_config={"object_class": "person", "max_duration_seconds": 300},
        actions=[
            {"type": "notification", "channels": ["in_app"]},
        ],
    ),
    EventTemplate(
        id="face_blacklist",
        name="Blacklist Face Match",
        description="Alert when blacklisted person is detected",
        category="security",
        trigger_type="face_match",
        trigger_config={"list": "blacklist", "confidence_min": 0.85},
        actions=[
            {"type": "notification", "channels": ["in_app", "push", "sms"]},
            {"type": "alarm", "level": "critical"},
            {"type": "recording", "duration": 60},
        ],
    ),
]


def get_event_template(template_id: str) -> EventTemplate | None:
    """Get event template by ID."""
    return next((t for t in EVENT_TEMPLATES if t.id == template_id), None)


def list_event_templates(category: str | None = None) -> list[EventTemplate]:
    """List all templates, optionally filtered by category."""
    if category:
        return [t for t in EVENT_TEMPLATES if t.category == category]
    return EVENT_TEMPLATES
