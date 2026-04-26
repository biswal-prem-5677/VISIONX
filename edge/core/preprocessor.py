"""
VisionX — Image Preprocessor
==============================
Image enhancement pipeline applied before AI inference.
Includes CLAHE, noise reduction, edge detection, and resizing.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import cv2
import numpy as np
from loguru import logger


class PreprocessStep(str, Enum):
    RESIZE = "resize"
    CLAHE = "clahe"
    DENOISE = "denoise"
    EDGE = "edge"
    NORMALIZE = "normalize"
    GRAYSCALE = "grayscale"


@dataclass
class PreprocessConfig:
    """Configuration for preprocessing steps."""
    target_size: Optional[tuple[int, int]] = None  # (width, height)
    clahe_clip_limit: float = 2.0
    clahe_grid_size: tuple[int, int] = (8, 8)
    denoise_strength: int = 10
    steps: list[str] = None

    def __post_init__(self):
        if self.steps is None:
            # Default pipeline: just resize
            self.steps = [PreprocessStep.RESIZE]


class Preprocessor:
    """
    Image preprocessing engine.

    Applies a configurable pipeline of enhancement steps
    to each frame before AI inference.

    Available steps:
        - resize: Scale to target input size
        - clahe: Contrast Limited Adaptive Histogram Equalization
        - denoise: Non-local means denoising
        - edge: Canny edge detection
        - normalize: Pixel value normalization (0-1)
        - grayscale: Convert to grayscale
    """

    def __init__(self, config: Optional[PreprocessConfig] = None):
        self.config = config or PreprocessConfig()
        self._clahe = cv2.createCLAHE(
            clipLimit=self.config.clahe_clip_limit,
            tileGridSize=self.config.clahe_grid_size,
        )
        logger.info(f"Preprocessor initialized with steps: {self.config.steps}")

    def process(self, frame: np.ndarray) -> np.ndarray:
        """
        Apply the full preprocessing pipeline to a frame.

        Args:
            frame: BGR image (numpy array)

        Returns:
            Processed BGR image
        """
        result = frame.copy()

        for step in self.config.steps:
            if step == PreprocessStep.RESIZE:
                result = self._resize(result)
            elif step == PreprocessStep.CLAHE:
                result = self._apply_clahe(result)
            elif step == PreprocessStep.DENOISE:
                result = self._denoise(result)
            elif step == PreprocessStep.EDGE:
                result = self._edge_detect(result)
            elif step == PreprocessStep.NORMALIZE:
                result = self._normalize(result)
            elif step == PreprocessStep.GRAYSCALE:
                result = self._grayscale(result)

        return result

    def _resize(self, frame: np.ndarray) -> np.ndarray:
        """Resize frame to target size while maintaining aspect ratio."""
        if self.config.target_size is None:
            return frame

        target_w, target_h = self.config.target_size
        h, w = frame.shape[:2]

        if w == target_w and h == target_h:
            return frame

        # Calculate scale to fit within target while maintaining aspect ratio
        scale = min(target_w / w, target_h / h)
        new_w, new_h = int(w * scale), int(h * scale)

        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

        # Pad to exact target size if needed
        if new_w != target_w or new_h != target_h:
            canvas = np.zeros((target_h, target_w, 3), dtype=np.uint8)
            y_offset = (target_h - new_h) // 2
            x_offset = (target_w - new_w) // 2
            canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized
            return canvas

        return resized

    def _apply_clahe(self, frame: np.ndarray) -> np.ndarray:
        """Apply CLAHE for contrast enhancement."""
        if len(frame.shape) == 2:
            return self._clahe.apply(frame)

        # Convert to LAB, apply CLAHE to L channel
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        channels = list(cv2.split(lab))
        channels[0] = self._clahe.apply(channels[0])
        lab = cv2.merge(channels)
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    def _denoise(self, frame: np.ndarray) -> np.ndarray:
        """Apply non-local means denoising."""
        return cv2.fastNlMeansDenoisingColored(
            frame,
            None,
            h=self.config.denoise_strength,
            hForColorComponents=self.config.denoise_strength,
            templateWindowSize=7,
            searchWindowSize=21,
        )

    def _edge_detect(self, frame: np.ndarray) -> np.ndarray:
        """Apply Canny edge detection."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

    def _normalize(self, frame: np.ndarray) -> np.ndarray:
        """Normalize pixel values to 0-1 range."""
        return (frame.astype(np.float32) / 255.0 * 255).astype(np.uint8)

    def _grayscale(self, frame: np.ndarray) -> np.ndarray:
        """Convert to grayscale (returns 3-channel gray)."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    def resize_only(self, frame: np.ndarray, size: tuple[int, int]) -> np.ndarray:
        """Quick resize without full pipeline."""
        return cv2.resize(frame, size, interpolation=cv2.INTER_LINEAR)
