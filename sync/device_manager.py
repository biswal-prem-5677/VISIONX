"""
VisionX — Device Manager
========================================
Register, monitor, and manage edge devices.
Tracks heartbeat, status, capabilities, and firmware versions.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional
from uuid import uuid4

from loguru import logger
from pydantic import BaseModel, Field


class DeviceType(str, Enum):
    EDGE_NODE = "edge_node"      # Jetson / RPi
    CAMERA = "camera"            # RTSP / USB camera
    MOBILE = "mobile"            # Phone / Tablet
    DESKTOP = "desktop"          # Desktop client
    CLOUD_WORKER = "cloud_worker"  # Cloud GPU worker


class DeviceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    UPDATING = "updating"
    ERROR = "error"


class DeviceCapabilities(BaseModel):
    """Hardware capabilities of a device."""
    cpu_cores: int = 0
    ram_gb: float = 0
    gpu_available: bool = False
    gpu_model: str = ""
    gpu_vram_gb: float = 0
    camera_count: int = 0
    max_fps: int = 30
    supported_models: list[str] = Field(default_factory=list)
    network_type: str = "ethernet"  # ethernet, wifi, cellular
    storage_gb: float = 0


class DeviceInfo(BaseModel):
    """Full device registration record."""
    device_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = "Unnamed Device"
    device_type: DeviceType = DeviceType.EDGE_NODE
    status: DeviceStatus = DeviceStatus.OFFLINE
    ip_address: str = ""
    firmware_version: str = "1.0.0"
    model_version: str = ""
    capabilities: DeviceCapabilities = Field(default_factory=DeviceCapabilities)
    location: str = ""
    tags: list[str] = Field(default_factory=list)

    last_heartbeat: Optional[datetime] = None
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    uptime_seconds: float = 0
    error_message: str = ""


class DeviceManager:
    """
    Manages the fleet of VisionX edge devices.

    Responsibilities:
    - Device registration (self-registration via API)
    - Heartbeat monitoring (mark offline after timeout)
    - Status tracking (online/offline/degraded/error)
    - Capability querying (what can this device run?)
    - Remote commands (restart, update, reconfigure)
    - Device grouping by location/tags
    """

    def __init__(
        self,
        heartbeat_timeout_seconds: float = 60.0,
        check_interval_seconds: float = 15.0,
    ):
        self.heartbeat_timeout = heartbeat_timeout_seconds
        self.check_interval = check_interval_seconds
        self._devices: dict[str, DeviceInfo] = {}
        self._command_queue: dict[str, list[dict]] = {}
        self._running = False

        logger.info(
            f"DeviceManager initialized "
            f"(timeout={heartbeat_timeout_seconds}s, check={check_interval_seconds}s)"
        )

    # ─── Registration ────────────────────────────────────────────────────

    def register(self, device: DeviceInfo) -> DeviceInfo:
        """Register a new device or update existing."""
        device.status = DeviceStatus.ONLINE
        device.last_heartbeat = datetime.now(timezone.utc)
        self._devices[device.device_id] = device
        self._command_queue.setdefault(device.device_id, [])
        logger.info(f"Device registered: {device.name} ({device.device_id[:8]})")
        return device

    def unregister(self, device_id: str) -> bool:
        """Remove a device from the fleet."""
        if device_id in self._devices:
            name = self._devices[device_id].name
            del self._devices[device_id]
            self._command_queue.pop(device_id, None)
            logger.info(f"Device unregistered: {name} ({device_id[:8]})")
            return True
        return False

    # ─── Heartbeat ───────────────────────────────────────────────────────

    def heartbeat(self, device_id: str, metrics: Optional[dict] = None) -> bool:
        """Process a heartbeat from a device."""
        device = self._devices.get(device_id)
        if not device:
            logger.warning(f"Heartbeat from unknown device: {device_id[:8]}")
            return False

        now = datetime.now(timezone.utc)
        if device.last_heartbeat:
            device.uptime_seconds += (now - device.last_heartbeat).total_seconds()

        device.last_heartbeat = now
        device.status = DeviceStatus.ONLINE
        device.error_message = ""

        if metrics:
            # Update any runtime metrics
            if "model_version" in metrics:
                device.model_version = metrics["model_version"]
            if "error" in metrics:
                device.error_message = metrics["error"]
                device.status = DeviceStatus.DEGRADED

        return True

    # ─── Queries ─────────────────────────────────────────────────────────

    def get_device(self, device_id: str) -> Optional[DeviceInfo]:
        """Get device by ID."""
        return self._devices.get(device_id)

    def list_devices(
        self,
        status_filter: Optional[DeviceStatus] = None,
        type_filter: Optional[DeviceType] = None,
        tag: Optional[str] = None,
    ) -> list[DeviceInfo]:
        """List devices with optional filters."""
        devices = list(self._devices.values())
        if status_filter:
            devices = [d for d in devices if d.status == status_filter]
        if type_filter:
            devices = [d for d in devices if d.device_type == type_filter]
        if tag:
            devices = [d for d in devices if tag in d.tags]
        return devices

    def get_online_devices(self) -> list[DeviceInfo]:
        """Get all online devices."""
        return self.list_devices(status_filter=DeviceStatus.ONLINE)

    def get_fleet_status(self) -> dict:
        """Get fleet-wide status summary."""
        total = len(self._devices)
        online = sum(1 for d in self._devices.values() if d.status == DeviceStatus.ONLINE)
        offline = sum(1 for d in self._devices.values() if d.status == DeviceStatus.OFFLINE)
        degraded = sum(1 for d in self._devices.values() if d.status == DeviceStatus.DEGRADED)
        return {
            "total": total,
            "online": online,
            "offline": offline,
            "degraded": degraded,
            "error": total - online - offline - degraded,
        }

    # ─── Remote Commands ─────────────────────────────────────────────────

    def send_command(self, device_id: str, command: str, params: Optional[dict] = None) -> bool:
        """Queue a command for a device to pick up on next heartbeat."""
        if device_id not in self._devices:
            return False

        cmd = {
            "id": str(uuid4()),
            "command": command,
            "params": params or {},
            "issued_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending",
        }
        self._command_queue[device_id].append(cmd)
        logger.info(f"Command queued for {device_id[:8]}: {command}")
        return True

    def get_pending_commands(self, device_id: str) -> list[dict]:
        """Get and clear pending commands for a device."""
        commands = self._command_queue.get(device_id, [])
        self._command_queue[device_id] = []
        return commands

    def broadcast_command(self, command: str, params: Optional[dict] = None) -> int:
        """Send a command to all online devices."""
        count = 0
        for device in self.get_online_devices():
            self.send_command(device.device_id, command, params)
            count += 1
        logger.info(f"Broadcast '{command}' to {count} devices")
        return count

    # ─── Health Check Loop ───────────────────────────────────────────────

    async def start_monitoring(self) -> None:
        """Start background health check loop."""
        self._running = True
        logger.info("Device monitoring started")

        while self._running:
            self._check_heartbeats()
            await asyncio.sleep(self.check_interval)

    def stop_monitoring(self) -> None:
        """Stop the monitoring loop."""
        self._running = False
        logger.info("Device monitoring stopped")

    def _check_heartbeats(self) -> None:
        """Mark devices offline if heartbeat exceeds timeout."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=self.heartbeat_timeout)

        for device in self._devices.values():
            if device.status == DeviceStatus.ONLINE and device.last_heartbeat:
                if device.last_heartbeat < cutoff:
                    device.status = DeviceStatus.OFFLINE
                    logger.warning(f"Device offline (no heartbeat): {device.name} ({device.device_id[:8]})")
