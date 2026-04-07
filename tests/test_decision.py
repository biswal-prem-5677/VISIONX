"""
VisionX — Decision Engine Tests
===================================
Unit tests for the rule-based decision engine.
"""

import time

import pytest

from decision.engine import DecisionEngine
from decision.rules import (
    Rule,
    RuleCondition,
    RuleField,
    RuleOperator,
    RuleSeverity,
)
from shared.models import BoundingBox, Detection, FrameResult


# ============================================
# Helpers
# ============================================

def make_detections(person_count: int = 0, car_count: int = 0) -> list[Detection]:
    """Create mock detections."""
    detections = []
    for i in range(person_count):
        detections.append(
            Detection(
                class_id=0,
                class_name="person",
                confidence=0.9,
                bbox=BoundingBox(x1=100 + i * 50, y1=100, x2=150 + i * 50, y2=300),
                track_id=i + 1,
            )
        )
    for i in range(car_count):
        detections.append(
            Detection(
                class_id=2,
                class_name="car",
                confidence=0.85,
                bbox=BoundingBox(x1=400 + i * 80, y1=200, x2=500 + i * 80, y2=350),
                track_id=100 + i,
            )
        )
    return detections


def make_frame_result(person_count: int = 0, car_count: int = 0) -> FrameResult:
    """Create a mock FrameResult."""
    return FrameResult(
        frame_id=1,
        detections=make_detections(person_count, car_count),
        fps=30.0,
    )


# ============================================
# Tests
# ============================================

class TestRuleDefinition:
    """Test rule creation and structure."""

    def test_basic_rule(self):
        rule = Rule(
            id="test_rule",
            name="Test Rule",
            conditions=[
                RuleCondition(
                    field=RuleField.PERSON_COUNT,
                    operator=RuleOperator.GT,
                    value=5,
                )
            ],
            actions=["log_event"],
        )
        assert rule.id == "test_rule"
        assert rule.enabled is True
        assert len(rule.conditions) == 1
        assert rule.severity == RuleSeverity.WARNING

    def test_rule_with_severity(self):
        rule = Rule(
            id="critical_rule",
            name="Critical",
            conditions=[
                RuleCondition(
                    field=RuleField.PERSON_COUNT,
                    operator=RuleOperator.GT,
                    value=10,
                )
            ],
            severity=RuleSeverity.CRITICAL,
            actions=["send_email"],
        )
        assert rule.severity == RuleSeverity.CRITICAL


class TestDecisionEngine:
    """Test the decision engine evaluation."""

    def test_add_rule(self):
        engine = DecisionEngine()
        rule = Rule(
            id="test",
            name="Test",
            conditions=[
                RuleCondition(
                    field=RuleField.PERSON_COUNT,
                    operator=RuleOperator.GT,
                    value=3,
                )
            ],
            actions=["log_event"],
        )
        engine.add_rule(rule)
        assert len(engine.get_all_rules()) == 1

    def test_remove_rule(self):
        engine = DecisionEngine()
        rule = Rule(
            id="test",
            name="Test",
            conditions=[
                RuleCondition(
                    field=RuleField.PERSON_COUNT,
                    operator=RuleOperator.GT,
                    value=3,
                )
            ],
            actions=["log_event"],
        )
        engine.add_rule(rule)
        engine.remove_rule("test")
        assert len(engine.get_all_rules()) == 0

    def test_trigger_person_count_gt(self):
        """Rule should trigger when person_count > threshold."""
        engine = DecisionEngine()
        engine.add_rule(
            Rule(
                id="crowd",
                name="Crowd Alert",
                conditions=[
                    RuleCondition(
                        field=RuleField.PERSON_COUNT,
                        operator=RuleOperator.GT,
                        value=3,
                    )
                ],
                actions=["send_email", "log_event"],
                cooldown_seconds=0,  # No cooldown for test
            )
        )

        # 5 people → should trigger
        frame = make_frame_result(person_count=5)
        results = engine.evaluate(frame)

        assert len(results) == 1
        assert results[0].triggered is True
        assert results[0].rule_id == "crowd"
        assert "send_email" in results[0].actions

    def test_no_trigger_below_threshold(self):
        """Rule should NOT trigger when below threshold."""
        engine = DecisionEngine()
        engine.add_rule(
            Rule(
                id="crowd",
                name="Crowd Alert",
                conditions=[
                    RuleCondition(
                        field=RuleField.PERSON_COUNT,
                        operator=RuleOperator.GT,
                        value=10,
                    )
                ],
                actions=["log_event"],
                cooldown_seconds=0,
            )
        )

        # 3 people → should NOT trigger
        frame = make_frame_result(person_count=3)
        results = engine.evaluate(frame)

        assert len(results) == 0

    def test_disabled_rule_not_triggered(self):
        """Disabled rules should not be evaluated."""
        engine = DecisionEngine()
        engine.add_rule(
            Rule(
                id="disabled",
                name="Disabled Rule",
                enabled=False,
                conditions=[
                    RuleCondition(
                        field=RuleField.PERSON_COUNT,
                        operator=RuleOperator.GT,
                        value=0,
                    )
                ],
                actions=["log_event"],
                cooldown_seconds=0,
            )
        )

        frame = make_frame_result(person_count=5)
        results = engine.evaluate(frame)

        assert len(results) == 0

    def test_cooldown_prevents_retrigger(self):
        """Cooldown should prevent repeated triggers."""
        engine = DecisionEngine()
        engine.add_rule(
            Rule(
                id="crowd",
                name="Crowd Alert",
                conditions=[
                    RuleCondition(
                        field=RuleField.PERSON_COUNT,
                        operator=RuleOperator.GT,
                        value=3,
                    )
                ],
                actions=["log_event"],
                cooldown_seconds=60,  # 60 second cooldown
            )
        )

        frame = make_frame_result(person_count=5)

        # First eval → trigger
        results1 = engine.evaluate(frame)
        assert len(results1) == 1

        # Second eval (within cooldown) → no trigger
        results2 = engine.evaluate(frame)
        assert len(results2) == 0

    def test_and_logic(self):
        """AND logic: all conditions must be met."""
        engine = DecisionEngine()
        engine.add_rule(
            Rule(
                id="both",
                name="Both Conditions",
                logic="AND",
                conditions=[
                    RuleCondition(
                        field=RuleField.PERSON_COUNT,
                        operator=RuleOperator.GT,
                        value=2,
                    ),
                    RuleCondition(
                        field=RuleField.OBJECT_COUNT,
                        operator=RuleOperator.GT,
                        value=5,
                    ),
                ],
                actions=["log_event"],
                cooldown_seconds=0,
            )
        )

        # 3 people + 2 cars = 5 total → OBJECT_COUNT not > 5
        frame = make_frame_result(person_count=3, car_count=2)
        results = engine.evaluate(frame)
        assert len(results) == 0

        # 4 people + 3 cars = 7 total → both conditions met
        frame2 = make_frame_result(person_count=4, car_count=3)
        results2 = engine.evaluate(frame2)
        assert len(results2) == 1

    def test_or_logic(self):
        """OR logic: any condition can trigger."""
        engine = DecisionEngine()
        engine.add_rule(
            Rule(
                id="either",
                name="Either Condition",
                logic="OR",
                conditions=[
                    RuleCondition(
                        field=RuleField.PERSON_COUNT,
                        operator=RuleOperator.GT,
                        value=100,
                    ),
                    RuleCondition(
                        field=RuleField.OBJECT_COUNT,
                        operator=RuleOperator.GT,
                        value=2,
                    ),
                ],
                actions=["log_event"],
                cooldown_seconds=0,
            )
        )

        # 3 people → person not > 100, but object > 2
        frame = make_frame_result(person_count=3)
        results = engine.evaluate(frame)
        assert len(results) == 1

    def test_contains_operator(self):
        """CONTAINS should check if class is in detected classes."""
        engine = DecisionEngine()
        engine.add_rule(
            Rule(
                id="has_car",
                name="Car Detected",
                conditions=[
                    RuleCondition(
                        field=RuleField.DETECTION_CLASS,
                        operator=RuleOperator.CONTAINS,
                        value="car",
                    )
                ],
                actions=["log_event"],
                cooldown_seconds=0,
            )
        )

        # No cars
        frame1 = make_frame_result(person_count=3)
        assert len(engine.evaluate(frame1)) == 0

        # Has cars
        frame2 = make_frame_result(person_count=1, car_count=2)
        assert len(engine.evaluate(frame2)) == 1

    def test_stats(self):
        """Stats should track evaluations and triggers."""
        engine = DecisionEngine()
        engine.add_rule(
            Rule(
                id="test",
                name="Test",
                conditions=[
                    RuleCondition(
                        field=RuleField.PERSON_COUNT,
                        operator=RuleOperator.GT,
                        value=0,
                    )
                ],
                actions=["log_event"],
                cooldown_seconds=0,
            )
        )

        engine.evaluate(make_frame_result(person_count=2))
        engine.evaluate(make_frame_result(person_count=0))

        stats = engine.get_stats()
        assert stats["total_rules"] == 1
        assert stats["total_evaluations"] == 2
