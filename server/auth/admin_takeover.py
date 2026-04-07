"""
VisionX — Admin Takeover (Impersonation)
============================================
Allows super_admins to impersonate users for debugging.
All actions are audit-logged.
"""

from __future__ import annotations

import time
from typing import Optional

from loguru import logger
from pydantic import BaseModel, Field


class TakeoverSession(BaseModel):
    """An admin takeover session."""
    admin_id: str
    target_user_id: str
    started_at: float = Field(default_factory=time.time)
    ended_at: Optional[float] = None
    reason: str = ""
    actions_log: list[str] = Field(default_factory=list)


class AdminTakeover:
    """
    Admin impersonation system.

    Allows super_admins to view the platform as another user.
    Every action taken during impersonation is audit-logged.
    """

    def __init__(self):
        self._active_sessions: dict[str, TakeoverSession] = {}
        self._session_history: list[TakeoverSession] = []

        logger.info("Admin Takeover system initialized")

    def start_session(
        self,
        admin_id: str,
        target_user_id: str,
        admin_role: str,
        reason: str = "",
    ) -> Optional[TakeoverSession]:
        """Start an impersonation session."""
        if admin_role != "super_admin":
            logger.warning(
                f"Takeover denied: {admin_id} (role: {admin_role}) "
                f"tried to impersonate {target_user_id}"
            )
            return None

        session = TakeoverSession(
            admin_id=admin_id,
            target_user_id=target_user_id,
            reason=reason,
        )

        self._active_sessions[admin_id] = session

        logger.warning(
            f"ADMIN TAKEOVER: {admin_id} → {target_user_id} "
            f"(reason: {reason})"
        )

        return session

    def end_session(self, admin_id: str) -> Optional[TakeoverSession]:
        """End an impersonation session."""
        session = self._active_sessions.pop(admin_id, None)
        if session:
            session.ended_at = time.time()
            self._session_history.append(session)

            duration = session.ended_at - session.started_at
            logger.warning(
                f"ADMIN TAKEOVER ENDED: {admin_id} → {session.target_user_id} "
                f"(duration: {duration:.1f}s, actions: {len(session.actions_log)})"
            )

        return session

    def log_action(self, admin_id: str, action: str) -> None:
        """Log an action during impersonation."""
        session = self._active_sessions.get(admin_id)
        if session:
            entry = f"[{time.time():.0f}] {action}"
            session.actions_log.append(entry)

    def is_impersonating(self, admin_id: str) -> Optional[str]:
        """Check if an admin is currently impersonating someone."""
        session = self._active_sessions.get(admin_id)
        return session.target_user_id if session else None

    def get_audit_log(self, limit: int = 100) -> list[TakeoverSession]:
        """Get takeover audit history."""
        return self._session_history[-limit:]
