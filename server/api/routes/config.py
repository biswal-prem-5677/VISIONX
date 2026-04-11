"""
VisionX — Config API Routes
===============================
Pipeline configuration management endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/config", tags=["config"])


class ModuleConfig(BaseModel):
    """AI module configuration."""
    module_id: str
    enabled: bool
    confidence_threshold: float = 0.5
    custom_params: dict = {}


class PerformanceConfig(BaseModel):
    """Performance mode configuration."""
    mode: str = "balanced"  # lite, balanced, max
    resolution: int = 640
    fps: int = 30
    gpu_enabled: bool = True


class PipelineConfig(BaseModel):
    """Complete pipeline configuration."""
    modules: list[ModuleConfig] = []
    performance: PerformanceConfig = PerformanceConfig()
    roi_zones: list[dict] = []


# In-memory config store (replace with DB in production)
_current_config = PipelineConfig()


@router.get("/", response_model=PipelineConfig)
async def get_config():
    """Get current pipeline configuration."""
    return _current_config


@router.put("/", response_model=PipelineConfig)
async def update_config(config: PipelineConfig):
    """Update pipeline configuration."""
    global _current_config
    _current_config = config
    return _current_config


@router.get("/modules", response_model=list[ModuleConfig])
async def get_modules():
    """Get AI module configurations."""
    return _current_config.modules


@router.put("/modules/{module_id}")
async def update_module(module_id: str, config: ModuleConfig):
    """Update single module configuration."""
    for i, m in enumerate(_current_config.modules):
        if m.module_id == module_id:
            _current_config.modules[i] = config
            return {"status": "updated"}
    raise HTTPException(status_code=404, detail="Module not found")


@router.get("/performance", response_model=PerformanceConfig)
async def get_performance():
    """Get performance mode settings."""
    return _current_config.performance


@router.put("/performance")
async def set_performance(config: PerformanceConfig):
    """Set performance mode."""
    _current_config.performance = config
    return {"status": "updated", "mode": config.mode}
