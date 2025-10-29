#!/usr/bin/env python3
"""
Face detection module using MediaPipe BlazeFace.

Provides lightweight, real-time face detection within person bounding boxes.
Optimized for accuracy ≥70% detection rate with ≤10ms latency.
"""

import logging
from typing import Optional, List, Tuple
import numpy as np
import cv2
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False

logger = logging.getLogger(__name__)


class FaceDetector:
    """Face detector using MediaPipe BlazeFace within person bounding boxes."""
    
    def __init__(
        self,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        model_selection: int = 0  # 0=short range, 1=full range
    ) -> None:
        """
        Initialize face detector.
        
        Args:
            min_detection_confidence: Minimum confidence threshold (default: 0.5)
            min_tracking_confidence: Minimum tracking confidence (default: 0.5)
            model_selection: 0 for close faces (<2m), 1 for far faces
        """
        if not MEDIAPIPE_AVAILABLE:
            logger.warning("mediapipe not available, face detection disabled")
            self.detector = None
            self.face_detection = None
            return
        
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        
        # Initialize MediaPipe Face Detection
        self.face_detection = mp.solutions.face_detection.FaceDetection(
            model_selection=model_selection,
            min_detection_confidence=min_detection_confidence
        )
        
        logger.info(
            "FaceDetector initialized with confidence=%0.2f, model=%d",
            min_detection_confidence,
            model_selection
        )
    
    def detect_face(
        self,
        person_crop: np.ndarray
    ) -> Optional[Tuple[np.ndarray, float]]:
        """
        Detect face within person crop.
        
        Args:
            person_crop: Person bounding box crop (BGR format)
            
        Returns:
            Tuple of (face_bbox, confidence) or None if no face detected
            face_bbox: (x1, y1, x2, y2) relative to person_crop coordinates
        """
        if self.face_detection is None:
            return None
        
        try:
            # Convert BGR to RGB for MediaPipe
            rgb_crop = cv2.cvtColor(person_crop, cv2.COLOR_BGR2RGB)
            
            # Run face detection
            results = self.face_detection.process(rgb_crop)
            
            if not results.detections or len(results.detections) == 0:
                return None
            
            # Get first (most confident) detection
            detection = results.detections[0]
            confidence = detection.score[0]
            
            # Extract bounding box (normalized coordinates 0-1)
            bbox = detection.location_data.relative_bounding_box
            
            h, w = person_crop.shape[:2]
            
            # Convert to pixel coordinates
            x1 = int(bbox.xmin * w)
            y1 = int(bbox.ymin * h)
            width = int(bbox.width * w)
            height = int(bbox.height * h)
            
            x2 = x1 + width
            y2 = y1 + height
            
            # Clamp to crop boundaries
            x1 = max(0, min(x1, w - 1))
            y1 = max(0, min(y1, h - 1))
            x2 = max(0, min(x2, w))
            y2 = max(0, min(y2, h))
            
            if x2 <= x1 or y2 <= y1:
                return None
            
            face_bbox = np.array([x1, y1, x2, y2], dtype=np.int32)
            
            return face_bbox, confidence
            
        except Exception as e:
            logger.error(f"Face detection error: {e}")
            return None
    
    def detect_faces_batch(
        self,
        person_crops: List[np.ndarray]
    ) -> List[Optional[Tuple[np.ndarray, float]]]:
        """
        Detect faces in batch of person crops.
        
        Args:
            person_crops: List of person bounding box crops
            
        Returns:
            List of (face_bbox, confidence) or None for each crop
        """
        results = []
        for crop in person_crops:
            result = self.detect_face(crop)
            results.append(result)
        return results
    
    def crop_face(
        self,
        person_crop: np.ndarray,
        face_bbox: np.ndarray,
        expand_ratio: float = 0.1
    ) -> Optional[np.ndarray]:
        """
        Crop face region from person crop.
        
        Args:
            person_crop: Person bounding box crop
            face_bbox: Face bounding box (x1, y1, x2, y2)
            expand_ratio: Expansion ratio for crop (default: 0.1 = 10% margin)
            
        Returns:
            Face crop or None if invalid
        """
        h, w = person_crop.shape[:2]
        x1, y1, x2, y2 = face_bbox
        
        # Expand bounding box slightly
        width = x2 - x1
        height = y2 - y1
        
        expand_w = int(width * expand_ratio)
        expand_h = int(height * expand_ratio)
        
        x1_expanded = max(0, x1 - expand_w)
        y1_expanded = max(0, y1 - expand_h)
        x2_expanded = min(w, x2 + expand_w)
        y2_expanded = min(h, y2 + expand_h)
        
        # Crop face region
        face_crop = person_crop[y1_expanded:y2_expanded, x1_expanded:x2_expanded]
        
        if face_crop.size == 0:
            return None
        
        return face_crop
    
    def release(self) -> None:
        """Release resources."""
        if self.face_detection is not None:
            self.face_detection.close()
            self.face_detection = None
        logger.info("Face detector resources released")


if __name__ == "__main__":
    # Test the module
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        detector = FaceDetector()
        
        print("✅ Face detector initialized")
        
        # Test with random person crop
        test_crop = np.random.randint(0, 255, (200, 150, 3), dtype=np.uint8)
        
        result = detector.detect_face(test_crop)
        if result:
            bbox, conf = result
            print(f"Face detected: bbox={bbox}, confidence={conf:.2f}")
        else:
            print("No face detected (expected for random noise)")
        
        detector.release()
        print("\n✅ Face detector test completed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

