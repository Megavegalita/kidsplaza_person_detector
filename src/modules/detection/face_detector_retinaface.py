#!/usr/bin/env python3
"""
RetinaFace face detector for improved accuracy and false positive reduction.

Replaces YuNet to solve:
- False positive issues (motorcycles)
- Low accuracy for difficult angles
- Better landmark quality
"""

import logging
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

try:
    from retinaface import RetinaFace

    RETINAFACE_AVAILABLE = True
except ImportError:
    RETINAFACE_AVAILABLE = False
    RetinaFace = None

logger = logging.getLogger(__name__)


class FaceDetectorRetinaFace:
    """
    Face detector using RetinaFace for high accuracy and low false positives.

    Replaces YuNet to solve:
    - False positive issues (motorcycles)
    - Low accuracy for difficult angles
    - Better landmark quality
    """

    def __init__(
        self,
        min_detection_confidence: float = 0.5,
        model_selection: str = "mobile",  # "mobile" (fast) or "resnet50" (accurate)
        body_expand_ratio: float = 3.0,
        body_expand_vertical: float = 0.5,
        input_size: Optional[tuple[int, int]] = None,
        detect_resize: Optional[tuple[int, int]] = None,
    ) -> None:
        """
        Initialize RetinaFace detector.

        Args:
            min_detection_confidence: Minimum confidence threshold
            model_selection: "mobile" (fast, ~10ms) or "resnet50" (accurate, ~15ms)
            body_expand_ratio: Ratio to expand face bbox for full body
            body_expand_vertical: Additional vertical expansion
            input_size: Input size (not used for RetinaFace, kept for compatibility)
            detect_resize: Resize frame for faster detection
        """
        if not RETINAFACE_AVAILABLE:
            raise ImportError(
                "retinaface not available. Install with: pip install retinaface"
            )

        self.min_detection_confidence = min_detection_confidence
        self.body_expand_ratio = body_expand_ratio
        self.body_expand_vertical = body_expand_vertical
        self.model_selection = model_selection
        self.detect_resize = detect_resize

        logger.info(
            "FaceDetectorRetinaFace initialized: confidence=%.2f, model=%s",
            min_detection_confidence,
            model_selection,
        )

    def detect_persons_from_faces(
        self, frame: np.ndarray, channel_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect persons from faces using RetinaFace.

        Args:
            frame: Input frame (BGR format)
            channel_id: Optional channel ID for channel-specific validation

        Returns:
            List of person detections in format:
            {
                "bbox": [x1, y1, x2, y2],
                "confidence": float,
                "class_id": 0,
                "class_name": "person",
                "face_bbox": [x1, y1, x2, y2],
            }
        """
        try:
            h, w = frame.shape[:2]

            # Resize for faster detection if needed
            if self.detect_resize is not None:
                detect_w, detect_h = self.detect_resize
                if w > detect_w or h > detect_h:
                    scale_w = detect_w / w
                    scale_h = detect_h / h
                    scale = min(scale_w, scale_h)
                    new_w = int(w * scale)
                    new_h = int(h * scale)
                    detect_frame = cv2.resize(
                        frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR
                    )
                    scale_factor_x = w / new_w
                    scale_factor_y = h / new_h
                else:
                    detect_frame = frame
                    scale_factor_x = 1.0
                    scale_factor_y = 1.0
            else:
                detect_frame = frame
                scale_factor_x = 1.0
                scale_factor_y = 1.0

            # RetinaFace expects RGB
            rgb_frame = cv2.cvtColor(detect_frame, cv2.COLOR_BGR2RGB)

            # Run RetinaFace detection
            # RetinaFace.detect_faces returns dict: {"face_1": {...}, "face_2": {...}}
            results = RetinaFace.detect_faces(rgb_frame)

            person_detections = []

            if results:
                logger.info("Found %d faces from RetinaFace detector", len(results))

                for face_key, face_data in results.items():
                    confidence = face_data.get("score", 0.0)

                    # Filter by confidence
                    if confidence < self.min_detection_confidence:
                        logger.debug(
                            "Rejected face: confidence %.3f < threshold %.3f",
                            confidence,
                            self.min_detection_confidence,
                        )
                        continue

                    # Get face bbox
                    # RetinaFace returns: facial_area: [x1, y1, x2, y2]
                    facial_area = face_data.get("facial_area", [])
                    if len(facial_area) < 4:
                        continue

                    face_x = facial_area[0]
                    face_y = facial_area[1]
                    face_x2 = facial_area[2]
                    face_y2 = facial_area[3]
                    face_w = face_x2 - face_x
                    face_h = face_y2 - face_y

                    # Scale back to original frame size
                    face_x = face_x * scale_factor_x
                    face_y = face_y * scale_factor_y
                    face_w = face_w * scale_factor_x
                    face_h = face_h * scale_factor_y

                    face_x2 = face_x + face_w
                    face_y2 = face_y + face_h

                    # Clamp to frame boundaries
                    face_x = int(max(0, min(face_x, w - 1)))
                    face_y = int(max(0, min(face_y, h - 1)))
                    face_x2 = int(max(0, min(face_x2, w)))
                    face_y2 = int(max(0, min(face_y2, h)))

                    if face_x2 <= face_x or face_y2 <= face_y:
                        continue

                    # Validate face size
                    face_w_actual = face_x2 - face_x
                    face_h_actual = face_y2 - face_y

                    # Channel-specific minimum face size
                    if channel_id in [3, 4]:
                        min_face_size = 16  # Indoor
                    else:
                        min_face_size = 12  # Outdoor

                    if face_w_actual < min_face_size or face_h_actual < min_face_size:
                        logger.debug(
                            "Rejected face: too small (%dx%d < %dx%d)",
                            face_w_actual,
                            face_h_actual,
                            min_face_size,
                            min_face_size,
                        )
                        continue

                    # Validate aspect ratio
                    face_aspect_ratio = (
                        face_w_actual / face_h_actual if face_h_actual > 0 else 0
                    )
                    min_aspect = 0.5
                    max_aspect = 1.5
                    if (
                        face_aspect_ratio <= min_aspect
                        or face_aspect_ratio >= max_aspect
                    ):
                        logger.debug(
                            "Rejected face: invalid aspect ratio (%.3f)",
                            face_aspect_ratio,
                        )
                        continue

                    # Estimate full body bbox
                    face_center_x = (face_x + face_x2) / 2
                    face_center_y = (face_y + face_y2) / 2

                    body_width = face_w_actual * self.body_expand_ratio
                    body_height = (
                        face_h_actual
                        * self.body_expand_ratio
                        * (1 + self.body_expand_vertical)
                    )

                    body_x1 = int(face_center_x - body_width / 2)
                    body_y1 = int(face_center_y - face_h_actual * 0.5)
                    body_x2 = int(body_x1 + body_width)
                    body_y2 = int(body_y1 + body_height)

                    # Clamp to frame boundaries
                    body_x1 = max(0, min(body_x1, w - 1))
                    body_y1 = max(0, min(body_y1, h - 1))
                    body_x2 = max(0, min(body_x2, w))
                    body_y2 = max(0, min(body_y2, h))

                    if body_x2 > body_x1 and body_y2 > body_y1:
                        person_detections.append(
                            {
                                "bbox": [body_x1, body_y1, body_x2, body_y2],
                                "confidence": confidence,
                                "class_id": 0,
                                "class_name": "person",
                                "face_bbox": [face_x, face_y, face_x2, face_y2],
                            }
                        )

                if len(person_detections) > 0:
                    logger.info(
                        "RetinaFace detected %d persons (from %d faces)",
                        len(person_detections),
                        len(results),
                    )
            else:
                logger.debug("RetinaFace returned no faces")

            return person_detections

        except Exception as e:
            logger.error("RetinaFace detection error: %s", e, exc_info=True)
            return []

    def release(self) -> None:
        """Release resources."""
        # RetinaFace doesn't require explicit release
        logger.info("RetinaFace detector resources released")


# Export availability flag
__all__ = ["FaceDetectorRetinaFace", "RETINAFACE_AVAILABLE"]
