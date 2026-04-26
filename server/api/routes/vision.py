"""
VisionX — Vision Routes
===========================
Vision processing API endpoints.
"""

from __future__ import annotations

from typing import Any

try:
    from fastapi import APIRouter, HTTPException  # noqa: F401
except ImportError:
    raise

from pydantic import BaseModel

router = APIRouter()


class RuleCreateRequest(BaseModel):
    name: str
    conditions: list[dict[str, Any]]
    actions: list[str]
    severity: str = "warning"
    cooldown_seconds: int = 30


class RuleResponse(BaseModel):
    id: str
    name: str
    enabled: bool
    severity: str
    conditions: list[dict[str, Any]]
    actions: list[str]


@router.get("/status")
async def vision_status():
    """Get vision pipeline status."""
    return {
        "status": "ready",
        "modules": {
            "detection": "active",
            "tracking": "active",
            "counting": "active",
            "measurement": "active",
        },
    }


@router.get("/modules")
async def list_modules():
    """List all available AI modules."""
    return {
        "edge": [
            {"name": "detection", "type": "edge", "status": "active"},
            {"name": "tracking", "type": "edge", "status": "active"},
            {"name": "counting", "type": "edge", "status": "active"},
            {"name": "measurement", "type": "edge", "status": "active"},
        ],
        "cloud": [
            {"name": "ocr", "type": "cloud", "status": "available"},
            {"name": "face_recognition", "type": "cloud", "status": "available"},
            {"name": "pose_estimation", "type": "cloud", "status": "available"},
            {"name": "segmentation", "type": "cloud", "status": "available"},
            {"name": "behavior_analysis", "type": "cloud", "status": "available"},
            {"name": "speed_estimation", "type": "cloud", "status": "available"},
        ],
    }


@router.post("/rules")
async def create_rule(req: RuleCreateRequest):
    """Create a new detection rule."""
    import uuid

    rule_id = str(uuid.uuid4())[:8]
    return RuleResponse(
        id=rule_id,
        name=req.name,
        enabled=True,
        severity=req.severity,
        conditions=req.conditions,
        actions=req.actions,
    )
