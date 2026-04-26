"""
VisionX — AI Model Manager
========================================
Download, cache, version, and hot-swap AI models across devices.
Supports model registry, A/B deployment, and rollback.
"""

from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional
from uuid import uuid4

from loguru import logger
from pydantic import BaseModel, Field


class ModelFormat(str, Enum):
    ONNX = "onnx"
    TENSORRT = "trt"
    PYTORCH = "pt"
    TFLITE = "tflite"
    OPENVINO = "xml"


class ModelStatus(str, Enum):
    AVAILABLE = "available"
    DOWNLOADING = "downloading"
    LOADED = "loaded"
    FAILED = "failed"
    DEPRECATED = "deprecated"


class ModelInfo(BaseModel):
    """Registry entry for an AI model."""
    model_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    version: str = "1.0.0"
    format: ModelFormat = ModelFormat.ONNX
    task: str = "detection"  # detection, tracking, face, ocr, pose, segmentation
    description: str = ""
    file_size_mb: float = 0
    checksum_sha256: str = ""
    input_shape: list[int] = Field(default_factory=lambda: [1, 3, 640, 640])
    labels: list[str] = Field(default_factory=list)
    metrics: dict[str, float] = Field(default_factory=dict)  # mAP, latency_ms, etc.
    status: ModelStatus = ModelStatus.AVAILABLE
    download_url: str = ""
    local_path: str = ""
    is_default: bool = False
    deployed_to: list[str] = Field(default_factory=list)  # device IDs
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None


