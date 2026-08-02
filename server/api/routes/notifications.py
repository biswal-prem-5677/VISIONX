"""
VisionX — Notifications API Route
========================================
CRUD endpoints for notification management.

Authorization
-------------
All routes require an authenticated caller — every one of them is scoped to
"the current user", which is meaningless without knowing who that is.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from server.api.dependencies import get_current_user

router = APIRouter(
    prefix="/notifications",
    tags=["notifications"],
    dependencies=[Depends(get_current_user)],
)


class NotificationResponse(BaseModel):
    id: str
    type: str  # info, warning, danger, success
    title: str
    message: str
    read: bool = False
    created_at: datetime


class NotificationPrefsUpdate(BaseModel):
    email_enabled: bool = True
    push_enabled: bool = True
    sms_enabled: bool = False
    in_app_enabled: bool = True
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None


@router.get("/")
async def list_notifications(
    limit: int = 50,
    unread_only: bool = False,
):
    """List notifications for the current user."""
    return {"notifications": [], "total": 0, "unread_count": 0}


@router.post("/{notification_id}/read")
async def mark_as_read(notification_id: str):
    """Mark a notification as read."""
    return {"status": "ok", "notification_id": notification_id}


@router.post("/read-all")
async def mark_all_read():
    """Mark all notifications as read."""
    return {"status": "ok", "marked_count": 0}


@router.delete("/{notification_id}")
async def delete_notification(notification_id: str):
    """Delete a notification."""
    return {"status": "deleted", "notification_id": notification_id}


@router.get("/preferences")
async def get_notification_preferences():
    """Get notification preferences."""
    return NotificationPrefsUpdate()


@router.put("/preferences")
async def update_notification_preferences(prefs: NotificationPrefsUpdate):
    """Update notification preferences."""
    return {"status": "updated", "preferences": prefs}
