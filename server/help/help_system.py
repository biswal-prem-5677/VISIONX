"""
VisionX — Help & Support System
===================================
Knowledge base, ticket system, and onboarding.
"""

from __future__ import annotations

import time
from typing import Optional

from loguru import logger
from pydantic import BaseModel, Field


class HelpArticle(BaseModel):
    """A help/knowledge base article."""
    id: str
    title: str
    content: str
    category: str = "general"
    tags: list[str] = Field(default_factory=list)
    views: int = 0


class SupportTicket(BaseModel):
    """A support ticket."""
    id: str = ""
    user_id: str
    subject: str
    description: str
    status: str = "open"  # open, in_progress, resolved, closed
    priority: str = "normal"  # low, normal, high, urgent
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    messages: list[dict[str, str]] = Field(default_factory=list)


class HelpSystem:
    """
    Help and support system.

    Provides:
    - Searchable knowledge base
    - Support ticket management
    - Interactive onboarding
    """

    def __init__(self):
        self._articles: dict[str, HelpArticle] = {}
        self._tickets: dict[str, SupportTicket] = {}
        self._ticket_counter = 0

        # Load default articles
        self._load_defaults()

        logger.info("Help System initialized")

    def _load_defaults(self) -> None:
        """Load default help articles."""
        defaults = [
            HelpArticle(
                id="getting-started",
                title="Getting Started with VisionX",
                content="Welcome to VisionX! Follow these steps to set up your first camera...",
                category="setup",
                tags=["beginner", "setup", "camera"],
            ),
            HelpArticle(
                id="rules-setup",
                title="Setting Up Detection Rules",
                content="Rules define what VisionX should watch for. Example: IF person_count > 5...",
                category="rules",
                tags=["rules", "automation", "alerts"],
            ),
            HelpArticle(
                id="troubleshooting",
                title="Troubleshooting Common Issues",
                content="Camera not connecting? Check firewall settings and ensure RTSP port is open...",
                category="troubleshooting",
                tags=["help", "fix", "camera", "errors"],
            ),
        ]

        for article in defaults:
            self._articles[article.id] = article

    def search_articles(self, query: str) -> list[HelpArticle]:
        """Search knowledge base articles."""
        query_lower = query.lower()
        results = []

        for article in self._articles.values():
            if (
                query_lower in article.title.lower()
                or query_lower in article.content.lower()
                or any(query_lower in tag for tag in article.tags)
            ):
                article.views += 1
                results.append(article)

        return results

    def get_article(self, article_id: str) -> Optional[HelpArticle]:
        """Get a specific article."""
        article = self._articles.get(article_id)
        if article:
            article.views += 1
        return article

    def create_ticket(self, ticket: SupportTicket) -> SupportTicket:
        """Create a support ticket."""
        self._ticket_counter += 1
        ticket.id = f"TICKET-{self._ticket_counter:04d}"
        self._tickets[ticket.id] = ticket

        logger.info(f"Support ticket created: {ticket.id} - {ticket.subject}")
        return ticket

    def update_ticket_status(
        self, ticket_id: str, status: str
    ) -> Optional[SupportTicket]:
        """Update ticket status."""
        ticket = self._tickets.get(ticket_id)
        if ticket:
            ticket.status = status
            ticket.updated_at = time.time()
        return ticket

    def get_user_tickets(self, user_id: str) -> list[SupportTicket]:
        """Get all tickets for a user."""
        return [
            t for t in self._tickets.values()
            if t.user_id == user_id
        ]

    def get_open_tickets(self) -> list[SupportTicket]:
        """Get all open tickets (for admin)."""
        return [
            t for t in self._tickets.values()
            if t.status in ("open", "in_progress")
        ]
