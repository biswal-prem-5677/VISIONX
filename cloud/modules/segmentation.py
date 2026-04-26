"""
VisionX — Segmentation Module (Cloud)
=========================================
Pixel-level object segmentation using SAM or YOLO-Seg.
Provides precise object boundaries beyond bounding boxes.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
from loguru import logger
from pydantic import BaseModel, Field


class SegmentResult(BaseModel):
    """Result from segmentation processing."""
    class_id: int
    class_name: str
    confidence: float
    bbox: list[int] = Field(default_factory=list)  # [x1, y1, x2, y2]
    mask_area_px: int = 0
    mask_percentage: float = 0.0  # % of frame covered


class SegmentationModule:
    """
    Instance segmentation module.

    Uses YOLO-Seg for simultaneous detection + segmentation.
    Provides pixel-level masks for precise object boundaries.
    Runs on cloud for compute-intensive processing.
    """

    def __init__(self, model_path: str = "yolov8n-seg.pt"):
        self._model_path = model_path
        self._model = None
        self._is_loaded = False

        logger.info(f"Segmentation Module initialized (model: {model_path})")

    def load(self) -> None:
        """Load the segmentation model."""
        if self._is_loaded:
            return

        try:
            from ultralytics import YOLO

            self._model = YOLO(self._model_path)
            self._is_loaded = True
            logger.info(f"Segmentation model loaded: {self._model_path}")
        except ImportError:
            logger.warning(
                "ultralytics not installed. "
                "Install with: pip install ultralytics"
            )
        except Exception as e:
            logger.error(f"Segmentation model load failed: {e}")

    def process(
        self,
        image: np.ndarray,
        confidence: float = 0.5,
        classes: list[int] | None = None,
    ) -> tuple[list[SegmentResult], Optional[np.ndarray]]:
        """
        Run segmentation on an image.

        Args:
            image: Input image (BGR numpy array)
            confidence: Confidence threshold
            classes: Filter to specific class IDs

        Returns:
            Tuple of (results list, combined mask image)
        """
        if not self._is_loaded:
            self.load()

        if self._model is None:
            return [], None

        try:
            results = self._model(
                image,
                conf=confidence,
                classes=classes,
                verbose=False,
            )

            if not results or len(results) == 0:
                return [], None

            result = results[0]
            frame_area = image.shape[0] * image.shape[1]
            segments: list[SegmentResult] = []
            combined_mask = np.zeros(image.shape[:2], dtype=np.uint8)

            if result.masks is not None:
                masks = result.masks.data.cpu().numpy()
                boxes = result.boxes

                for i, (mask, box) in enumerate(zip(masks, boxes)):
                    cls_id = int(box.cls[0])
                    cls_name = result.names[cls_id]
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    # Resize mask to frame size
                    import cv2

                    mask_resized = cv2.resize(
                        mask, (image.shape[1], image.shape[0])
                    )
                    mask_binary = (mask_resized > 0.5).astype(np.uint8)
                    mask_area = int(mask_binary.sum())

                    # Add to combined mask
                    combined_mask = np.maximum(
                        combined_mask, mask_binary * (i + 1)
                    )

                    segments.append(
                        SegmentResult(
                            class_id=cls_id,
                            class_name=cls_name,
                            confidence=conf,
                            bbox=[x1, y1, x2, y2],
                            mask_area_px=mask_area,
                            mask_percentage=round(
                                mask_area / frame_area * 100, 2
                            ),
                        )
                    )

            logger.debug(f"Segmentation: {len(segments)} objects segmented")
            return segments, combined_mask

        except Exception as e:
            logger.error(f"Segmentation error: {e}")
            return [], None

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded
