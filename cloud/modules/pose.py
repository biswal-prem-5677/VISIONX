"""
VisionX — Pose Estimation Module (Cloud)
============================================
Human skeleton detection and action recognition.
Uses MediaPipe or YOLO-Pose for keypoint estimation.
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np
from loguru import logger
from pydantic import BaseModel, Field


class Keypoint(BaseModel):
    """A single body keypoint."""
    name: str
    x: float
    y: float
    confidence: float


class PoseResult(BaseModel):
    """Result from pose estimation."""
    person_id: int
    keypoints: list[Keypoint] = Field(default_factory=list)
    bbox: list[int] = Field(default_factory=list)  # [x1, y1, x2, y2]
    action: str = "unknown"  # Detected action (standing, sitting, etc.)
    confidence: float = 0.0


# MediaPipe pose landmark names
BODY_KEYPOINTS = [
    "nose", "left_eye_inner", "left_eye", "left_eye_outer",
    "right_eye_inner", "right_eye", "right_eye_outer",
    "left_ear", "right_ear", "mouth_left", "mouth_right",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_pinky", "right_pinky",
    "left_index", "right_index", "left_thumb", "right_thumb",
    "left_hip", "right_hip", "left_knee", "right_knee",
    "left_ankle", "right_ankle", "left_heel", "right_heel",
    "left_foot_index", "right_foot_index",
]


class PoseModule:
    """
    Pose estimation module.

    Detects human body keypoints and classifies basic actions.
    Uses MediaPipe Pose for keypoint detection.
    Runs on cloud for multi-person estimation.
    """

    def __init__(self, min_detection_confidence: float = 0.5):
        self._min_confidence = min_detection_confidence
        self._pose = None
        self._is_loaded = False

        logger.info(f"Pose Module initialized (min_conf: {min_detection_confidence})")

    def load(self) -> None:
        """Load the pose estimation model."""
        if self._is_loaded:
            return

        try:
            import mediapipe as mp

            self._mp_pose = mp.solutions.pose
            self._pose = self._mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                min_detection_confidence=self._min_confidence,
                min_tracking_confidence=0.5,
            )
            self._is_loaded = True
            logger.info("Pose estimation model loaded (MediaPipe)")
        except ImportError:
            logger.warning(
                "MediaPipe not installed. Install with: pip install mediapipe"
            )
        except Exception as e:
            logger.error(f"Pose model load failed: {e}")

    def process(self, image: np.ndarray) -> list[PoseResult]:
        """
        Detect poses in an image.

        Args:
            image: Input image (BGR numpy array)

        Returns:
            List of PoseResult objects
        """
        if not self._is_loaded:
            self.load()

        if self._pose is None:
            return []

        try:
            import cv2

            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            result = self._pose.process(rgb)

            if not result.pose_landmarks:
                return []

            h, w = image.shape[:2]
            landmarks = result.pose_landmarks.landmark

            keypoints = []
            xs, ys = [], []

            for i, lm in enumerate(landmarks):
                name = BODY_KEYPOINTS[i] if i < len(BODY_KEYPOINTS) else f"kp_{i}"
                kp = Keypoint(
                    name=name,
                    x=lm.x * w,
                    y=lm.y * h,
                    confidence=lm.visibility,
                )
                keypoints.append(kp)
                xs.append(lm.x * w)
                ys.append(lm.y * h)

            # Bounding box from keypoints
            bbox = [int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))]

            # Basic action classification
            action = self._classify_action(keypoints)

            pose_result = PoseResult(
                person_id=0,
                keypoints=keypoints,
                bbox=bbox,
                action=action,
                confidence=sum(kp.confidence for kp in keypoints) / len(keypoints),
            )

            return [pose_result]

        except Exception as e:
            logger.error(f"Pose processing error: {e}")
            return []

    def _classify_action(self, keypoints: list[Keypoint]) -> str:
        """Basic action classification from keypoints."""
        try:
            kp_dict = {kp.name: kp for kp in keypoints}

            left_hip = kp_dict.get("left_hip")
            right_hip = kp_dict.get("right_hip")
            left_knee = kp_dict.get("left_knee")
            right_knee = kp_dict.get("right_knee")
            nose = kp_dict.get("nose")
            left_wrist = kp_dict.get("left_wrist")
            right_wrist = kp_dict.get("right_wrist")

            if not all([left_hip, right_hip, left_knee, right_knee]):
                return "unknown"

            hip_y = (left_hip.y + right_hip.y) / 2
            knee_y = (left_knee.y + right_knee.y) / 2

            # Sitting: knees roughly at same height as hips
            if abs(hip_y - knee_y) < 50:
                return "sitting"

            # Hands raised: wrists above nose
            if left_wrist and right_wrist and nose:
                if left_wrist.y < nose.y and right_wrist.y < nose.y:
                    return "hands_raised"

            # Fall detection: nose below hips
            if nose and nose.y > hip_y:
                return "fallen"

            return "standing"

        except Exception:
            return "unknown"

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded
