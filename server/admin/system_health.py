"""
VisionX — System Health Monitor
========================================
Real-time system health monitoring for admin dashboard.
"""

from __future__ import annotations

import platform
import psutil
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel
from loguru import logger


class SystemHealth(BaseModel):
    cpu_percent: float = 0.0
    memory_used_gb: float = 0.0
    memory_total_gb: float = 0.0
    memory_percent: float = 0.0
    disk_used_gb: float = 0.0
    disk_total_gb: float = 0.0
    disk_percent: float = 0.0
    gpu_available: bool = False
    gpu_memory_used_mb: float = 0.0
    gpu_memory_total_mb: float = 0.0
    active_cameras: int = 0
    active_websockets: int = 0
    events_per_minute: int = 0
    uptime_seconds: float = 0.0
    python_version: str = ""
    os_info: str = ""
    status: str = "healthy"  # healthy, degraded, critical
    checked_at: Optional[datetime] = None


class SystemHealthMonitor:
    """System-wide health monitoring."""

    def __init__(self):
        self._start_time = datetime.now(timezone.utc)
        logger.info("SystemHealthMonitor initialized")

    async def get_health(self) -> SystemHealth:
        """Get current system health snapshot."""
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            cpu = psutil.cpu_percent(interval=0.1)

            uptime = (datetime.now(timezone.utc) - self._start_time).total_seconds()

            health = SystemHealth(
                cpu_percent=cpu,
                memory_used_gb=round(memory.used / (1024**3), 2),
                memory_total_gb=round(memory.total / (1024**3), 2),
                memory_percent=memory.percent,
                disk_used_gb=round(disk.used / (1024**3), 2),
                disk_total_gb=round(disk.total / (1024**3), 2),
                disk_percent=round(disk.percent, 1),
                uptime_seconds=uptime,
                python_version=platform.python_version(),
                os_info=f"{platform.system()} {platform.release()}",
                checked_at=datetime.now(timezone.utc),
            )

            # Determine status
            if cpu > 90 or memory.percent > 90:
                health.status = "critical"
            elif cpu > 70 or memory.percent > 70:
                health.status = "degraded"
            else:
                health.status = "healthy"

            return health

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return SystemHealth(status="critical", checked_at=datetime.now(timezone.utc))

    async def get_service_status(self) -> dict:
        """Check status of dependent services."""
        services = {
            "database": "unknown",
            "redis": "unknown",
            "pinecone": "unknown",
            "edge_pipeline": "unknown",
        }
        # In production, ping each service
        return services
