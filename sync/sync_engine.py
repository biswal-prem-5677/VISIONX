"""
VisionX — Sync Engine
========================================
Bidirectional Edge ↔ Cloud synchronization.
Handles event sync, config sync, model sync, and state reconciliation.
Supports offline-first: buffers when disconnected, drains on reconnect.
"""

from __future__ import annotations

import asyncio
import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from loguru import logger
from pydantic import BaseModel, Field


class SyncDirection(str, Enum):
    EDGE_TO_CLOUD = "edge_to_cloud"
    CLOUD_TO_EDGE = "cloud_to_edge"
    BIDIRECTIONAL = "bidirectional"


class SyncStatus(str, Enum):
    IDLE = "idle"
    SYNCING = "syncing"
    OFFLINE = "offline"
    ERROR = "error"
    CONFLICT = "conflict"


class SyncRecord(BaseModel):
    """A single sync operation record."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    entity_type: str  # event, config, model, device_state
    entity_id: str
    direction: SyncDirection
    checksum: str = ""
    payload: dict = Field(default_factory=dict)
    status: str = "pending"  # pending, synced, failed, conflict
    retry_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    synced_at: Optional[datetime] = None


class ConflictResolution(str, Enum):
    """Strategy when edge and cloud have conflicting data."""
    CLOUD_WINS = "cloud_wins"
    EDGE_WINS = "edge_wins"
    LAST_WRITE_WINS = "last_write_wins"
    MANUAL = "manual"


class SyncEngine:
    """
    Edge ↔ Cloud bidirectional synchronization engine.

    Architecture:
    - Uses an outbox pattern: events are written to a local queue first
    - Background worker drains the queue and pushes to cloud
    - Cloud pushes config/model updates down to edge
    - Conflict resolution via configurable strategy
    """

    def __init__(
        self,
        cloud_url: str = "",
        device_id: str = "",
        sync_interval_seconds: float = 5.0,
        batch_size: int = 50,
        max_retries: int = 5,
        conflict_strategy: ConflictResolution = ConflictResolution.LAST_WRITE_WINS,
    ):
        self.cloud_url = cloud_url
        self.device_id = device_id or str(uuid4())
        self.sync_interval = sync_interval_seconds
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.conflict_strategy = conflict_strategy

        self._status = SyncStatus.IDLE
        self._outbox: list[SyncRecord] = []
        self._inbox: list[SyncRecord] = []
        self._conflicts: list[SyncRecord] = []
        self._sync_log: list[dict] = []
        self._running = False
        self._last_sync_at: Optional[datetime] = None
        self._total_synced = 0
        self._total_failed = 0

        logger.info(
            f"SyncEngine initialized "
            f"(device={self.device_id[:8]}, interval={sync_interval_seconds}s, "
            f"batch={batch_size}, conflict={conflict_strategy.value})"
        )

    @property
    def status(self) -> SyncStatus:
        return self._status

    @property
    def pending_count(self) -> int:
        return len(self._outbox)

    @property
    def conflict_count(self) -> int:
        return len(self._conflicts)

    # ─── Outbound (Edge → Cloud) ─────────────────────────────────────────

    def enqueue(self, entity_type: str, entity_id: str, payload: dict) -> SyncRecord:
        """Add an item to the sync outbox."""
        checksum = hashlib.sha256(str(payload).encode()).hexdigest()[:16]
        record = SyncRecord(
            entity_type=entity_type,
            entity_id=entity_id,
            direction=SyncDirection.EDGE_TO_CLOUD,
            checksum=checksum,
            payload=payload,
        )
        self._outbox.append(record)
        logger.debug(f"Enqueued sync: {entity_type}/{entity_id} ({checksum})")
        return record

    async def flush(self) -> dict:
        """
        Push all pending outbox items to cloud.
        Returns summary of results.
        """
        if not self._outbox:
            return {"synced": 0, "failed": 0, "remaining": 0}

        self._status = SyncStatus.SYNCING
        batch = self._outbox[:self.batch_size]
        synced = 0
        failed = 0

        for record in batch:
            try:
                success = await self._push_to_cloud(record)
                if success:
                    record.status = "synced"
                    record.synced_at = datetime.now(timezone.utc)
                    synced += 1
                    self._total_synced += 1
                else:
                    record.retry_count += 1
                    if record.retry_count >= self.max_retries:
                        record.status = "failed"
                        failed += 1
                        self._total_failed += 1
                    else:
                        record.status = "pending"
            except Exception as e:
                logger.error(f"Sync failed for {record.entity_id}: {e}")
                record.retry_count += 1
                failed += 1

        # Remove completed/failed records from outbox
        self._outbox = [r for r in self._outbox if r.status == "pending"]
        self._last_sync_at = datetime.now(timezone.utc)
        self._status = SyncStatus.IDLE

        self._sync_log.append({
            "timestamp": self._last_sync_at.isoformat(),
            "synced": synced,
            "failed": failed,
            "remaining": len(self._outbox),
        })

        logger.info(f"Sync flush: {synced} synced, {failed} failed, {len(self._outbox)} remaining")
        return {"synced": synced, "failed": failed, "remaining": len(self._outbox)}

    # ─── Inbound (Cloud → Edge) ──────────────────────────────────────────

    async def pull(self) -> list[SyncRecord]:
        """Pull updates from cloud to edge."""
        try:
            records = await self._pull_from_cloud()
            self._inbox.extend(records)
            logger.info(f"Pulled {len(records)} records from cloud")
            return records
        except Exception as e:
            logger.error(f"Pull failed: {e}")
            self._status = SyncStatus.OFFLINE
            return []

    async def apply_inbox(self) -> int:
        """Apply all inbox items to local state."""
        applied = 0
        for record in self._inbox:
            try:
                conflict = await self._check_conflict(record)
                if conflict:
                    resolved = await self._resolve_conflict(record, conflict)
                    if not resolved:
                        self._conflicts.append(record)
                        continue

                await self._apply_locally(record)
                record.status = "synced"
                applied += 1
            except Exception as e:
                logger.error(f"Apply failed for {record.entity_id}: {e}")

        self._inbox = [r for r in self._inbox if r.status != "synced"]
        logger.info(f"Applied {applied} inbox records")
        return applied

    # ─── Sync Loop ───────────────────────────────────────────────────────

    async def start(self) -> None:
        """Start the background sync loop."""
        self._running = True
        logger.info("Sync loop started")

        while self._running:
            try:
                await self.flush()
                await self.pull()
                await self.apply_inbox()
            except Exception as e:
                logger.error(f"Sync loop error: {e}")
                self._status = SyncStatus.ERROR

            await asyncio.sleep(self.sync_interval)

    def stop(self) -> None:
        """Stop the sync loop."""
        self._running = False
        logger.info("Sync loop stopped")

    # ─── Status / Metrics ────────────────────────────────────────────────

    def get_status(self) -> dict:
        """Get current sync status."""
        return {
            "status": self._status.value,
            "device_id": self.device_id,
            "pending": len(self._outbox),
            "inbox": len(self._inbox),
            "conflicts": len(self._conflicts),
            "total_synced": self._total_synced,
            "total_failed": self._total_failed,
            "last_sync_at": self._last_sync_at.isoformat() if self._last_sync_at else None,
            "recent_log": self._sync_log[-10:],
        }

    # ─── Internal Methods ────────────────────────────────────────────────

    async def _push_to_cloud(self, record: SyncRecord) -> bool:
        """Push a single record to cloud API. Override for real HTTP."""
        # In production: POST to self.cloud_url/api/sync/push
        logger.debug(f"Push → cloud: {record.entity_type}/{record.entity_id}")
        return True

    async def _pull_from_cloud(self) -> list[SyncRecord]:
        """Pull new records from cloud. Override for real HTTP."""
        # In production: GET from self.cloud_url/api/sync/pull?device_id={}&since={}
        return []

    async def _check_conflict(self, record: SyncRecord) -> Optional[SyncRecord]:
        """Check if an incoming record conflicts with local state."""
        # In production: compare checksums with local DB
        return None

    async def _resolve_conflict(
        self, incoming: SyncRecord, local: SyncRecord
    ) -> bool:
        """Resolve a conflict between incoming and local record."""
        if self.conflict_strategy == ConflictResolution.CLOUD_WINS:
            return True  # Accept incoming
        elif self.conflict_strategy == ConflictResolution.EDGE_WINS:
            return False  # Reject incoming
        elif self.conflict_strategy == ConflictResolution.LAST_WRITE_WINS:
            return incoming.created_at > local.created_at
        else:
            # Manual — add to conflict queue for human resolution
            return False

    async def _apply_locally(self, record: SyncRecord) -> None:
        """Apply a synced record to local state. Override for real DB."""
        logger.debug(f"Apply locally: {record.entity_type}/{record.entity_id}")
