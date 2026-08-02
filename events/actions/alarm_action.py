"""
VisionX — Alarm Action
=========================
Sound alarm / siren when critical event triggers.

Contract note
-------------
This class previously declared ``async def execute(self, event: dict, ...)``
and did not subclass :class:`~events.event_engine.EventAction`. The engine
dispatches actions synchronously on a thread pool, so calling it returned an
un-awaited coroutine — truthy — and the engine recorded a **successful alarm
that never sounded**. It now implements the synchronous ``EventAction``
contract and takes the ``Event`` model rather than a dict.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from events.event_engine import EventAction
from shared.models import Event


class AlarmAction(EventAction):
    """
    Trigger audio alarm for critical events.

    Supports local buzzer (GPIO), system sound, and network siren control.
    """

    action_type = "alarm"

    #: Beeping for the full alarm duration occupies a dispatch worker for that
    #: whole time. Capped so one alarm cannot starve the (bounded) pool.
    MAX_BLOCKING_SECONDS = 3

    def __init__(self, alarm_type: str = "system", duration: int = 5):
        self.alarm_type = alarm_type  # system, gpio, network
        self.duration = duration

        logger.info(f"AlarmAction initialized (type={alarm_type}, duration={duration}s)")

    def execute(self, event: Event, context: dict[str, Any]) -> bool:
        """Sound the configured alarm. Returns True only if it actually fired."""
        severity = event.severity or "warning"
        message = event.message or "Alert triggered"

        logger.warning(f"🔊 ALARM: {message} (severity={severity})")

        try:
            if self.alarm_type == "system":
                return self._system_beep(severity)

            if self.alarm_type == "gpio":
                logger.error(
                    "GPIO alarm is not implemented — no buzzer was driven. "
                    "Implement _gpio_beep() before relying on this action."
                )
                return False

            if self.alarm_type == "network":
                logger.error(
                    "Network siren is not implemented — no siren was triggered. "
                    "Use WebhookAction or IoTAction to drive a network siren."
                )
                return False

            logger.error(f"Unknown alarm type: {self.alarm_type}")
            return False

        except Exception as e:
            logger.error(f"Alarm failed: {e}")
            return False

    def _system_beep(self, severity: str) -> bool:
        """Emit a local audible beep. Windows uses winsound; others use the bell."""
        seconds = min(self.duration, self.MAX_BLOCKING_SECONDS)

        try:
            import winsound
        except ImportError:
            # POSIX fallback — terminal bell. Writing to stdout is the only
            # portable option without an audio dependency.
            print("\a", end="", flush=True)
            return True

        frequency = 2500 if severity in ("critical", "emergency", "danger") else 1500
        winsound.Beep(frequency, int(seconds * 1000))
        return True
