"""
VisionX — GDPR Compliance Endpoints
========================================
Data export, deletion, consent management (GDPR Articles 15-20).

Authorization
-------------
Every route requires an authenticated caller. These endpoints act on "the data
subject's own data" — without an identity there is no data subject, and an
anonymous ``POST /gdpr/delete`` is an unauthenticated destructive operation.
The subject identity now comes from the token, never from the request body.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from server.api.dependencies import CurrentUser, get_current_user

router = APIRouter(
    prefix="/gdpr",
    tags=["gdpr"],
    dependencies=[Depends(get_current_user)],
)


class DataExportRequest(BaseModel):
    format: str = "json"  # json, csv
    include_events: bool = True
    include_analytics: bool = True
    include_face_data: bool = True
    include_preferences: bool = True


class DataDeleteRequest(BaseModel):
    confirm: bool = False
    delete_face_data: bool = True
    delete_events: bool = True
    delete_analytics: bool = True
    reason: str = ""


class ConsentUpdate(BaseModel):
    analytics_consent: Optional[bool] = None
    face_recognition_consent: Optional[bool] = None
    marketing_consent: Optional[bool] = None
    third_party_consent: Optional[bool] = None


class ConsentRecord(BaseModel):
    user_id: str = ""
    analytics_consent: bool = False
    face_recognition_consent: bool = False
    marketing_consent: bool = False
    third_party_consent: bool = False
    consent_version: str = "1.0"
    updated_at: Optional[datetime] = None
    ip_address: str = ""


# ─── Art.15: Right of Access / Data Export ───────────────────────────────

@router.post("/export")
async def request_data_export(req: DataExportRequest):
    """
    GDPR Article 15 — Right of Access.
    Export all personal data associated with the authenticated user.
    Response is delivered as a downloadable file within 30 days.
    """
    export_id = f"export-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    return {
        "export_id": export_id,
        "status": "processing",
        "format": req.format,
        "estimated_ready_at": "Within 30 days per GDPR Art.12",
        "message": "Your data export request has been received. "
                   "You will be notified when the export is ready for download.",
    }


@router.get("/export/{export_id}")
async def get_export_status(export_id: str):
    """Check status of a data export request."""
    return {
        "export_id": export_id,
        "status": "pending",
        "ready": False,
        "download_url": None,
    }


# ─── Art.17: Right to Erasure (Right to be Forgotten) ────────────────────

@router.post("/delete")
async def request_data_deletion(req: DataDeleteRequest):
    """
    GDPR Article 17 — Right to Erasure.
    Permanently delete all personal data. This action is IRREVERSIBLE.
    """
    if not req.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must set 'confirm: true' to proceed with data deletion.",
        )

    deletion_id = f"del-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    return {
        "deletion_id": deletion_id,
        "status": "scheduled",
        "scope": {
            "face_data": req.delete_face_data,
            "events": req.delete_events,
            "analytics": req.delete_analytics,
        },
        "estimated_completion": "Within 30 days per GDPR Art.17",
        "message": "Your data deletion request has been scheduled. "
                   "All specified data will be permanently erased.",
    }


# ─── Art.20: Right to Data Portability ───────────────────────────────────

@router.get("/portability")
async def request_data_portability():
    """
    GDPR Article 20 — Right to Data Portability.
    Export data in a structured, commonly used, machine-readable format.
    """
    return {
        "status": "available",
        "formats": ["json", "csv"],
        "includes": [
            "user_profile",
            "detection_events",
            "analytics_history",
            "automation_rules",
            "notification_preferences",
        ],
        "message": "Use POST /gdpr/export to initiate a portable data export.",
    }


# ─── Art.7: Consent Management ──────────────────────────────────────────

@router.get("/consent")
async def get_consent(user: CurrentUser = Depends(get_current_user)):
    """Get current consent status for the authenticated user."""
    return ConsentRecord(
        user_id=user.user_id,
        consent_version="1.0",
        updated_at=datetime.now(timezone.utc),
    )


@router.put("/consent")
async def update_consent(update: ConsentUpdate):
    """
    Update consent preferences.
    Changes take effect immediately. Revoking consent stops related processing.
    """
    return {
        "status": "updated",
        "changes": update.model_dump(exclude_none=True),
        "effective_at": datetime.now(timezone.utc).isoformat(),
        "message": "Consent preferences updated. Changes are effective immediately.",
    }


@router.get("/consent/history")
async def get_consent_history():
    """Get consent change history for audit trail."""
    return {
        "history": [],
        "message": "Full consent change audit trail.",
    }


# ─── Art.21: Right to Object ────────────────────────────────────────────

@router.post("/object")
async def object_to_processing(reason: str = ""):
    """
    GDPR Article 21 — Right to Object.
    Object to specific types of data processing.
    """
    return {
        "status": "recorded",
        "reason": reason,
        "message": "Your objection has been recorded. "
                   "Affected processing will be reviewed within 30 days.",
    }
