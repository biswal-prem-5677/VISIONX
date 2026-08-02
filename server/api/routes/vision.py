"""
VisionX — Vision Routes
===========================
Vision processing API endpoints.

Authorization
-------------
All routes require an authenticated caller. Rule creation additionally requires
``Permission.MANAGE_RULES`` — rules drive real-world actions (alarms, webhooks,
emails), so rule creation is a privileged operation, not a read.
"""

from __future__ import annotations

from typing import Any

try:
    from fastapi import APIRouter, Depends, HTTPException  # noqa: F401
except ImportError:
    raise

from pydantic import BaseModel

from server.api.dependencies import get_current_user, require_permission
from server.auth.rbac import Permission

router = APIRouter(dependencies=[Depends(get_current_user)])


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


@router.post(
    "/rules",
    dependencies=[Depends(require_permission(Permission.MANAGE_RULES))],
)
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
