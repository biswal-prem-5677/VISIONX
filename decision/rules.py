"""
VisionX — Rule Definitions
==============================
Data models and presets for the decision engine rule system.
Rules define conditions that trigger events when evaluated to True.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class RuleOperator(str, Enum):
    """Comparison operators for rule conditions."""
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    EQ = "=="
    NEQ = "!="
    CONTAINS = "contains"
    IN_ZONE = "in_zone"
    NOT_IN_ZONE = "not_in_zone"


class RuleField(str, Enum):
    """Fields that can be evaluated in rules."""
    PERSON_COUNT = "person_count"
    OBJECT_COUNT = "object_count"
    CLASS_COUNT = "class_count"
    ZONE_COUNT = "zone_count"
    TRACK_DIRECTION = "track_direction"
    DETECTION_CLASS = "detection_class"
    CONFIDENCE = "confidence"
    LOITERING_DURATION = "loitering_duration"
    SPEED = "speed"
    ZONE_OCCUPANCY = "zone_occupancy"


class RuleCondition(BaseModel):
    """A single condition to evaluate."""
    field: RuleField
    operator: RuleOperator
    value: Any
    class_filter: Optional[str] = None  # e.g., "person", "car"
    zone_filter: Optional[str] = None   # e.g., zone_id


class RuleSeverity(str, Enum):
    """Severity level of a triggered rule."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class Rule(BaseModel):
    """
    A complete rule definition.

    Example:
        Rule(
            id="crowd_alert",
            name="Crowd Alert",
            conditions=[
                RuleCondition(field="person_count", operator=">", value=10)
            ],
            actions=["send_email", "log_event"],
            severity="critical",
            cooldown_seconds=60,
        )
    """
    id: str
    name: str
    description: str = ""
    enabled: bool = True
    conditions: list[RuleCondition]
    logic: str = "AND"  # "AND" = all conditions, "OR" = any condition
    actions: list[str] = Field(default_factory=list)
    severity: RuleSeverity = RuleSeverity.WARNING
    cooldown_seconds: int = 30  # Minimum seconds between triggers
    metadata: dict[str, Any] = Field(default_factory=dict)


class RuleResult(BaseModel):
    """Result of evaluating a rule."""
    rule_id: str
    rule_name: str
    triggered: bool
    severity: RuleSeverity
    actions: list[str]
    matched_conditions: list[str] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)


# ============================================
# Pre-built Rule Templates
# ============================================

RULE_TEMPLATES: dict[str, Rule] = {
    "crowd_alert": Rule(
        id="crowd_alert",
        name="Crowd Alert",
        description="Alert when too many people detected",
        conditions=[
            RuleCondition(
                field=RuleField.PERSON_COUNT,
                operator=RuleOperator.GT,
                value=10,
            )
        ],
        actions=["send_email", "log_event"],
        severity=RuleSeverity.CRITICAL,
        cooldown_seconds=60,
    ),
    "intrusion_alert": Rule(
        id="intrusion_alert",
        name="Intrusion Alert",
        description="Alert when person enters restricted zone",
        conditions=[
            RuleCondition(
                field=RuleField.ZONE_COUNT,
                operator=RuleOperator.GT,
                value=0,
                class_filter="person",
                zone_filter="restricted",
            )
        ],
        actions=["send_email", "trigger_webhook", "log_event"],
        severity=RuleSeverity.EMERGENCY,
        cooldown_seconds=30,
    ),
    "no_helmet": Rule(
        id="no_helmet",
        name="Safety Violation - No Helmet",
        description="Alert when person detected without helmet",
        conditions=[
            RuleCondition(
                field=RuleField.DETECTION_CLASS,
                operator=RuleOperator.CONTAINS,
                value="no_helmet",
            )
        ],
        actions=["send_email", "log_event"],
        severity=RuleSeverity.WARNING,
        cooldown_seconds=30,
    ),
    "object_missing": Rule(
        id="object_missing",
        name="Object Missing From Zone",
        description="Alert when expected object is no longer detected in zone",
        conditions=[
            RuleCondition(
                field=RuleField.ZONE_COUNT,
                operator=RuleOperator.EQ,
                value=0,
                zone_filter="monitored",
            )
        ],
        actions=["log_event", "trigger_webhook"],
        severity=RuleSeverity.WARNING,
        cooldown_seconds=120,
    ),
}
