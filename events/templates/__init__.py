"""VisionX — Event Templates Package."""

from events.templates.event_templates import (
    EventTemplate,
    get_event_template,
    list_event_templates,
    EVENT_TEMPLATES,
)

__all__ = ["EventTemplate", "get_event_template", "list_event_templates", "EVENT_TEMPLATES"]
