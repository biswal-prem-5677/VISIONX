"""
VisionX — Device Routes
===========================
Device management API endpoints.

Authorization
-------------
Reads require an authenticated caller; writes require
``Permission.MANAGE_DEVICES``. Before this, every route here was fully
unauthenticated — anyone who could reach the API could enumerate camera source
URIs (which embed ``user:password@`` for RTSP) or delete a site's cameras.
"""

from __future__ import annotations


try:
    from fastapi import APIRouter, Depends, HTTPException
except ImportError:
    raise

from pydantic import BaseModel

from server.api.dependencies import get_current_user, require_permission
from server.auth.rbac import Permission

router = APIRouter(dependencies=[Depends(get_current_user)])

_manage_devices = require_permission(Permission.MANAGE_DEVICES)

# In-memory device store
_devices: dict[str, dict] = {}


class DeviceCreateRequest(BaseModel):
    name: str
    source_type: str  # webcam, rtsp, ip_camera, video_file
    source_uri: str


class DeviceResponse(BaseModel):
    device_id: str
    name: str
    source_type: str
    source_uri: str
    status: str


@router.get("/")
async def list_devices():
    """List all registered devices."""
    return {"devices": list(_devices.values()), "total": len(_devices)}


@router.post(
    "/",
    response_model=DeviceResponse,
    dependencies=[Depends(_manage_devices)],
)
async def register_device(req: DeviceCreateRequest):
    """Register a new camera/device."""
    import uuid

    device_id = str(uuid.uuid4())[:8]
    device = {
        "device_id": device_id,
        "name": req.name,
        "source_type": req.source_type,
        "source_uri": req.source_uri,
        "status": "inactive",
    }

    _devices[device_id] = device
    return DeviceResponse(**device)


@router.delete("/{device_id}", dependencies=[Depends(_manage_devices)])
async def remove_device(device_id: str):
    """Remove a device."""
    if device_id not in _devices:
        raise HTTPException(status_code=404, detail="Device not found")

    del _devices[device_id]
    return {"message": f"Device {device_id} removed"}
