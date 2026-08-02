"""
VisionX — Event Engine (Jarvis Core)
=======================================
Central event dispatch system. Receives triggered rules from the
Decision Engine and executes the corresponding actions.

Event Types: Alert · Notification · Automation trigger · API call · Hardware signal

Delivery guarantees
-------------------
This is an *alerting* product, so the failure modes that matter are the silent
ones. Two were fixed here:

1. **Silent no-op.** ``_dispatch_action`` called ``action.execute(...)`` and
   treated any truthy return as success. Several bundled actions declared
   ``async def execute``, so the call returned an un-awaited **coroutine** —
   truthy. The action never ran, and the engine recorded a success.
   ``register_action`` now rejects non-conforming handlers at registration time,
   and dispatch rejects coroutine returns at runtime.

2. **Dropped alerts.** A failing action was logged and discarded. Failures are
   now retried with exponential backoff and, if still failing, moved to an
   inspectable dead-letter queue instead of vanishing.

The DLQ is in-memory and therefore still lost on restart. That is a known,
tracked gap (EXECUTION_TRACKER.md DEF-011): the durable outbox belongs in
Postgres. This change makes the failure *visible*, which is the prerequisite.
"""

from __future__ import annotations

import inspect
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict, deque
from typing import Any, Optional

from loguru import logger

from decision.rules import RuleResult, RuleSeverity
from shared.models import Event


