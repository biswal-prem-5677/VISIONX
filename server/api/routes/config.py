"""
VisionX — Config API Routes
===============================
Pipeline configuration management endpoints.

Authorization
-------------
Reads require an authenticated caller; writes require
``Permission.MANAGE_DEVICES``. Every write here changes what the detection
pipeline does — disabling a module or dropping the confidence threshold
silently degrades a customer's security coverage — and all of them were
previously callable by anyone who could reach the API.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from server.api.dependencies import get_current_user, require_permission
from server.auth.rbac import Permission

router = APIRouter(
    prefix="/config",
    tags=["config"],
    dependencies=[Depends(get_current_user)],
)

_manage_config = require_permission(Permission.MANAGE_DEVICES)


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


@router.put(
    "/",
    response_model=PipelineConfig,
    dependencies=[Depends(_manage_config)],
)
async def update_config(config: PipelineConfig):
    """Update pipeline configuration."""
    global _current_config
    _current_config = config
    return _current_config


@router.get("/modules", response_model=list[ModuleConfig])
async def get_modules():
    """Get AI module configurations."""
    return _current_config.modules


@router.put("/modules/{module_id}", dependencies=[Depends(_manage_config)])
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


@router.put("/performance", dependencies=[Depends(_manage_config)])
async def set_performance(config: PerformanceConfig):
    """Set performance mode."""
    _current_config.performance = config
    return {"status": "updated", "mode": config.mode}