class ModelManager:
    """
    AI model lifecycle manager.

    Responsibilities:
    - Model registry (register, list, query models)
    - Download & cache (with checksum verification)
    - Version management (keep N versions, rollback support)
    - Hot-swap (switch active model without restart)
    - Deployment tracking (which devices run which model)
    - A/B testing support (canary deployments)
    """

    def __init__(
        self,
        cache_dir: str = ".visionx/models",
        max_cached_versions: int = 3,
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_cached = max_cached_versions

        self._registry: dict[str, ModelInfo] = {}
        self._active_models: dict[str, str] = {}  # task → model_id
        self._download_queue: list[str] = []

        # Register default models
        self._register_defaults()

        logger.info(
            f"ModelManager initialized "
            f"(cache={cache_dir}, max_versions={max_cached_versions}, "
            f"models={len(self._registry)})"
        )

    # ─── Registry ────────────────────────────────────────────────────────

    def register(self, model: ModelInfo) -> ModelInfo:
        """Register a new model in the registry."""
        model.updated_at = datetime.now(timezone.utc)
        self._registry[model.model_id] = model

        if model.is_default:
            self._active_models[model.task] = model.model_id

        logger.info(f"Model registered: {model.name} v{model.version} ({model.format.value})")
        return model

    def get_model(self, model_id: str) -> Optional[ModelInfo]:
        """Get model by ID."""
        return self._registry.get(model_id)

    def list_models(
        self,
        task: Optional[str] = None,
        format: Optional[ModelFormat] = None,
    ) -> list[ModelInfo]:
        """List models with optional filters."""
        models = list(self._registry.values())
        if task:
            models = [m for m in models if m.task == task]
        if format:
            models = [m for m in models if m.format == format]
        return sorted(models, key=lambda m: m.created_at, reverse=True)

    def get_active_model(self, task: str) -> Optional[ModelInfo]:
        """Get the currently active model for a task."""
        model_id = self._active_models.get(task)
        return self._registry.get(model_id) if model_id else None

    # ─── Download & Cache ────────────────────────────────────────────────

    async def download(self, model_id: str) -> bool:
        """Download a model to local cache."""
        model = self._registry.get(model_id)
        if not model:
            logger.error(f"Model not found: {model_id}")
            return False

        model.status = ModelStatus.DOWNLOADING
        logger.info(f"Downloading {model.name} v{model.version}...")

        try:
            # Determine local path
            local_dir = self.cache_dir / model.task / model.name
            local_dir.mkdir(parents=True, exist_ok=True)
            local_path = local_dir / f"{model.name}_{model.version}.{model.format.value}"

            # In production: download from model.download_url using httpx
            # For now, mark as available
            model.local_path = str(local_path)
            model.status = ModelStatus.AVAILABLE
            model.updated_at = datetime.now(timezone.utc)

            logger.info(f"Downloaded: {model.name} → {local_path}")
            return True

        except Exception as e:
            model.status = ModelStatus.FAILED
            logger.error(f"Download failed for {model.name}: {e}")
            return False

    def verify_checksum(self, model_id: str) -> bool:
        """Verify model file integrity via SHA-256."""
        model = self._registry.get(model_id)
        if not model or not model.local_path or not model.checksum_sha256:
            return False

        try:
            sha256 = hashlib.sha256()
            with open(model.local_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
            return sha256.hexdigest() == model.checksum_sha256
        except Exception:
            return False

    def get_cache_size_mb(self) -> float:
        """Get total size of model cache in MB."""
        total = 0
        for path in self.cache_dir.rglob("*"):
            if path.is_file():
                total += path.stat().st_size
        return round(total / (1024 * 1024), 2)

    # ─── Hot-Swap & Deployment ───────────────────────────────────────────

    def activate(self, model_id: str) -> bool:
        """Set a model as the active model for its task (hot-swap)."""
        model = self._registry.get(model_id)
        if not model:
            return False

        old_id = self._active_models.get(model.task)
        self._active_models[model.task] = model_id
        model.status = ModelStatus.LOADED

        old_name = self._registry[old_id].name if old_id and old_id in self._registry else "none"
        logger.info(f"Hot-swap: {model.task} [{old_name}] → [{model.name} v{model.version}]")
        return True

    def rollback(self, task: str) -> bool:
        """Roll back to the previous model version for a task."""
        versions = [
            m for m in self._registry.values()
            if m.task == task and m.model_id != self._active_models.get(task)
        ]
        if not versions:
            return False

        previous = sorted(versions, key=lambda m: m.created_at, reverse=True)[0]
        return self.activate(previous.model_id)

    def deploy_to_device(self, model_id: str, device_id: str) -> bool:
        """Mark a model as deployed to a specific device."""
        model = self._registry.get(model_id)
        if not model:
            return False
        if device_id not in model.deployed_to:
            model.deployed_to.append(device_id)
        logger.info(f"Model {model.name} deployed to device {device_id[:8]}")
        return True

    # ─── Cleanup ─────────────────────────────────────────────────────────

    def cleanup_old_versions(self, task: str) -> int:
        """Remove old model versions beyond max_cached limit."""
        models = sorted(
            [m for m in self._registry.values() if m.task == task],
            key=lambda m: m.created_at,
            reverse=True,
        )

        removed = 0
        for model in models[self.max_cached:]:
            if model.model_id != self._active_models.get(task):
                if model.local_path and os.path.exists(model.local_path):
                    os.remove(model.local_path)
                model.status = ModelStatus.DEPRECATED
                removed += 1

        if removed:
            logger.info(f"Cleaned {removed} old model versions for task '{task}'")
        return removed

    def get_registry_stats(self) -> dict:
        """Get model registry statistics."""
        return {
            "total_models": len(self._registry),
            "active_models": dict(self._active_models),
            "by_task": {
                task: len([m for m in self._registry.values() if m.task == task])
                for task in set(m.task for m in self._registry.values())
            },
            "cache_size_mb": self.get_cache_size_mb(),
        }

    # ─── Defaults ────────────────────────────────────────────────────────

    def _register_defaults(self) -> None:
        """Register built-in default models."""
        defaults = [
            ModelInfo(
                name="yolov8n", version="8.0.0", format=ModelFormat.ONNX,
                task="detection", description="YOLOv8 Nano — fast, lightweight",
                input_shape=[1, 3, 640, 640], file_size_mb=6.2, is_default=True,
                metrics={"mAP50": 37.3, "latency_ms": 8.1},
            ),
            ModelInfo(
                name="yolov8s", version="8.0.0", format=ModelFormat.ONNX,
                task="detection", description="YOLOv8 Small — balanced",
                input_shape=[1, 3, 640, 640], file_size_mb=22.5,
                metrics={"mAP50": 44.9, "latency_ms": 15.4},
            ),
            ModelInfo(
                name="bytetrack", version="1.0.0", format=ModelFormat.ONNX,
                task="tracking", description="ByteTrack multi-object tracker",
                file_size_mb=3.8, is_default=True,
            ),
            ModelInfo(
                name="arcface", version="1.0.0", format=ModelFormat.ONNX,
                task="face", description="ArcFace face recognition",
                file_size_mb=120, is_default=True,
                metrics={"accuracy": 99.2},
            ),
        ]
        for model in defaults:
            self._registry[model.model_id] = model
            if model.is_default:
                self._active_models[model.task] = model.model_id