class EventAction:
    """
    Base class for event actions.
    All action implementations should inherit from this.

    ``execute`` must be a **synchronous** method: the engine runs actions in a
    thread pool, and an ``async def`` override would return an un-awaited
    coroutine that never runs.
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


class DeadLetter:
    """An action that exhausted its retries, retained for inspection/replay."""

    __slots__ = ("action_name", "event", "context", "attempts", "last_error", "failed_at")

    def __init__(
        self,
        action_name: str,
        event: Event,
        context: dict[str, Any],
        attempts: int,
        last_error: str,
    ):
        self.action_name = action_name
        self.event = event
        self.context = context
        self.attempts = attempts
        self.last_error = last_error
        self.failed_at = time.time()

    def as_dict(self) -> dict[str, Any]:
        return {
            "action_name": self.action_name,
            "event_id": str(self.event.id),
            "event_type": self.event.event_type,
            "severity": self.event.severity,
            "message": self.event.message,
            "attempts": self.attempts,
            "last_error": self.last_error,
            "failed_at": self.failed_at,
        }

    def __repr__(self) -> str:
        return f"<DeadLetter {self.action_name} attempts={self.attempts}>"


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

    def __init__(
        self,
        max_workers: int = 8,
        max_attempts: int = 3,
        retry_base_delay: float = 0.5,
        max_dead_letters: int = 500,
    ):
        self._actions: dict[str, EventAction] = {}
        self._event_history: list[Event] = []
        self._max_history: int = 1000
        self._action_stats: dict[str, dict[str, int]] = defaultdict(
            lambda: {"success": 0, "failure": 0, "retried": 0, "dead_lettered": 0}
        )
        self._total_events: int = 0
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="vx-action"
        )

        self.max_attempts = max(1, max_attempts)
        self.retry_base_delay = retry_base_delay

        # Bounded so a sustained outage cannot exhaust memory (EXECUTION_RULES R8).
        self._dead_letters: deque[DeadLetter] = deque(maxlen=max_dead_letters)
        self._lock = threading.Lock()

        logger.info(
            f"Event Engine (Jarvis Core) initialized "
            f"(workers={max_workers}, max_attempts={self.max_attempts})"
        )

    def register_action(self, action_name: str, action: EventAction) -> None:
        """
        Register an action handler.

        Raises:
            TypeError: if the handler does not satisfy the ``EventAction``
                contract. Rejecting at registration turns a silent runtime
                no-op into an immediate, obvious startup failure.
        """
        execute = getattr(action, "execute", None)

        if not callable(execute):
            raise TypeError(
                f"Action '{action_name}' ({type(action).__name__}) has no callable "
                f"execute(); it cannot be dispatched."
            )

        if inspect.iscoroutinefunction(execute):
            raise TypeError(
                f"Action '{action_name}' ({type(action).__name__}) declares "
                f"'async def execute'. The event engine dispatches actions on a "
                f"thread pool and would never await it — the action would silently "
                f"never run. Make execute() synchronous."
            )

        if not isinstance(action, EventAction):
            logger.warning(
                f"Action '{action_name}' ({type(action).__name__}) does not subclass "
                f"EventAction. Accepting it because it is structurally compatible, "
                f"but subclassing is expected."
            )

        self._actions[action_name] = action
        logger.info(
            f"Action registered: {action_name} "
            f"({getattr(action, 'action_type', type(action).__name__)})"
        )

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
        """
        Execute a single action with bounded retries (runs in background thread).

        On permanent failure the attempt is dead-lettered rather than dropped.
        """
        action = self._actions.get(action_name)

        if action is None:
            logger.warning(f"Action not registered: {action_name}")
            self._record(action_name, "failure")
            self._dead_letter(
                action_name, event, context, 0, "action not registered"
            )
            return

        last_error = "returned False"

        for attempt in range(1, self.max_attempts + 1):
            try:
                success = action.execute(event, context)

                if inspect.isawaitable(success):
                    # Defence in depth: register_action rejects async handlers,
                    # but a handler could return an awaitable from a sync method.
                    # Close it so Python does not warn about a dangling coroutine.
                    getattr(success, "close", lambda: None)()
                    raise TypeError(
                        f"{type(action).__name__}.execute() returned an awaitable. "
                        f"The action did not run. Make it fully synchronous."
                    )

                if success:
                    self._record(action_name, "success")
                    logger.debug(
                        f"Action executed: {action_name} (attempt {attempt})"
                    )
                    return

                last_error = "returned False"

            except Exception as e:  # noqa: BLE001 - retried, then dead-lettered
                last_error = f"{type(e).__name__}: {e}"

            if attempt < self.max_attempts:
                self._record(action_name, "retried")
                delay = self.retry_base_delay * (2 ** (attempt - 1))
                logger.warning(
                    f"Action failed: {action_name} (attempt {attempt}/"
                    f"{self.max_attempts}) — {last_error}. Retrying in {delay:.1f}s"
                )
                time.sleep(delay)

        self._record(action_name, "failure")
        logger.error(
            f"Action permanently failed after {self.max_attempts} attempts: "
            f"{action_name} — {last_error}. Dead-lettered."
        )
        self._dead_letter(
            action_name, event, context, self.max_attempts, last_error
        )

    def _record(self, action_name: str, outcome: str) -> None:
        """Increment a stat counter under the lock (called from worker threads)."""
        with self._lock:
            self._action_stats[action_name][outcome] += 1

    def _dead_letter(
        self,
        action_name: str,
        event: Event,
        context: dict[str, Any],
        attempts: int,
        error: str,
    ) -> None:
        """Retain a permanently failed dispatch for inspection and replay."""
        with self._lock:
            self._dead_letters.append(
                DeadLetter(action_name, event, context, attempts, error)
            )
            self._action_stats[action_name]["dead_lettered"] += 1

    def get_dead_letters(self, limit: int = 100) -> list[dict[str, Any]]:
        """Return recent dead-lettered dispatches, newest last."""
        with self._lock:
            items = list(self._dead_letters)[-limit:]
        return [dl.as_dict() for dl in items]

    def replay_dead_letters(self) -> int:
        """
        Re-dispatch everything in the dead-letter queue. Returns the count
        resubmitted. Used after fixing whatever caused the outage.
        """
        with self._lock:
            pending = list(self._dead_letters)
            self._dead_letters.clear()

        for dl in pending:
            self._dispatch_async(dl.action_name, dl.event, dl.context)

        if pending:
            logger.info(f"Replayed {len(pending)} dead-lettered actions")
        return len(pending)

    def shutdown(self, wait: bool = True) -> None:
        """
        Stop accepting new dispatches and drain in-flight ones.

        Without this, interpreter exit could kill worker threads mid-action —
        an alert that was half-sent and never recorded either way.
        """
        self._executor.shutdown(wait=wait)
        logger.info("Event Engine shut down")

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
        with self._lock:
            action_stats = {
                name: dict(stats) for name, stats in self._action_stats.items()
            }
            dead_letters = len(self._dead_letters)

        return {
            "total_events": self._total_events,
            "history_size": len(self._event_history),
            "registered_actions": list(self._actions.keys()),
            "action_stats": action_stats,
            "dead_letters": dead_letters,
        }
