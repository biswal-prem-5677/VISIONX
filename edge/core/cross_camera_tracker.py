"""
VisionX — Cross-Camera Tracker
========================================
Maintains shared identity graph across multiple cameras.
Re-identifies objects/persons across different views using appearance features.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

import numpy as np
from loguru import logger


@dataclass
class GlobalIdentity:
    """A unique entity tracked across multiple cameras."""
    global_id: str = field(default_factory=lambda: str(uuid4()))
    label: str = "person"
    appearance_features: Optional[np.ndarray] = None
    sightings: list[dict] = field(default_factory=list)
    first_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    total_sightings: int = 0
    confidence: float = 0.0
    metadata: dict = field(default_factory=dict)


class CrossCameraTracker:
    """
    Cross-camera re-identification and tracking.

    Architecture:
    - Each camera produces local track IDs
    - This tracker merges local IDs into global identities
    - Uses cosine similarity on appearance embeddings for matching
    - Maintains a gallery of known identities
    - Supports handoff detection (person moving between camera FOVs)
    """

    def __init__(
        self,
        similarity_threshold: float = 0.7,
        max_gallery_size: int = 1000,
        identity_timeout_seconds: float = 300.0,
        feature_dim: int = 128,
    ):
        self.similarity_threshold = similarity_threshold
        self.max_gallery_size = max_gallery_size
        self.identity_timeout = identity_timeout_seconds
        self.feature_dim = feature_dim

        self._gallery: dict[str, GlobalIdentity] = {}
        self._camera_to_global: dict[str, dict[str, str]] = {}
        self._handoff_log: list[dict] = []

        logger.info(
            f"CrossCameraTracker initialized "
            f"(threshold={similarity_threshold}, gallery_max={max_gallery_size}, "
            f"timeout={identity_timeout_seconds}s)"
        )

    def update(
        self,
        camera_id: str,
        local_tracks: list[dict],
    ) -> list[dict]:
        """
        Update with tracks from a single camera.

        Args:
            camera_id: Source camera ID
            local_tracks: List of dicts with 'track_id', 'label', 'bbox', 'features' (optional)

        Returns:
            List of tracks with added 'global_id' field
        """
        if camera_id not in self._camera_to_global:
            self._camera_to_global[camera_id] = {}

        mapping = self._camera_to_global[camera_id]
        results = []

        for track in local_tracks:
            local_id = str(track.get("track_id", ""))
            features = track.get("features")
            label = track.get("label", "person")

            if local_id in mapping:
                global_id = mapping[local_id]
                identity = self._gallery.get(global_id)
                if identity:
                    self._update_identity(identity, camera_id, track)
                    track["global_id"] = global_id
                    results.append(track)
                    continue

            # Try to match with existing gallery
            global_id = self._match_identity(features, label)

            if global_id:
                mapping[local_id] = global_id
                identity = self._gallery[global_id]
                self._update_identity(identity, camera_id, track)

                # Detect handoff
                prev_cameras = set(s["camera_id"] for s in identity.sightings[-10:])
                if camera_id not in prev_cameras and len(prev_cameras) > 0:
                    self._log_handoff(global_id, list(prev_cameras)[-1], camera_id)
            else:
                # New identity
                global_id = self._create_identity(label, features, camera_id, track)
                mapping[local_id] = global_id

            track["global_id"] = global_id
            results.append(track)

        self._purge_stale()
        return results

    def get_identity(self, global_id: str) -> Optional[GlobalIdentity]:
        """Get a global identity by ID."""
        return self._gallery.get(global_id)

    def get_active_identities(self) -> list[GlobalIdentity]:
        """Get all currently active identities."""
        now = datetime.now(timezone.utc)
        return [
            i for i in self._gallery.values()
            if (now - i.last_seen).total_seconds() < self.identity_timeout
        ]

    def get_identity_trail(self, global_id: str) -> list[dict]:
        """Get the camera trail for an identity (which cameras, when)."""
        identity = self._gallery.get(global_id)
        if not identity:
            return []
        return identity.sightings

    def get_handoff_log(self, limit: int = 50) -> list[dict]:
        """Get recent camera handoff events."""
        return self._handoff_log[-limit:]

    def get_stats(self) -> dict:
        """Get tracker statistics."""
        active = self.get_active_identities()
        return {
            "gallery_size": len(self._gallery),
            "active_identities": len(active),
            "cameras_tracked": len(self._camera_to_global),
            "total_handoffs": len(self._handoff_log),
            "avg_sightings": round(
                sum(i.total_sightings for i in active) / max(len(active), 1), 1
            ),
        }

    # ─── Internal ────────────────────────────────────────────────────────

    def _match_identity(
        self, features: Optional[np.ndarray], label: str
    ) -> Optional[str]:
        """Find matching identity in gallery using cosine similarity."""
        if features is None:
            return None

        best_match: Optional[str] = None
        best_score = 0.0

        for gid, identity in self._gallery.items():
            if identity.label != label:
                continue
            if identity.appearance_features is None:
                continue

            score = self._cosine_similarity(features, identity.appearance_features)
            if score > self.similarity_threshold and score > best_score:
                best_score = score
                best_match = gid

        return best_match

    def _create_identity(
        self, label: str, features: Optional[np.ndarray],
        camera_id: str, track: dict,
    ) -> str:
        """Create a new global identity."""
        identity = GlobalIdentity(
            label=label,
            appearance_features=features,
        )
        self._update_identity(identity, camera_id, track)
        self._gallery[identity.global_id] = identity

        # Evict oldest if gallery full
        if len(self._gallery) > self.max_gallery_size:
            oldest = min(self._gallery.values(), key=lambda i: i.last_seen)
            del self._gallery[oldest.global_id]

        return identity.global_id

    def _update_identity(
        self, identity: GlobalIdentity, camera_id: str, track: dict
    ) -> None:
        """Update an existing identity with new sighting."""
        now = datetime.now(timezone.utc)
        identity.last_seen = now
        identity.total_sightings += 1
        identity.sightings.append({
            "camera_id": camera_id,
            "track_id": track.get("track_id"),
            "bbox": track.get("bbox"),
            "timestamp": now.isoformat(),
        })
        # Keep last 100 sightings
        if len(identity.sightings) > 100:
            identity.sightings = identity.sightings[-100:]

        # Update appearance features (exponential moving average)
        new_features = track.get("features")
        if new_features is not None and identity.appearance_features is not None:
            alpha = 0.1
            identity.appearance_features = (
                alpha * new_features + (1 - alpha) * identity.appearance_features
            )

    def _log_handoff(self, global_id: str, from_camera: str, to_camera: str) -> None:
        """Log a camera handoff event."""
        entry = {
            "global_id": global_id,
            "from_camera": from_camera,
            "to_camera": to_camera,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._handoff_log.append(entry)
        logger.info(
            f"Handoff: {global_id[:8]} moved {from_camera[:8]} → {to_camera[:8]}"
        )

    def _purge_stale(self) -> None:
        """Remove identities not seen within timeout."""
        now = datetime.now(timezone.utc)
        stale = [
            gid for gid, i in self._gallery.items()
            if (now - i.last_seen).total_seconds() > self.identity_timeout * 2
        ]
        for gid in stale:
            del self._gallery[gid]

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two feature vectors."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
