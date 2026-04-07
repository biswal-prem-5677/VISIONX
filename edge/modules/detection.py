"""
VisionX — YOLO Object Detection Module
=========================================
Modular object detection using Ultralytics YOLOv8.
Supports multiple model sizes and configurable class filtering.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import numpy as np
from loguru import logger

from shared.constants import COCO_CLASSES, DEFAULT_CONFIDENCE_THRESHOLD, DEFAULT_NMS_THRESHOLD
from shared.models import BoundingBox, Detection


class Detector:
    """
    YOLO-based object detector.
    
    Uses Ultralytics YOLOv8 for inference. Supports:
        - Multiple model sizes: yolov8n/s/m/l/x
        - Class filtering (detect only specific objects)
        - Configurable confidence and NMS thresholds
        - ONNX / TensorRT backends
    """

    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        confidence: float = DEFAULT_CONFIDENCE_THRESHOLD,
        nms_threshold: float = DEFAULT_NMS_THRESHOLD,
        target_classes: Optional[list[str]] = None,
        device: str = "auto",
    ):
        self.model_path = model_path
        self.confidence = confidence
        self.nms_threshold = nms_threshold
        self.target_classes = target_classes
        self.device = device

        self._model = None
        self._class_names: list[str] = COCO_CLASSES
        self._target_class_ids: Optional[list[int]] = None
        self._is_loaded = False

        # Stats
        self._total_inferences = 0
        self._total_time_ms = 0.0

    def load(self) -> None:
        """Load the YOLO model into memory."""
        try:
            from ultralytics import YOLO

            logger.info(f"Loading YOLO model: {self.model_path}")
            self._model = YOLO(self.model_path)

            # Get class names from model
            if hasattr(self._model, "names"):
                self._class_names = list(self._model.names.values())

            # Resolve target class IDs
            if self.target_classes:
                self._target_class_ids = [
                    i for i, name in enumerate(self._class_names)
                    if name in self.target_classes
                ]
                logger.info(f"Filtering to classes: {self.target_classes} (IDs: {self._target_class_ids})")

            self._is_loaded = True
            logger.info(f"Model loaded: {self.model_path} ({len(self._class_names)} classes)")

        except ImportError:
            logger.error("ultralytics not installed. Run: pip install ultralytics")
            raise
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def detect(self, frame: np.ndarray) -> list[Detection]:
        """
        Run object detection on a single frame.
        
        Args:
            frame: BGR image (numpy array)
            
        Returns:
            List of Detection objects
        """
        if not self._is_loaded:
            self.load()

        start = time.perf_counter()

        # Run inference
        results = self._model(
            frame,
            conf=self.confidence,
            iou=self.nms_threshold,
            classes=self._target_class_ids,
            verbose=False,
        )

        elapsed_ms = (time.perf_counter() - start) * 1000
        self._total_inferences += 1
        self._total_time_ms += elapsed_ms

        # Parse results
        detections: list[Detection] = []

        if results and len(results) > 0:
            result = results[0]
            if result.boxes is not None:
                boxes = result.boxes
                for i in range(len(boxes)):
                    x1, y1, x2, y2 = boxes.xyxy[i].cpu().numpy()
                    conf = float(boxes.conf[i].cpu().numpy())
                    cls_id = int(boxes.cls[i].cpu().numpy())
                    cls_name = self._class_names[cls_id] if cls_id < len(self._class_names) else f"class_{cls_id}"

                    detections.append(Detection(
                        class_id=cls_id,
                        class_name=cls_name,
                        confidence=round(conf, 3),
                        bbox=BoundingBox(
                            x1=float(x1),
                            y1=float(y1),
                            x2=float(x2),
                            y2=float(y2),
                        ),
                    ))

        return detections

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    @property
    def avg_inference_ms(self) -> float:
        if self._total_inferences == 0:
            return 0.0
        return self._total_time_ms / self._total_inferences

    def get_stats(self) -> dict:
        return {
            "model": self.model_path,
            "is_loaded": self._is_loaded,
            "total_inferences": self._total_inferences,
            "avg_inference_ms": round(self.avg_inference_ms, 2),
            "confidence_threshold": self.confidence,
            "target_classes": self.target_classes,
        }

    def update_confidence(self, confidence: float) -> None:
        """Update confidence threshold at runtime."""
        self.confidence = max(0.0, min(1.0, confidence))
        logger.info(f"Confidence threshold updated to {self.confidence}")

    def update_target_classes(self, classes: Optional[list[str]]) -> None:
        """Update target class filter at runtime."""
        self.target_classes = classes
        if classes:
            self._target_class_ids = [
                i for i, name in enumerate(self._class_names)
                if name in classes
            ]
        else:
            self._target_class_ids = None
        logger.info(f"Target classes updated: {classes}")
