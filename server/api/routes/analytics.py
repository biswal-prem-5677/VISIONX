"""
VisionX — Analytics Routes
==============================
Analytics and reporting API endpoints.

Authorization
-------------
All routes require ``Permission.VIEW_ANALYTICS``. Occupancy and movement
analytics describe how a customer's site is used; they were previously served
to anonymous callers.
"""

from __future__ import annotations

try:
    from fastapi import APIRouter, Depends, Query
except ImportError:
    raise

from server.api.dependencies import require_permission
from server.auth.rbac import Permission

router = APIRouter(
    dependencies=[Depends(require_permission(Permission.VIEW_ANALYTICS))],
)


@router.get("/summary")
async def analytics_summary(hours: int = Query(24, ge=1, le=168)):
    """Get analytics summary for a time period."""
    return {
        "period_hours": hours,
        "total_detections": 0,
        "total_events": 0,
        "detection_by_class": {},
        "peak_count": 0,
        "average_count": 0.0,
    }


@router.get("/timeseries")
async def timeseries(
    class_name: str = Query("person"),
    hours: int = Query(1, ge=1, le=24),
):
    """Get detection count time series."""
    return {
        "class_name": class_name,
        "period_hours": hours,
        "data": [],
    }


@router.get("/heatmap")
async def heatmap():
    """Get spatial activity heatmap data."""
    return {
        "cells": [],
        "resolution": 50,
    }
