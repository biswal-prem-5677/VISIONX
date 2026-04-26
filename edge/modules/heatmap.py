"""
VisionX — Heatmap Module
========================================
Generate spatial heatmaps from detection data.
"""

from __future__ import annotations

import numpy as np
from loguru import logger


class HeatmapEngine:
    """Generate spatial heatmaps from detection positions."""

    def __init__(self, width: int = 640, height: int = 480, decay: float = 0.98):
        self.width = width
        self.height = height
        self.decay = decay
        self._heatmap = np.zeros((height, width), dtype=np.float32)
        logger.info(f"HeatmapEngine initialized ({width}x{height}, decay={decay})")

    def update(self, detections: list[dict]) -> np.ndarray:
        """
        Update heatmap with new detections.

        Args:
            detections: List of dicts with 'x', 'y', 'w', 'h' keys (bbox center + size)

        Returns:
            Updated heatmap as numpy array
        """
        # Apply decay to previous frame
        self._heatmap *= self.decay

        # Add heat for each detection
        for det in detections:
            cx = int(det.get("x", 0))
            cy = int(det.get("y", 0))
            w = int(det.get("w", 40))
            h = int(det.get("h", 40))

            # Clamp to bounds
            x1 = max(0, cx - w // 2)
            y1 = max(0, cy - h // 2)
            x2 = min(self.width, cx + w // 2)
            y2 = min(self.height, cy + h // 2)

            self._heatmap[y1:y2, x1:x2] += 1.0

        # Normalize to [0, 1]
        max_val = self._heatmap.max()
        if max_val > 0:
            return self._heatmap / max_val
        return self._heatmap

    def get_heatmap(self) -> np.ndarray:
        """Get current heatmap."""
        return self._heatmap

    def get_hotspots(self, threshold: float = 0.7) -> list[dict]:
        """Get coordinates of hot regions above threshold."""
        normalized = self._heatmap / max(self._heatmap.max(), 1e-6)
        hotspots = []

        # Simple grid-based hotspot detection
        grid_size = 32
        for y in range(0, self.height, grid_size):
            for x in range(0, self.width, grid_size):
                region = normalized[y : y + grid_size, x : x + grid_size]
                avg = float(region.mean())
                if avg > threshold:
                    hotspots.append({"x": x, "y": y, "intensity": round(avg, 3)})

        return hotspots

    def reset(self) -> None:
        """Reset heatmap to zero."""
        self._heatmap = np.zeros((self.height, self.width), dtype=np.float32)
        logger.debug("Heatmap reset")
