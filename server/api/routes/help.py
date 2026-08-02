"""
VisionX — Help API Routes
=============================
Help center, tickets, and knowledge base endpoints.

Authorization
-------------
Knowledge-base reads (``/articles``, ``/search``) are **deliberately public** —
help content must be readable before signup. Ticket routes require an
authenticated caller and are scoped to that caller: ``GET /tickets`` previously
returned every ticket from every user, including their free-text descriptions.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from server.api.dependencies import CurrentUser, get_current_user

router = APIRouter(prefix="/help", tags=["help"])


class HelpArticle(BaseModel):
    """Help knowledge base article."""
    id: str
    title: str
    content: str
    category: str
    read_time: str = "3 min"


class SupportTicket(BaseModel):
    """Support ticket submission."""
    subject: str
    description: str
    priority: str = "normal"  # low, normal, high, urgent


class TicketResponse(BaseModel):
    """Ticket response."""
    ticket_id: str
    status: str
    created_at: str


# Mock data
_articles = [
    HelpArticle(id="1", title="Getting Started with VisionX", content="Welcome to VisionX...", category="Getting Started"),
    HelpArticle(id="2", title="Adding Cameras", content="To add a camera source...", category="Setup"),
    HelpArticle(id="3", title="Creating Automation Rules", content="Automation rules follow an IF-THEN pattern...", category="Automation"),
    HelpArticle(id="4", title="Understanding Detection Classes", content="VisionX uses YOLOv8...", category="AI"),
    HelpArticle(id="5", title="Billing & Plans", content="VisionX offers Free, Pro, and Enterprise plans...", category="Billing"),
]

_tickets: list[dict] = []


@router.get("/articles", response_model=list[HelpArticle])
async def list_articles(category: Optional[str] = None):
    """List all help articles, optionally filtered by category."""
    if category:
        return [a for a in _articles if a.category.lower() == category.lower()]
    return _articles


@router.get("/articles/{article_id}", response_model=HelpArticle)
async def get_article(article_id: str):
    """Get a specific help article."""
    for a in _articles:
        if a.id == article_id:
            return a
    raise HTTPException(status_code=404, detail="Article not found")


@router.get("/search")
async def search_articles(q: str):
    """Search help articles."""
    query = q.lower()
    results = [a for a in _articles if query in a.title.lower() or query in a.content.lower()]
    return results


@router.post("/tickets", response_model=TicketResponse)
async def create_ticket(
    ticket: SupportTicket,
    user: CurrentUser = Depends(get_current_user),
):
    """Submit a support ticket."""
    import time
    import uuid

    # Time-derived IDs collide when two tickets are filed in the same second and
    # are trivially guessable. A random suffix removes both problems.
    ticket_id = f"VX-{int(time.time())}-{uuid.uuid4().hex[:6]}"
    created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    _tickets.append({
        "ticket_id": ticket_id,
        "user_id": user.user_id,
        "subject": ticket.subject,
        "description": ticket.description,
        "priority": ticket.priority,
        "status": "open",
        "created_at": created_at,
    })
    return TicketResponse(
        ticket_id=ticket_id,
        status="open",
        created_at=created_at,
    )


@router.get("/tickets")
async def list_tickets(user: CurrentUser = Depends(get_current_user)):
    """List the caller's own support tickets."""
    return [t for t in _tickets if t.get("user_id") == user.user_id]
