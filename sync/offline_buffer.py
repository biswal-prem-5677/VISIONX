"""
VisionX — Offline Buffer
========================================
Durable event queue for offline-first operation.
Buffers events locally when cloud is unreachable, drains on reconnect.
Implements WAL-style persistence for crash safety.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

from loguru import logger
from pydantic import BaseModel, Field


class BufferedEvent(BaseModel):
    """A single buffered event awaiting sync."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    payload: dict = Field(default_factory=dict)
    priority: int = 5  # 1=critical, 5=normal, 10=low
    retry_count: int = 0
    max_retries: int = 10
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None


class OfflineBuffer:
    """
    Durable offline event buffer.

    Design:
    - Events written to in-memory queue + optional WAL file
    - Priority queue: critical events sync first
    - TTL support: events expire after configurable time
    - Backpressure: limits max buffer size to prevent OOM
    - Drain on reconnect: push all pending events to cloud
    """

    def __init__(
        self,
        max_buffer_size: int = 10_000,
        wal_path: str = "",
        auto_persist: bool = True,
    ):
        self.max_buffer_size = max_buffer_size
        self.wal_path = wal_path
        self.auto_persist = auto_persist

        self._buffer: list[BufferedEvent] = []
        self._is_online = True
        self._total_buffered = 0
        self._total_drained = 0
        self._total_dropped = 0
        self._total_expired = 0

        # Restore from WAL if exists
        if wal_path and os.path.exists(wal_path):
            self._restore_from_wal()

        logger.info(
            f"OfflineBuffer initialized "
            f"(max={max_buffer_size}, wal={'enabled' if wal_path else 'disabled'})"
        )

    # ─── Buffer Operations ───────────────────────────────────────────────

    def push(self, event_type: str, payload: dict, priority: int = 5) -> Optional[BufferedEvent]:
        """
        Add event to buffer.
        Returns the buffered event or None if dropped (buffer full).
        """
        # Backpressure: drop low-priority events when buffer is full
        if len(self._buffer) >= self.max_buffer_size:
            if priority > 3:
                self._total_dropped += 1
                logger.warning(
                    f"Buffer full ({self.max_buffer_size}), dropping low-priority event"
                )
                return None
            else:
                # Drop oldest low-priority event to make room
                self._evict_lowest_priority()

        event = BufferedEvent(
            event_type=event_type,
            payload=payload,
            priority=priority,
        )
        self._buffer.append(event)
        self._total_buffered += 1

        # Write to WAL
        if self.auto_persist and self.wal_path:
            self._append_to_wal(event)

        logger.debug(f"Buffered: {event_type} (priority={priority}, queue={len(self._buffer)})")
        return event

    def drain(self, batch_size: int = 50) -> list[BufferedEvent]:
        """
        Remove and return a batch of events, highest priority first.
        Used by sync engine to push events to cloud.
        """
        # Remove expired events first
        self._purge_expired()

        # Sort by priority (lower = higher priority)
        self._buffer.sort(key=lambda e: (e.priority, e.created_at.timestamp()))

        batch = self._buffer[:batch_size]
        self._buffer = self._buffer[batch_size:]
        self._total_drained += len(batch)

        if batch:
            logger.info(f"Drained {len(batch)} events from buffer ({len(self._buffer)} remaining)")

        # Update WAL
        if self.auto_persist and self.wal_path:
            self._write_wal()

        return batch

    def peek(self, count: int = 10) -> list[BufferedEvent]:
        """Preview next events without removing them."""
        sorted_buffer = sorted(self._buffer, key=lambda e: (e.priority, e.created_at.timestamp()))
        return sorted_buffer[:count]

    def requeue(self, events: list[BufferedEvent]) -> int:
        """Put failed events back into the buffer with incremented retry count."""
        requeued = 0
        for event in events:
            event.retry_count += 1
            if event.retry_count < event.max_retries:
                self._buffer.append(event)
                requeued += 1
            else:
                self._total_dropped += 1
                logger.warning(f"Event {event.id[:8]} exceeded max retries, dropping")
        return requeued

    # ─── Status ──────────────────────────────────────────────────────────

    @property
    def size(self) -> int:
        return len(self._buffer)

    @property
    def is_empty(self) -> bool:
        return len(self._buffer) == 0

    def set_online(self, is_online: bool) -> None:
        """Update connectivity status."""
        if is_online and not self._is_online:
            logger.info(f"Back online — {len(self._buffer)} events pending sync")
        elif not is_online and self._is_online:
            logger.warning("Gone offline — buffering events locally")
        self._is_online = is_online

    def get_stats(self) -> dict:
        """Get buffer statistics."""
        return {
            "size": len(self._buffer),
            "max_size": self.max_buffer_size,
            "utilization_pct": round(len(self._buffer) / max(self.max_buffer_size, 1) * 100, 1),
            "is_online": self._is_online,
            "total_buffered": self._total_buffered,
            "total_drained": self._total_drained,
            "total_dropped": self._total_dropped,
            "total_expired": self._total_expired,
            "priority_breakdown": self._get_priority_breakdown(),
        }

    def clear(self) -> int:
        """Clear all buffered events. Returns count cleared."""
        count = len(self._buffer)
        self._buffer.clear()
        if self.wal_path:
            self._write_wal()
        logger.info(f"Buffer cleared ({count} events)")
        return count

    # ─── Internal ────────────────────────────────────────────────────────

    def _evict_lowest_priority(self) -> None:
        """Remove the lowest priority (highest number) event."""
        if not self._buffer:
            return
        worst = max(self._buffer, key=lambda e: (e.priority, e.created_at.timestamp()))
        self._buffer.remove(worst)
        self._total_dropped += 1

    def _purge_expired(self) -> None:
        """Remove events past their TTL."""
        now = datetime.now(timezone.utc)
        before = len(self._buffer)
        self._buffer = [
            e for e in self._buffer
            if not e.expires_at or e.expires_at > now
        ]
        expired = before - len(self._buffer)
        if expired:
            self._total_expired += expired
            logger.debug(f"Purged {expired} expired events")

    def _get_priority_breakdown(self) -> dict:
        """Count events by priority level."""
        breakdown: dict[int, int] = {}
        for event in self._buffer:
            breakdown[event.priority] = breakdown.get(event.priority, 0) + 1
        return breakdown

    def _append_to_wal(self, event: BufferedEvent) -> None:
        """Append a single event to the WAL file."""
        try:
            Path(self.wal_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.wal_path, "a") as f:
                f.write(event.model_dump_json() + "\n")
        except Exception as e:
            logger.error(f"WAL append failed: {e}")

    def _write_wal(self) -> None:
        """Rewrite the entire WAL file (after drain/clear)."""
        try:
            Path(self.wal_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.wal_path, "w") as f:
                for event in self._buffer:
                    f.write(event.model_dump_json() + "\n")
        except Exception as e:
            logger.error(f"WAL write failed: {e}")

    def _restore_from_wal(self) -> None:
        """Restore buffer from WAL file on startup."""
        try:
            count = 0
            with open(self.wal_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        event = BufferedEvent.model_validate_json(line)
                        self._buffer.append(event)
                        count += 1
            logger.info(f"Restored {count} events from WAL")
        except Exception as e:
            logger.error(f"WAL restore failed: {e}")
