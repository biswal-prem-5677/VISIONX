"""
VisionX — Device Authentication
===================================
Device token management for camera/edge device registration.
"""

from __future__ import annotations

import hashlib
import secrets
import time

from loguru import logger
from pydantic import BaseModel, Field


class DeviceToken(BaseModel):
    """A registered device token."""
    device_id: str
    token: str
    name: str = ""
    device_type: str = "edge"  # edge, camera, mobile
    created_at: float = Field(default_factory=time.time)
    last_seen: float = 0.0
    is_active: bool = True


class DeviceAuthManager:
    """
    Device authentication manager.

    Generates and validates device tokens for edge devices,
    cameras, and mobile clients.
    """

    def __init__(self):
        self._devices: dict[str, DeviceToken] = {}

        logger.info("Device Auth Manager initialized")

    def register_device(
        self,
        device_id: str,
        name: str = "",
        device_type: str = "edge",
    ) -> DeviceToken:
        """Register a new device and generate its token."""
        token = self._generate_token(device_id)

        device = DeviceToken(
            device_id=device_id,
            token=token,
            name=name or device_id,
            device_type=device_type,
        )

        self._devices[device_id] = device
        logger.info(f"Device registered: {device_id} ({device_type})")

        return device

    def validate_token(self, device_id: str, token: str) -> bool:
        """Validate a device token."""
        device = self._devices.get(device_id)
        if not device:
            return False

        if not device.is_active:
            return False

        if device.token != token:
            return False

        # Update last seen
        device.last_seen = time.time()
        return True

    def revoke_device(self, device_id: str) -> bool:
        """Revoke a device's access."""
        device = self._devices.get(device_id)
        if device:
            device.is_active = False
            logger.info(f"Device revoked: {device_id}")
            return True
        return False

    def get_active_devices(self) -> list[DeviceToken]:
        """Get all active devices."""
        return [d for d in self._devices.values() if d.is_active]

    @staticmethod
    def _generate_token(device_id: str) -> str:
        """Generate a secure device token."""
        random_bytes = secrets.token_bytes(32)
        return hashlib.sha256(
            f"{device_id}:{random_bytes.hex()}".encode()
        ).hexdigest()
