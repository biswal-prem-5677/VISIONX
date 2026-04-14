"""
VisionX — Notification Templates
========================================
Pre-built notification templates for common events.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NotificationTemplate:
    """Template for a notification."""
    id: str
    title: str
    body: str
    type: str = "info"  # info, success, warning, danger
    channels: list[str] = None  # push, email, in_app, sms

    def __post_init__(self):
        if self.channels is None:
            self.channels = ["in_app"]

    def render(self, **kwargs) -> tuple[str, str]:
        """Render template with variables."""
        title = self.title.format(**kwargs)
        body = self.body.format(**kwargs)
        return title, body


# ─── Template Registry ───────────────────────────────────────────────────────

TEMPLATES = {
    # Detection events
    "person_detected": NotificationTemplate(
        id="person_detected",
        title="Person Detected — {camera}",
        body="{count} person(s) detected at {location}. Confidence: {confidence}%",
        type="info",
        channels=["in_app"],
    ),
    "crowd_alert": NotificationTemplate(
        id="crowd_alert",
        title="⚠️ Crowd Alert — {camera}",
        body="Crowd count ({count}) exceeded threshold ({threshold}) at {location}.",
        type="warning",
        channels=["in_app", "push", "email"],
    ),
    "intrusion_alert": NotificationTemplate(
        id="intrusion_alert",
        title="🔴 Intrusion Detected — {camera}",
        body="Unauthorized person detected in restricted zone: {zone}.",
        type="danger",
        channels=["in_app", "push", "email", "sms"],
    ),
    "face_match": NotificationTemplate(
        id="face_match",
        title="Face Match — {camera}",
        body="Known person '{name}' identified at {location}.",
        type="success",
        channels=["in_app", "push"],
    ),

    # System events
    "camera_offline": NotificationTemplate(
        id="camera_offline",
        title="📹 Camera Offline — {camera}",
        body="Camera '{camera}' has been offline for {duration}.",
        type="warning",
        channels=["in_app", "email"],
    ),
    "system_health_warning": NotificationTemplate(
        id="system_health_warning",
        title="⚠️ System Health Warning",
        body="CPU: {cpu}%, Memory: {memory}%. System may be degraded.",
        type="warning",
        channels=["in_app", "push"],
    ),
    "quota_exceeded": NotificationTemplate(
        id="quota_exceeded",
        title="📊 Quota Exceeded",
        body="Your {resource} quota ({limit}) has been exceeded. Upgrade to continue.",
        type="danger",
        channels=["in_app", "email"],
    ),

    # Governance events
    "action_blocked": NotificationTemplate(
        id="action_blocked",
        title="🛡️ Action Blocked by Governance",
        body="Action '{action}' was blocked: {reason}. Review required.",
        type="warning",
        channels=["in_app", "push"],
    ),
    "low_confidence": NotificationTemplate(
        id="low_confidence",
        title="⚠️ Low Confidence Detection",
        body="Detection on {camera} has confidence {confidence}%. Human review required.",
        type="warning",
        channels=["in_app"],
    ),
}


def get_template(template_id: str) -> NotificationTemplate | None:
    """Get a notification template by ID."""
    return TEMPLATES.get(template_id)
