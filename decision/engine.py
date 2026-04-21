"""
VisionX — Decision Engine
============================
Evaluates rules against current detection state.
IF condition → THEN trigger actions via Event Engine.

This is the brain of VisionX — it turns raw detections into intelligent decisions.
"""

from __future__ import annotations

import time
from typing import Any, Optional

from loguru import logger

from decision.rules import (
    Rule,
    RuleCondition,
    RuleField,
    RuleOperator,
    RuleResult,
    RuleSeverity,
)
from shared.models import Detection, FrameResult


class DecisionEngine:
    """
    Rule-based decision engine.

    Evaluates a set of rules against the current frame state.
    Manages cooldowns to prevent alert flooding.
    
    Usage:
        engine = DecisionEngine()
        engine.add_rule(rule)
        results = engine.evaluate(frame_result)
    """

    def __init__(self):
        self._rules: dict[str, Rule] = {}
        self._last_triggered: dict[str, float] = {}  # rule_id -> timestamp
        self._trigger_counts: dict[str, int] = {}
        self._total_evaluations: int = 0

        logger.info("Decision Engine initialized")

    def add_rule(self, rule: Rule) -> None:
        """Register a rule for evaluation."""
        self._rules[rule.id] = rule
        logger.info(f"Rule added: {rule.name} ({rule.id})")

    def remove_rule(self, rule_id: str) -> None:
        """Remove a rule."""
        if rule_id in self._rules:
            del self._rules[rule_id]
            logger.info(f"Rule removed: {rule_id}")

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Get a rule by ID."""
        return self._rules.get(rule_id)

    def get_all_rules(self) -> list[Rule]:
        """Get all registered rules."""
        return list(self._rules.values())

    def evaluate(self, frame_result: FrameResult) -> list[RuleResult]:
        """
        Evaluate all enabled rules against the current frame result.
        Rules are evaluated in priority order (1 = highest).
        Conflicting rules in the same group: highest priority wins.
        """
        self._total_evaluations += 1
        now = time.time()
        triggered_results: list[RuleResult] = []

        # Build context from frame result
        context = self._build_context(frame_result)

        # Sort rules by priority (lower number = higher priority)
        sorted_rules = sorted(
            [r for r in self._rules.values() if r.enabled],
            key=lambda r: r.priority,
        )

        # Track which groups have already been triggered (conflict resolution)
        triggered_groups: set[str] = set()

        for rule in sorted_rules:
            # Check cooldown
            last = self._last_triggered.get(rule.id, 0)
            if now - last < rule.cooldown_seconds:
                continue

            # Mutual exclusion: skip if a higher-priority rule in same group already fired
            if rule.group and rule.group in triggered_groups:
                logger.debug(
                    f"Rule skipped (group conflict): {rule.name} "
                    f"(group '{rule.group}' already triggered by higher-priority rule)"
                )
                continue

            # Evaluate conditions
            result = self._evaluate_rule(rule, context)

            if result.triggered:
                self._last_triggered[rule.id] = now
                self._trigger_counts[rule.id] = self._trigger_counts.get(rule.id, 0) + 1
                triggered_results.append(result)

                # Mark group as triggered
                if rule.group:
                    triggered_groups.add(rule.group)

                logger.info(
                    f"Rule triggered: {rule.name} | "
                    f"Priority: {rule.priority} | "
                    f"Severity: {rule.severity} | "
                    f"Actions: {rule.actions}"
                )

        return triggered_results

    def _build_context(self, frame_result: FrameResult) -> dict[str, Any]:
        """Build evaluation context from frame result."""
        detections = frame_result.detections

        # Count by class
        class_counts: dict[str, int] = {}
        for det in detections:
            class_counts[det.class_name] = class_counts.get(det.class_name, 0) + 1

        # All detected classes
        detected_classes = list(class_counts.keys())

        # Count info from metadata
        counts = frame_result.metadata.get("counts", {})

        context = {
            "person_count": class_counts.get("person", 0),
            "object_count": len(detections),
            "class_counts": class_counts,
            "detected_classes": detected_classes,
            "detections": detections,
            "zone_counts": counts.get("by_zone", {}),
            "total_objects": counts.get("total_objects", 0),
            "frame_id": frame_result.frame_id,
            "fps": frame_result.fps,
        }

        return context

    def _evaluate_rule(self, rule: Rule, context: dict[str, Any]) -> RuleResult:
        """Evaluate a single rule against context."""
        matched: list[str] = []
        results: list[bool] = []

        for condition in rule.conditions:
            is_met = self._evaluate_condition(condition, context)
            results.append(is_met)
            if is_met:
                matched.append(
                    f"{condition.field.value} {condition.operator.value} {condition.value}"
                )

        # Apply logic (AND / OR)
        if rule.logic == "AND":
            triggered = all(results) if results else False
        else:  # OR
            triggered = any(results) if results else False

        return RuleResult(
            rule_id=rule.id,
            rule_name=rule.name,
            triggered=triggered,
            severity=rule.severity,
            actions=rule.actions if triggered else [],
            matched_conditions=matched,
            context={
                "person_count": context.get("person_count", 0),
                "object_count": context.get("object_count", 0),
            },
        )

    def _evaluate_condition(
        self, condition: RuleCondition, context: dict[str, Any]
    ) -> bool:
        """Evaluate a single condition."""
        field = condition.field
        op = condition.operator
        target = condition.value

        # Get the actual value from context
        actual = self._get_field_value(field, condition, context)

        if actual is None:
            return False

        # Compare
        return self._compare(actual, op, target)

    def _get_field_value(
        self,
        field: RuleField,
        condition: RuleCondition,
        context: dict[str, Any],
    ) -> Any:
        """Extract the value of a field from context."""
        if field == RuleField.PERSON_COUNT:
            return context.get("person_count", 0)

        elif field == RuleField.OBJECT_COUNT:
            return context.get("object_count", 0)

        elif field == RuleField.CLASS_COUNT:
            if condition.class_filter:
                return context.get("class_counts", {}).get(condition.class_filter, 0)
            return context.get("object_count", 0)

        elif field == RuleField.ZONE_COUNT:
            zone_counts = context.get("zone_counts", {})
            if condition.zone_filter and condition.zone_filter in zone_counts:
                zone = zone_counts[condition.zone_filter]
                if condition.class_filter:
                    return zone.get(condition.class_filter, 0)
                return sum(zone.values()) if isinstance(zone, dict) else 0
            return 0

        elif field == RuleField.DETECTION_CLASS:
            return context.get("detected_classes", [])

        elif field == RuleField.CONFIDENCE:
            detections = context.get("detections", [])
            if detections:
                return max(d.confidence for d in detections)
            return 0.0

        elif field == RuleField.ZONE_OCCUPANCY:
            zone_counts = context.get("zone_counts", {})
            if condition.zone_filter and condition.zone_filter in zone_counts:
                zone = zone_counts[condition.zone_filter]
                return sum(zone.values()) if isinstance(zone, dict) else 0
            return 0

        return None

    @staticmethod
    def _compare(actual: Any, op: RuleOperator, target: Any) -> bool:
        """Perform comparison operation."""
        try:
            if op == RuleOperator.GT:
                return float(actual) > float(target)
            elif op == RuleOperator.GTE:
                return float(actual) >= float(target)
            elif op == RuleOperator.LT:
                return float(actual) < float(target)
            elif op == RuleOperator.LTE:
                return float(actual) <= float(target)
            elif op == RuleOperator.EQ:
                return actual == target
            elif op == RuleOperator.NEQ:
                return actual != target
            elif op == RuleOperator.CONTAINS:
                if isinstance(actual, list):
                    return target in actual
                return str(target) in str(actual)
            elif op == RuleOperator.IN_ZONE:
                return bool(actual)
            elif op == RuleOperator.NOT_IN_ZONE:
                return not bool(actual)
        except (TypeError, ValueError):
            return False

        return False

    def reset_cooldowns(self) -> None:
        """Reset all rule cooldowns."""
        self._last_triggered.clear()
        logger.info("All rule cooldowns reset")

    def get_stats(self) -> dict:
        """Get decision engine statistics."""
        return {
            "total_rules": len(self._rules),
            "enabled_rules": sum(1 for r in self._rules.values() if r.enabled),
            "total_evaluations": self._total_evaluations,
            "trigger_counts": dict(self._trigger_counts),
            "rules": [
                {
                    "id": r.id,
                    "name": r.name,
                    "enabled": r.enabled,
                    "severity": r.severity.value,
                    "triggers": self._trigger_counts.get(r.id, 0),
                }
                for r in self._rules.values()
            ],
        }
