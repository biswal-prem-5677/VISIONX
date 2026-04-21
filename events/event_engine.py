"""
VisionX — Event Engine (Jarvis Core)
=======================================
Central event dispatch system. Receives triggered rules from the
Decision Engine and executes the corresponding actions.

Event Types: Alert · Notification · Automation trigger · API call · Hardware signal
"""

from __future__ import annotations

import asyncio
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from typing import Any, Optional

from loguru import logger

from decision.rules import RuleResult, RuleSeverity
from shared.models import Event


class EventAction:
    """
    Base class for event actions.
    All action implementations should inherit from this.
    """

    action_type: str = "base"

    def execute(self, event: Event, context: dict[str, Any]) -> bool:
        """
        Execute the action (synchronous).

        Args:
            event: The event that triggered this action
            context: Additional context (detection data, frame info, etc.)

        Returns:
            True if action was executed successfully
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} ({self.action_type})>"


class EventEngine:
    """
    Central event dispatch engine (Jarvis Core).

    Receives rule results from the Decision Engine and dispatches
    the appropriate actions (email, webhook, log, IoT, etc.).
    Actions are dispatched asynchronously to avoid blocking the pipeline.

    Usage:
        engine = EventEngine()
        engine.register_action("send_email", EmailAction(...))
        engine.register_action("log_event", LogAction(...))
        engine.process_rule_results(triggered_rules)
    """

    def __init__(self):
        self._actions: dict[str, EventAction] = {}
        self._event_history: list[Event] = []
        self._max_history: int = 1000
        self._action_stats: dict[str, dict[str, int]] = defaultdict(
            lambda: {"success": 0, "failure": 0}
        )
        self._total_events: int = 0
        self._dispatch_queue: list[tuple[str, Event, dict]] = []
        self._executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="vx-action")

        logger.info("Event Engine (Jarvis Core) initialized")

    def register_action(self, action_name: str, action: EventAction) -> None:
        """Register an action handler."""
        self._actions[action_name] = action
        logger.info(f"Action registered: {action_name} ({action.action_type})")

    def unregister_action(self, action_name: str) -> None:
        """Remove an action handler."""
        if action_name in self._actions:
            del self._actions[action_name]
            logger.info(f"Action unregistered: {action_name}")

    def process_rule_results(
        self,
        results: list[RuleResult],
        frame_context: Optional[dict[str, Any]] = None,
    ) -> list[Event]:
        """
        Process triggered rule results and dispatch actions.
        Actions are dispatched in a background thread to avoid blocking.
        """
        events: list[Event] = []
        context = frame_context or {}

        for result in results:
            if not result.triggered:
                continue

            # Create event
            event = Event(
                event_type=self._severity_to_event_type(result.severity),
                source=result.rule_id,
                message=f"Rule triggered: {result.rule_name}",
                severity=result.severity.value,
                metadata={
                    "rule_id": result.rule_id,
                    "rule_name": result.rule_name,
                    "matched_conditions": result.matched_conditions,
                    "context": result.context,
                },
            )

            # Store in history
            self._event_history.append(event)
            self._total_events += 1

            # Trim history if needed
            if len(self._event_history) > self._max_history:
                self._event_history = self._event_history[-self._max_history:]

            # Dispatch actions asynchronously (non-blocking)
            for action_name in result.actions:
                self._dispatch_async(action_name, event, context)

            events.append(event)

        return events

    def _dispatch_async(
        self,
        action_name: str,
        event: Event,
        context: dict[str, Any],
    ) -> None:
        """Submit action to thread pool (bounded, non-blocking)."""
        self._executor.submit(self._dispatch_action, action_name, event, context)

    def _dispatch_action(
        self,
        action_name: str,
        event: Event,
        context: dict[str, Any],
    ) -> None:
        """Execute a single action (runs in background thread)."""
        action = self._actions.get(action_name)

        if action is None:
            logger.warning(f"Action not registered: {action_name}")
            return

        try:
            success = action.execute(event, context)
            if success:
                self._action_stats[action_name]["success"] += 1
                logger.debug(f"Action executed: {action_name}")
            else:
                self._action_stats[action_name]["failure"] += 1
                logger.warning(f"Action failed: {action_name}")
        except Exception as e:
            self._action_stats[action_name]["failure"] += 1
            logger.error(f"Action error ({action_name}): {e}")

    @staticmethod
    def _severity_to_event_type(severity: RuleSeverity) -> str:
        """Map rule severity to event type."""
        mapping = {
            RuleSeverity.INFO: "info",
            RuleSeverity.WARNING: "alert",
            RuleSeverity.CRITICAL: "critical_alert",
            RuleSeverity.EMERGENCY: "emergency",
        }
        return mapping.get(severity, "alert")

    def get_recent_events(
        self,
        limit: int = 50,
        severity: Optional[str] = None,
    ) -> list[Event]:
        """Get recent events, optionally filtered by severity."""
        events = self._event_history

        if severity:
            events = [e for e in events if e.severity == severity]

        return events[-limit:]

    def get_event_count(self) -> int:
        """Get total event count."""
        return self._total_events

    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()
        logger.info("Event history cleared")

    def get_stats(self) -> dict:
        """Get event engine statistics."""
        return {
            "total_events": self._total_events,
            "history_size": len(self._event_history),
            "registered_actions": list(self._actions.keys()),
            "action_stats": {
                name: dict(stats) for name, stats in self._action_stats.items()
            },
        }
