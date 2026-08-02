"""
VisionX — Hardware Action
========================================
Trigger physical hardware (buzzer, relay, PLC, GPIO) from events.

Contract note
-------------
Previously ``async def execute(self, device_type, action, pin, ...)`` on a
non-``EventAction`` class — never awaited by the engine, and the wrong signature
for dispatch. Device selection now happens in ``__init__``.

Implementation note
-------------------
The ``_trigger_*`` helpers previously **logged** and returned a success dict
without touching a GPIO pin, on any machine, whether or not GPIO existed. For a
physical-safety action that is the most dangerous shape a stub can take: the
system reports that a siren fired when nothing happened. They now drive real
pins via ``RPi.GPIO`` and fail when it is unavailable.
"""

from __future__ import annotations

import time
from typing import Any, Optional

from loguru import logger

from events.event_engine import EventAction
from shared.models import Event

try:  # pragma: no cover - hardware-only import
    import RPi.GPIO as GPIO
except Exception:  # noqa: BLE001 - absent on every non-Pi machine
    GPIO = None  # type: ignore[assignment]


DEFAULT_PINS = {"buzzer": 18, "relay": 23, "led": 24}


class HardwareAction(EventAction):
    """Event action that triggers physical hardware outputs."""

    action_type = "hardware"

    def __init__(
        self,
        device_type: str = "buzzer",
        pin: Optional[int] = None,
        duration_seconds: float = 1.0,
        active_high: bool = True,
    ):
        self.device_type = device_type
        self.pin = pin if pin is not None else DEFAULT_PINS.get(device_type, 18)
        self.duration_seconds = duration_seconds
        self.active_high = active_high
        self._gpio_available = GPIO is not None

        if not self._gpio_available:
            logger.warning(
                "HardwareAction initialized without GPIO (RPi.GPIO unavailable). "
                "Every dispatch will fail rather than pretend to fire."
            )
        else:
            logger.info(
                f"HardwareAction initialized "
                f"(device={device_type}, pin={self.pin}, GPIO: True)"
            )

    def execute(self, event: Event, context: dict[str, Any]) -> bool:
        """Drive the configured output. Returns True only if a pin was driven."""
        if self.device_type not in DEFAULT_PINS:
            logger.error(f"Unknown hardware device type: {self.device_type}")
            return False

        if not self._gpio_available:
            logger.error(
                f"Hardware output NOT driven for '{event.message}' — RPi.GPIO is "
                f"not available on this machine ({self.device_type} pin {self.pin})."
            )
            return False

        try:
            return self._pulse()
        except Exception as e:
            logger.error(f"Hardware action failed: {e}")
            return False

    def _pulse(self) -> bool:
        """Drive the pin active for ``duration_seconds``, then release it."""
        on, off = (GPIO.HIGH, GPIO.LOW) if self.active_high else (GPIO.LOW, GPIO.HIGH)

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        try:
            GPIO.output(self.pin, on)
            time.sleep(self.duration_seconds)
        finally:
            # Always release the pin: leaving a relay latched on because of an
            # exception is a physical-safety problem, not just a bug.
            GPIO.output(self.pin, off)
            GPIO.cleanup(self.pin)

        logger.info(
            f"{self.device_type} triggered on pin {self.pin} "
            f"for {self.duration_seconds}s"
        )
        return True
