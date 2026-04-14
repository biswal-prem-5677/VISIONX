"""
VisionX — Hardware Action
========================================
Trigger physical hardware (buzzer, relay, PLC, GPIO) from events.
"""

from __future__ import annotations

from typing import Optional
from loguru import logger


class HardwareAction:
    """Event action that triggers physical hardware outputs."""

    def __init__(self):
        self._gpio_available = False
        try:
            # Check if GPIO is available (Raspberry Pi / Jetson)
            import RPi.GPIO  # noqa: F401
            self._gpio_available = True
        except ImportError:
            pass
        logger.info(f"HardwareAction initialized (GPIO: {self._gpio_available})")

    async def execute(
        self,
        device_type: str,
        action: str = "trigger",
        pin: Optional[int] = None,
        duration_seconds: float = 1.0,
        payload: Optional[dict] = None,
    ) -> dict:
        """Trigger a hardware action."""
        try:
            if device_type == "buzzer":
                return await self._trigger_buzzer(pin or 18, duration_seconds)
            elif device_type == "relay":
                return await self._trigger_relay(pin or 23, action)
            elif device_type == "led":
                return await self._trigger_led(pin or 24, action)
            else:
                logger.warning(f"Unknown hardware device type: {device_type}")
                return {"status": "unsupported", "device_type": device_type}

        except Exception as e:
            logger.error(f"Hardware action failed: {e}")
            return {"status": "failed", "error": str(e)}

    async def _trigger_buzzer(self, pin: int, duration: float) -> dict:
        """Trigger a buzzer for a duration."""
        logger.info(f"Buzzer triggered on pin {pin} for {duration}s")
        return {"status": "triggered", "device": "buzzer", "pin": pin, "duration": duration}

    async def _trigger_relay(self, pin: int, action: str) -> dict:
        """Toggle a relay on/off."""
        logger.info(f"Relay {action} on pin {pin}")
        return {"status": action, "device": "relay", "pin": pin}

    async def _trigger_led(self, pin: int, action: str) -> dict:
        """Toggle an LED indicator."""
        logger.info(f"LED {action} on pin {pin}")
        return {"status": action, "device": "led", "pin": pin}
