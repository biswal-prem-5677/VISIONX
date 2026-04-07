"""
VisionX — OCR Module (Cloud)
================================
Read text from images: number plates, labels, documents.
Uses EasyOCR or Tesseract for text extraction.
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np
from loguru import logger
from pydantic import BaseModel, Field


class OCRResult(BaseModel):
    """Result from OCR processing."""
    text: str
    confidence: float
    bbox: list[list[int]] = Field(default_factory=list)  # [[x1,y1],[x2,y2],...]
    language: str = "en"


class OCRModule:
    """
    Optical Character Recognition module.
    
    Extracts text from images using EasyOCR.
    Runs on cloud for accuracy — too heavy for edge.
    """

    def __init__(self, languages: list[str] | None = None):
        self._languages = languages or ["en"]
        self._reader = None
        self._is_loaded = False

        logger.info(f"OCR Module initialized (languages: {self._languages})")

    def load(self) -> None:
        """Load the OCR model (lazy loading)."""
        if self._is_loaded:
            return

        try:
            import easyocr

            self._reader = easyocr.Reader(self._languages, gpu=True)
            self._is_loaded = True
            logger.info("OCR model loaded (EasyOCR)")
        except ImportError:
            logger.warning(
                "EasyOCR not installed. Install with: pip install easyocr"
            )
        except Exception as e:
            logger.error(f"OCR model load failed: {e}")

    def process(
        self,
        image: np.ndarray,
        min_confidence: float = 0.3,
    ) -> list[OCRResult]:
        """
        Extract text from an image.

        Args:
            image: Input image (BGR numpy array)
            min_confidence: Minimum confidence threshold

        Returns:
            List of OCRResult objects
        """
        if not self._is_loaded:
            self.load()

        if self._reader is None:
            return []

        try:
            results = self._reader.readtext(image)
            ocr_results = []

            for bbox, text, conf in results:
                if conf >= min_confidence:
                    ocr_results.append(
                        OCRResult(
                            text=text,
                            confidence=conf,
                            bbox=[[int(p[0]), int(p[1])] for p in bbox],
                        )
                    )

            logger.debug(f"OCR: {len(ocr_results)} text regions detected")
            return ocr_results

        except Exception as e:
            logger.error(f"OCR processing error: {e}")
            return []

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded
