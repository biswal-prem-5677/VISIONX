"""
VisionX — Event Engine Tests
================================
Unit tests for the event engine and actions.
"""

import json
import time


from decision.rules import RuleResult, RuleSeverity
from events.event_engine import EventAction, EventEngine
from events.actions.log_action import LogAction
from shared.models import Event


# ============================================
# Mock Action for Testing
# ============================================

class MockAction(EventAction):
    """A mock action that records calls."""

    action_type = "mock"

    def __init__(self, should_succeed: bool = True):
        self.call_count = 0
        self.last_event = None
        self._succeed = should_succeed

    def execute(self, event: Event, context: dict) -> bool:
        self.call_count += 1
        self.last_event = event
        return self._succeed


class MockFailAction(EventAction):
    """An action that always raises an exception."""

    action_type = "mock_fail"

    def execute(self, event: Event, context: dict) -> bool:
        raise RuntimeError("Action exploded!")


class MockFlakyAction(EventAction):
    """An action that fails a fixed number of times, then succeeds."""

    action_type = "mock_flaky"

    def __init__(self, fail_times: int = 1):
        self.call_count = 0
        self._fail_times = fail_times

    def execute(self, event: Event, context: dict) -> bool:
        self.call_count += 1
        if self.call_count <= self._fail_times:
            raise RuntimeError("Transient failure")
        return True


def _wait_for(predicate, timeout: float = 5.0, interval: float = 0.01) -> bool:
    """
    Poll ``predicate`` until it is true or ``timeout`` elapses.

    Actions dispatch on a background thread pool with retry backoff, so a fixed
    sleep is inherently racy — this waits for the outcome instead of guessing.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return predicate()


# ============================================
# Tests: EventEngine
# ============================================

class TestEventEngine:
    """Test the event engine dispatch."""

    def test_register_action(self):
        engine = EventEngine()
        action = MockAction()
        engine.register_action("test_action", action)

        stats = engine.get_stats()
        assert "test_action" in stats["registered_actions"]

    def test_unregister_action(self):
        engine = EventEngine()
        engine.register_action("test", MockAction())
        engine.unregister_action("test")

        stats = engine.get_stats()
        assert "test" not in stats["registered_actions"]

    def test_process_triggered_rule(self):
        """Triggered rule should dispatch its actions."""
        engine = EventEngine()
        mock = MockAction()
        engine.register_action("mock_action", mock)

        results = [
            RuleResult(
                rule_id="test_rule",
                rule_name="Test Rule",
                triggered=True,
                severity=RuleSeverity.WARNING,
                actions=["mock_action"],
                matched_conditions=["person_count > 5"],
            )
        ]

        events = engine.process_rule_results(results)
        time.sleep(0.05)  # Wait for ThreadPool dispatch

        assert len(events) == 1
        assert mock.call_count == 1
        assert events[0].event_type == "alert"

    def test_non_triggered_rule_ignored(self):
        """Non-triggered rules should not create events."""
        engine = EventEngine()
        mock = MockAction()
        engine.register_action("mock_action", mock)

        results = [
            RuleResult(
                rule_id="test_rule",
                rule_name="Test Rule",
                triggered=False,
                severity=RuleSeverity.INFO,
                actions=["mock_action"],
            )
        ]

        events = engine.process_rule_results(results)

        assert len(events) == 0
        assert mock.call_count == 0

    def test_multiple_actions(self):
        """Multiple actions should all be dispatched."""
        engine = EventEngine()
        mock1 = MockAction()
        mock2 = MockAction()
        engine.register_action("action1", mock1)
        engine.register_action("action2", mock2)

        results = [
            RuleResult(
                rule_id="test",
                rule_name="Test",
                triggered=True,
                severity=RuleSeverity.CRITICAL,
                actions=["action1", "action2"],
            )
        ]

        engine.process_rule_results(results)
        time.sleep(0.05)  # Wait for ThreadPool dispatch

        assert mock1.call_count == 1
        assert mock2.call_count == 1

    def test_action_error_handled(self):
        """Action exceptions should be retried, then dead-lettered — never dropped."""
        # Tiny delay so the three attempts complete inside the test.
        engine = EventEngine(max_attempts=3, retry_base_delay=0.001)
        engine.register_action("bad_action", MockFailAction())

        results = [
            RuleResult(
                rule_id="test",
                rule_name="Test",
                triggered=True,
                severity=RuleSeverity.WARNING,
                actions=["bad_action"],
            )
        ]

        # Should not raise
        events = engine.process_rule_results(results)
        assert len(events) == 1

        assert _wait_for(
            lambda: engine.get_stats()["action_stats"]["bad_action"]["failure"] == 1
        ), "action never recorded a permanent failure"

        stats = engine.get_stats()
        # 3 attempts = 2 retries + 1 permanent failure, dead-lettered once.
        assert stats["action_stats"]["bad_action"]["retried"] == 2
        assert stats["action_stats"]["bad_action"]["success"] == 0
        assert stats["action_stats"]["bad_action"]["dead_lettered"] == 1
        assert stats["dead_letters"] == 1

        # The failed dispatch is retained for inspection, not discarded.
        dead = engine.get_dead_letters()
        assert len(dead) == 1
        assert dead[0]["action_name"] == "bad_action"
        assert dead[0]["attempts"] == 3
        assert "Action exploded!" in dead[0]["last_error"]

    def test_transient_failure_recovered_by_retry(self):
        """An action that fails once then succeeds must be recorded as a success."""
        engine = EventEngine(max_attempts=3, retry_base_delay=0.001)
        engine.register_action("flaky", MockFlakyAction(fail_times=1))

        engine.process_rule_results([
            RuleResult(
                rule_id="test",
                rule_name="Test",
                triggered=True,
                severity=RuleSeverity.WARNING,
                actions=["flaky"],
            )
        ])

        assert _wait_for(
            lambda: engine.get_stats()["action_stats"]["flaky"]["success"] == 1
        ), "retry never succeeded"

        stats = engine.get_stats()
        assert stats["action_stats"]["flaky"]["retried"] == 1
        assert stats["action_stats"]["flaky"]["failure"] == 0
        assert stats["dead_letters"] == 0

    def test_unregistered_action_is_dead_lettered(self):
        """A dispatch to an unknown action must not look like a delivered alert."""
        engine = EventEngine()

        events = engine.process_rule_results([
            RuleResult(
                rule_id="test",
                rule_name="Test",
                triggered=True,
                severity=RuleSeverity.INFO,
                actions=["nonexistent_action"],
            )
        ])
        assert len(events) == 1

        assert _wait_for(lambda: engine.get_stats()["dead_letters"] == 1), (
            "unregistered action was silently dropped"
        )
        stats = engine.get_stats()
        assert stats["action_stats"]["nonexistent_action"]["failure"] == 1
        assert stats["action_stats"]["nonexistent_action"]["success"] == 0

    def test_severity_mapping(self):
        """Different severities should map to correct event types."""
        engine = EventEngine()
        mock = MockAction()
        engine.register_action("mock", mock)

        for severity, expected_type in [
            (RuleSeverity.INFO, "info"),
            (RuleSeverity.WARNING, "alert"),
            (RuleSeverity.CRITICAL, "critical_alert"),
            (RuleSeverity.EMERGENCY, "emergency"),
        ]:
            results = [
                RuleResult(
                    rule_id=f"test_{severity.value}",
                    rule_name="Test",
                    triggered=True,
                    severity=severity,
                    actions=["mock"],
                )
            ]
            events = engine.process_rule_results(results)
            assert events[0].event_type == expected_type

    def test_event_history(self):
        """Events should be stored in history."""
        engine = EventEngine()
        engine.register_action("mock", MockAction())

        for i in range(5):
            engine.process_rule_results([
                RuleResult(
                    rule_id=f"rule_{i}",
                    rule_name=f"Rule {i}",
                    triggered=True,
                    severity=RuleSeverity.INFO,
                    actions=["mock"],
                )
            ])

        recent = engine.get_recent_events(limit=3)
        assert len(recent) == 3
        assert engine.get_event_count() == 5

    def test_clear_history(self):
        engine = EventEngine()
        engine.register_action("mock", MockAction())
        engine.process_rule_results([
            RuleResult(
                rule_id="test",
                rule_name="Test",
                triggered=True,
                severity=RuleSeverity.INFO,
                actions=["mock"],
            )
        ])

        engine.clear_history()
        assert len(engine.get_recent_events()) == 0


# ============================================
# Tests: LogAction
# ============================================

class TestLogAction:
    """Test the log file action."""

    def test_log_creates_file(self, tmp_path):
        """Log action should create a JSONL file."""
        log_action = LogAction(log_dir=str(tmp_path))

        event = Event(
            event_type="alert",
            source="test_rule",
            message="Test alert",
            severity="warning",
        )

        result = log_action.execute(event, {})
        assert result is True

        # Check file was created
        log_files = list(tmp_path.glob("events_*.jsonl"))
        assert len(log_files) == 1

        # Check content
        content = log_files[0].read_text()
        entry = json.loads(content.strip())
        assert entry["message"] == "Test alert"
        assert entry["severity"] == "warning"
