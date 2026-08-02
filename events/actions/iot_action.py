"""
VisionX — IoT Action
========================
Trigger IoT devices (MQTT/HTTP) when events fire.
Supports buzzer, alarm, relay, and HTTP-based IoT devices.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from events.event_engine import EventAction
from shared.models import Event
from shared.url_safety import UnsafeURLError, validate_outbound_url


class IoTAction(EventAction):
    """Trigger IoT device via HTTP or MQTT signal."""

    action_type = "iot"

    def __init__(
        self,
        device_url: str = "",
        device_type: str = "http",  # "http" or "mqtt"
        signal_payload: dict[str, Any] | None = None,
    ):
        self.device_url = device_url
        self.device_type = device_type
        self.signal_payload = signal_payload or {"action": "trigger", "state": "on"}

    def execute(self, event: Event, context: dict[str, Any]) -> bool:
        """Send signal to IoT device."""
        if not self.device_url:
            logger.warning("IoT action: no device URL configured")
            return False

        if self.device_type == "http":
            return self._send_http(event)
        elif self.device_type == "mqtt":
            return self._send_mqtt(event)
        else:
            logger.error(f"Unknown IoT device type: {self.device_type}")
            return False

    def _send_http(self, event: Event) -> bool:
        """Send HTTP signal to IoT device."""
        try:
            validate_outbound_url(self.device_url)
        except UnsafeURLError as e:
            # IoT devices are commonly on the LAN, so this is the action most
            # likely to need VISIONX_WEBHOOK_ALLOWED_HOSTS. Making that an
            # explicit opt-in keeps the default safe.
            logger.error(f"IoT request blocked by URL policy: {e}")
            return False

        try:
            import requests

            payload = {
                **self.signal_payload,
                "event_type": event.event_type,
                "severity": event.severity,
                "message": event.message,
            }

            response = requests.post(
                self.device_url,
                json=payload,
                timeout=5,
                allow_redirects=False,
            )

            if response.status_code < 300:
                logger.info(f"IoT signal sent to {self.device_url}")
                return True

            logger.warning(f"IoT signal failed: {response.status_code}")
            return False

        except Exception as e:
            logger.error(f"IoT HTTP error: {e}")
            return False

    def _send_mqtt(self, event: Event) -> bool:
        """
        Send MQTT message to IoT device.

        Not implemented. This previously logged "[MQTT] Would send..." and
        returned ``True``, so the engine recorded a delivered alert for a
        message that was never sent (EXECUTION_RULES R7). Returning False makes
        the gap visible in the dead-letter queue instead.
        """
        logger.error(
            f"MQTT transport is not implemented — signal to {self.device_url} "
            f"was NOT sent ({event.severity}: {event.message}). "
            f"Install paho-mqtt and implement _send_mqtt, or use device_type='http'."
        )
        return False
