"""
VisionX — Face Recognition Module (Cloud)
=============================================
Identify and match faces against a database.
Uses face_recognition library (dlib-based).
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np
from loguru import logger
from pydantic import BaseModel, Field


class FaceResult(BaseModel):
    """Result from face recognition."""
    face_id: int
    name: str = "unknown"
    confidence: float = 0.0
    bbox: list[int] = Field(default_factory=list)  # [top, right, bottom, left]
    encoding: Optional[list[float]] = None
    is_match: bool = False


class FaceDatabase:
    """In-memory face database for matching."""

    def __init__(self):
        self._known_encodings: list[np.ndarray] = []
        self._known_names: list[str] = []

    def add_face(self, name: str, encoding: np.ndarray) -> None:
        """Register a face in the database."""
        self._known_encodings.append(encoding)
        self._known_names.append(name)
        logger.info(f"Face registered: {name}")

    def get_count(self) -> int:
        return len(self._known_names)

    @property
    def encodings(self) -> list[np.ndarray]:
        return self._known_encodings

    @property
    def names(self) -> list[str]:
        return self._known_names


class FaceModule:
    """
    Face recognition module.

    Detects faces in images and matches them against a known database.
    Uses face_recognition library (dlib-based).
    Runs on cloud for compute-heavy encoding.
    """

    def __init__(self, tolerance: float = 0.6):
        self._tolerance = tolerance
        self._database = FaceDatabase()
        self._is_loaded = False
        self._face_recognition = None

        logger.info(f"Face Module initialized (tolerance: {tolerance})")

    def load(self) -> None:
        """Load the face recognition library."""
        if self._is_loaded:
            return

        try:
            import face_recognition

            self._face_recognition = face_recognition
            self._is_loaded = True
            logger.info("Face recognition model loaded")
        except ImportError:
            logger.warning(
                "face_recognition not installed. "
                "Install with: pip install face_recognition"
            )
        except Exception as e:
            logger.error(f"Face module load failed: {e}")

    def register_face(self, name: str, image: np.ndarray) -> bool:
        """
        Register a face from an image.

        Args:
            name: Name/ID of the person
            image: Image containing the face (RGB)

        Returns:
            True if face was registered successfully
        """
        if not self._is_loaded:
            self.load()

        if self._face_recognition is None:
            return False

        try:
            rgb = image[:, :, ::-1]  # BGR to RGB
            encodings = self._face_recognition.face_encodings(rgb)

            if encodings:
                self._database.add_face(name, encodings[0])
                return True
            else:
                logger.warning(f"No face found in image for {name}")
                return False

        except Exception as e:
            logger.error(f"Face registration error: {e}")
            return False

    def process(self, image: np.ndarray) -> list[FaceResult]:
        """
        Detect and identify faces in an image.

        Args:
            image: Input image (BGR numpy array)

        Returns:
            List of FaceResult objects
        """
        if not self._is_loaded:
            self.load()

        if self._face_recognition is None:
            return []

        try:
            rgb = image[:, :, ::-1]  # BGR to RGB

            # Detect face locations and encodings
            locations = self._face_recognition.face_locations(rgb)
            encodings = self._face_recognition.face_encodings(rgb, locations)

            results = []
            for i, (location, encoding) in enumerate(zip(locations, encodings)):
                top, right, bottom, left = location

                # Try to match against database
                name = "unknown"
                confidence = 0.0
                is_match = False

                if self._database.get_count() > 0:
                    distances = self._face_recognition.face_distance(
                        self._database.encodings, encoding
                    )
                    best_idx = int(np.argmin(distances))
                    best_distance = distances[best_idx]

                    if best_distance <= self._tolerance:
                        name = self._database.names[best_idx]
                        confidence = 1.0 - best_distance
                        is_match = True

                results.append(
                    FaceResult(
                        face_id=i,
                        name=name,
                        confidence=confidence,
                        bbox=[top, right, bottom, left],
                        is_match=is_match,
                    )
                )

            logger.debug(f"Face: {len(results)} faces detected")
            return results

        except Exception as e:
            logger.error(f"Face processing error: {e}")
            return []

    @property
    def database(self) -> FaceDatabase:
        return self._database

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded
