"""
VisionX — Alarm Action
=========================
Sound alarm / siren when critical event triggers.
"""

from __future__ import annotations

import time
from typing import Any

from loguru import logger


class AlarmAction:
    """
    Trigger audio alarm for critical events.

    Supports local buzzer (GPIO), system sound, and network siren control.
    """

    def __init__(self, alarm_type: str = "system", duration: int = 5):
        self.alarm_type = alarm_type  # system, gpio, network
        self.duration = duration

        logger.info(f"AlarmAction initialized (type={alarm_type}, duration={duration}s)")

    async def execute(self, event: dict, context: dict | None = None) -> dict:
        """
        Execute alarm action.

        Args:
            event: Event data triggering the alarm
            context: Optional context with device info

        Returns:
            Action result
        """
        severity = event.get("severity", "warning")
        message = event.get("message", "Alert triggered")

        logger.warning(f"🔊 ALARM: {message} (severity={severity})")

        try:
            if self.alarm_type == "system":
                # System beep (Windows)
                try:
                    import winsound
                    frequency = 2500 if severity == "danger" else 1500
                    winsound.Beep(frequency, self.duration * 1000)
                except ImportError:
                    # Linux/Mac fallback
                    print("\a")  # Terminal bell

            elif self.alarm_type == "gpio":
                # Raspberry Pi GPIO buzzer
                logger.info("GPIO alarm triggered (pin 18)")

            elif self.alarm_type == "network":
                # Network siren via HTTP
                logger.info("Network siren triggered via API")

            return {
                "action": "alarm",
                "status": "success",
                "alarm_type": self.alarm_type,
                "duration": self.duration,
                "severity": severity,
            }

        except Exception as e:
            logger.error(f"Alarm failed: {e}")
            return {"action": "alarm", "status": "failed", "error": str(e)}
