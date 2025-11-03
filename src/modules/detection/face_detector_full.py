#!/usr/bin/env python3
"""
Full-frame face detection module using MediaPipe.

Primary detector for person detection - detects faces directly from full frame,
then expands to estimate full body bounding box.

Reuses FaceDetector from demographics module to avoid dependency conflicts.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

# Reuse existing FaceDetector which handles MediaPipe imports properly
# Import will be done at module level in process_live_camera.py
# This module expects to be imported after sys.path is set up
try:
    # Try importing - will work if sys.path is already set
    from src.modules.demographics.face_detector import (
        FaceDetector,
        MEDIAPIPE_AVAILABLE,
    )
except ImportError:
    # If direct import fails, will try lazy import
    FaceDetector = None  # type: ignore
    MEDIAPIPE_AVAILABLE = False

logger = logging.getLogger(__name__)


class FaceDetectorFull:
    """
    Full-frame face detector using MediaPipe.
    
    Detects faces directly from full camera frames, then estimates
    full body bounding boxes from face positions.
    """

    def __init__(
        self,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        model_selection: int = 1,  # 0=short range (<2m), 1=full range (2-5m)
        body_expand_ratio: float = 2.5,  # Expand face bbox by this ratio for full body
        body_expand_vertical: float = 0.4,  # Expand downward more
    ) -> None:
        """
        Initialize full-frame face detector.

        Args:
            min_detection_confidence: Minimum confidence for face detection
            min_tracking_confidence: Minimum tracking confidence
            model_selection: 0 for close faces (<2m), 1 for far faces (2-5m)
            body_expand_ratio: Ratio to expand face bbox for full body estimate
            body_expand_vertical: Additional vertical expansion ratio
        """
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.model_selection = model_selection
        self.body_expand_ratio = body_expand_ratio
        self.body_expand_vertical = body_expand_vertical

        # Try to import FaceDetector if not already imported
        _FaceDetectorClass = FaceDetector
        _MPAvailable = MEDIAPIPE_AVAILABLE
        
        if _FaceDetectorClass is None:
            try:
                import sys
                from pathlib import Path
                src_path = Path(__file__).parent.parent.parent
                if str(src_path) not in sys.path:
                    sys.path.insert(0, str(src_path))
                from src.modules.demographics.face_detector import (
                    FaceDetector as _FD,
                    MEDIAPIPE_AVAILABLE as _MP,
                )
                _FaceDetectorClass = _FD
                _MPAvailable = _MP
            except ImportError as e:
                logger.error("Failed to import FaceDetector: %s", e)
                raise ImportError("mediapipe is required for face detection") from e
        
        if not _MPAvailable:
            logger.error("mediapipe is required for face detection but not available")
            raise ImportError("mediapipe is required for face detection")

        # Create base FaceDetector instance (reuses existing implementation)
        # This handles MediaPipe imports properly and avoids conflicts
        self._base_detector = _FaceDetectorClass(
            min_detection_confidence=min_detection_confidence,
            model_selection=model_selection,
        )
        
        # Check if face_detection was initialized
        if self._base_detector.face_detection is None:
            raise ImportError(
                "Failed to initialize MediaPipe FaceDetection. "
                "MediaPipe may not be properly installed."
            )
        
        # Access the underlying MediaPipe face_detection instance
        self.face_detection = self._base_detector.face_detection

        logger.info(
            "FaceDetectorFull initialized: confidence=%.2f, model=%d, expand_ratio=%.2f",
            min_detection_confidence,
            model_selection,
            body_expand_ratio,
        )

    def detect_persons_from_faces(
        self, frame: np.ndarray
    ) -> List[Dict[str, Any]]:
        """
        Detect persons by detecting faces first, then expanding to full body.

        Args:
            frame: Full frame from camera (BGR format)

        Returns:
            List of person detections in format:
            {
                "bbox": [x1, y1, x2, y2],
                "confidence": float,
                "class_id": 0,
                "class_name": "person",
                "face_bbox": [x1, y1, x2, y2],  # Original face bbox
            }
        """
        if self.face_detection is None:
            return []

        try:
            # Convert BGR to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w = frame.shape[:2]

            # Run face detection on full frame
            results = self.face_detection.process(rgb_frame)

            person_detections = []

            if results.detections:
                for detection in results.detections:
                    confidence = detection.score[0]

                    # Get face bounding box (normalized 0-1)
                    bbox = detection.location_data.relative_bounding_box

                    # Convert to pixel coordinates
                    face_x1 = int(bbox.xmin * w)
                    face_y1 = int(bbox.ymin * h)
                    face_width = int(bbox.width * w)
                    face_height = int(bbox.height * h)

                    face_x2 = face_x1 + face_width
                    face_y2 = face_y1 + face_height

                    # Clamp to frame boundaries
                    face_x1 = max(0, min(face_x1, w - 1))
                    face_y1 = max(0, min(face_y1, h - 1))
                    face_x2 = max(0, min(face_x2, w))
                    face_y2 = max(0, min(face_y2, h))

                    if face_x2 <= face_x1 or face_y2 <= face_y1:
                        continue

                    # Estimate full body bounding box from face position
                    # Strategy: Face is typically in upper-middle of body
                    # Expand downward and slightly outward
                    face_center_x = (face_x1 + face_x2) / 2
                    face_center_y = (face_y1 + face_y2) / 2
                    face_w = face_x2 - face_x1
                    face_h = face_y2 - face_y1

                    # Estimate body width (wider than face)
                    body_width = face_w * self.body_expand_ratio
                    body_height = face_h * self.body_expand_ratio * (1 + self.body_expand_vertical)

                    # Center body bbox on face, but shift downward
                    # Face is typically at top 1/3 of body
                    body_x1 = int(face_center_x - body_width / 2)
                    body_y1 = int(face_center_y - face_h * 0.5)  # Face is at top of body
                    body_x2 = int(body_x1 + body_width)
                    body_y2 = int(body_y1 + body_height)

                    # Clamp to frame boundaries
                    body_x1 = max(0, min(body_x1, w - 1))
                    body_y1 = max(0, min(body_y1, h - 1))
                    body_x2 = max(0, min(body_x2, w))
                    body_y2 = max(0, min(body_y2, h))

                    if body_x2 > body_x1 and body_y2 > body_y1:
                        person_detection = {
                            "bbox": np.array([body_x1, body_y1, body_x2, body_y2], dtype=np.float32),
                            "confidence": float(confidence),
                            "class_id": 0,
                            "class_name": "person",
                            "face_bbox": np.array([face_x1, face_y1, face_x2, face_y2], dtype=np.float32),
                        }
                        person_detections.append(person_detection)

            return person_detections

        except Exception as e:
            logger.error("Face detection error: %s", e)
            return []

    def release(self) -> None:
        """Release resources."""
        if self._base_detector is not None:
            self._base_detector.release()
        self.face_detection = None
        self._base_detector = None
        logger.info("Face detector resources released")


if __name__ == "__main__":
    # Test the module
    import sys

    logging.basicConfig(level=logging.INFO)

    try:
        detector = FaceDetectorFull()
        print("✅ FaceDetectorFull initialized successfully")

        # Create test image
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

        # Test detection
        detections = detector.detect_persons_from_faces(test_frame)
        print(f"✅ Detection test passed: {len(detections)} detections")

        detector.release()
        print("✅ FaceDetectorFull test passed")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

