"""
VisionX — Events Routes
===========================
Event management API endpoints.

Authorization
-------------
All routes require an authenticated caller. Event history is the security
record of a site; it was previously readable without any credential.

Implementation status
---------------------
These endpoints are **not implemented** and say so with ``501``.

They previously returned ``{"events": [], "total": 0}`` — hardcoded, with no
backing store. For an alerting product that is the worst possible stub: a
caller cannot distinguish *"nothing happened"* from *"the query never ran"*,
so a site with a real incident and a site with a broken API look identical.

Implementing them requires the ``events`` table (MASTER_BLUEPRINT → Phase 1);
the API process does not currently own an ``EventEngine`` instance, and the
edge process that does has no persistence to read back from. Tracked as
DEF-021 in EXECUTION_TRACKER.md.
"""

from __future__ import annotations


try:
    from fastapi import APIRouter, Depends, HTTPException, Query, status
except ImportError:
    raise

from pydantic import BaseModel

from server.api.dependencies import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])


#: Shared detail payload so both endpoints fail the same, explicit way.
_NOT_IMPLEMENTED = {
    "code": "not_implemented",
    "message": (
        "Event history is not implemented. It requires the persistent `events` "
        "table, which does not exist yet. This endpoint returns 501 rather than "
        "an empty result so that an absent store is never mistaken for an "
        "absence of events."
    ),
    "tracker_id": "DEF-021",
}


def _not_implemented() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=_NOT_IMPLEMENTED,
    )


class EventResponse(BaseModel):
    """Shape the endpoint will return once persistence lands (Phase 1)."""

    id: str
    event_type: str
    severity: str
    message: str
    source: str
    timestamp: float


@router.get("/", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def list_events(
    limit: int = Query(50, ge=1, le=200),
    severity: str = Query("", description="Filter by severity"),
):
    """
    List recent events.

    Raises:
        HTTPException: 501 — no persistent event store exists yet (DEF-021).
    """
    raise _not_implemented()


@router.get("/stats", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def event_stats():
    """
    Get event statistics.

    Raises:
        HTTPException: 501 — no persistent event store exists yet (DEF-021).
    """
    raise _not_implemented()
