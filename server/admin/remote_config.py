"""
VisionX — Remote Config Service
========================================
Push configuration changes to connected devices and clients.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel
from loguru import logger


class ConfigEntry(BaseModel):
    key: str
    value: Any
    description: str = ""
    updated_by: str = "system"
    updated_at: Optional[datetime] = None
    is_override: bool = False


class RemoteConfig:
    """
    Remote configuration management.
    Allows admins to push config changes to all devices without redeployment.
    """

    def __init__(self):
        self._config: dict[str, ConfigEntry] = {}
        self._defaults: dict[str, Any] = {
            "detection.confidence_threshold": 0.5,
            "detection.max_detections": 100,
            "detection.model": "yolov8n",
            "tracking.enabled": True,
            "tracking.max_age": 30,
            "events.rate_limit_per_minute": 60,
            "events.email_enabled": True,
            "ui.theme": "obsidian",
            "ui.fps_display": True,
            "privacy.blur_faces": False,
            "privacy.retention_days": 30,
        }
        logger.info(f"RemoteConfig initialized with {len(self._defaults)} defaults")

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value, falling back to default."""
        if key in self._config:
            return self._config[key].value
        return self._defaults.get(key, default)

    def set(self, key: str, value: Any, updated_by: str = "admin") -> ConfigEntry:
        """Set a config value (admin override)."""
        entry = ConfigEntry(
            key=key,
            value=value,
            updated_by=updated_by,
            updated_at=datetime.now(timezone.utc),
            is_override=key in self._defaults,
        )
        self._config[key] = entry
        logger.info(f"Config updated: {key} = {value} (by {updated_by})")
        return entry

    def reset(self, key: str) -> bool:
        """Reset a config key to its default value."""
        if key in self._config:
            del self._config[key]
            logger.info(f"Config reset to default: {key}")
            return True
        return False

    def get_all(self) -> dict[str, Any]:
        """Get all config values (defaults + overrides)."""
        result = dict(self._defaults)
        for key, entry in self._config.items():
            result[key] = entry.value
        return result

    def get_overrides(self) -> list[ConfigEntry]:
        """Get only admin-overridden config entries."""
        return list(self._config.values())
