"""
VisionX — Usage Tracking API Route
========================================
Endpoints for viewing usage analytics and quotas.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/usage", tags=["usage"])


class UsageSummary(BaseModel):
    api_requests_today: int = 0
    api_requests_limit: int = 100
    events_today: int = 0
    events_limit: int = 100
    storage_used_gb: float = 0.0
    storage_limit_gb: float = 1.0
    cameras_active: int = 0
    cameras_limit: int = 2
    websocket_connections: int = 0
    websocket_limit: int = 2
    period_start: str = ""
    period_end: str = ""


@router.get("/summary")
async def get_usage_summary():
    """Get current usage summary for the authenticated user."""
    return UsageSummary()


@router.get("/history")
async def get_usage_history(days: int = 30):
    """Get usage history over time."""
    return {"history": [], "period_days": days}


@router.get("/quotas")
async def get_quota_status():
    """Get current quota status and limits."""
    return {
        "tier": "free",
        "quotas": {
            "api_requests": {"used": 0, "limit": 100, "reset_at": ""},
            "events": {"used": 0, "limit": 100, "reset_at": ""},
            "storage": {"used_gb": 0, "limit_gb": 1},
            "cameras": {"active": 0, "limit": 2},
        },
    }
