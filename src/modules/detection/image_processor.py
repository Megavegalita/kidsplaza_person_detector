#!/usr/bin/env python3
"""
Image processing utilities for detection.

Optimized for efficient preprocessing on M4 Pro.
"""

import logging
import numpy as np
from typing import Tuple, Optional
import cv2

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Handles image preprocessing for detection."""
    
    def __init__(
        self,
        target_size: Tuple[int, int] = (640, 640)
    ) -> None:
        """
        Initialize image processor.
        
        Args:
            target_size: Target size for resizing (width, height)
        """
        self.target_size = target_size
    
    def preprocess(
        self,
        frame: np.ndarray,
        maintain_aspect: bool = True
    ) -> np.ndarray:
        """
        Preprocess frame for detection.
        
        Args:
            frame: Input frame
            maintain_aspect: Whether to maintain aspect ratio
            
        Returns:
            Preprocessed frame
        """
        if maintain_aspect:
            return self._resize_pad(frame)
        else:
            return cv2.resize(frame, self.target_size)
    
    def _resize_pad(self, frame: np.ndarray) -> np.ndarray:
        """
        Resize frame with padding to maintain aspect ratio.
        
        Args:
            frame: Input frame
            
        Returns:
            Resized and padded frame
        """
        h, w = frame.shape[:2]
        target_w, target_h = self.target_size
        
        # Calculate scale
        scale = min(target_w / w, target_h / h)
        
        # Resize
        new_w = int(w * scale)
        new_h = int(h * scale)
        resized = cv2.resize(frame, (new_w, new_h))
        
        # Pad to target size
        top = (target_h - new_h) // 2
        bottom = target_h - new_h - top
        left = (target_w - new_w) // 2
        right = target_w - new_w - left
        
        padded = cv2.copyMakeBorder(
            resized,
            top, bottom, left, right,
            cv2.BORDER_CONSTANT,
            value=(0, 0, 0)
        )
        
        return padded
    
    def normalize(self, frame: np.ndarray) -> np.ndarray:
        """
        Normalize frame values to 0-1 range.
        
        Args:
            frame: Input frame
            
        Returns:
            Normalized frame
        """
        return frame.astype(np.float32) / 255.0
    
    def to_tensor(self, frame: np.ndarray) -> np.ndarray:
        """
        Convert frame to tensor format.
        
        Args:
            frame: Input frame
            
        Returns:
            Tensor-formatted frame
        """
        # HWC to CHW conversion
        return np.transpose(frame, (2, 0, 1))
    
    def draw_detections(
        self,
        frame: np.ndarray,
        detections: list,
        color: Tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2,
        show_labels: bool = True
    ) -> np.ndarray:
        """
        Draw detection bounding boxes on frame.
        
        Args:
            frame: Input frame
            detections: List of detections
            color: Box color (BGR format)
            thickness: Box thickness
            show_labels: Whether to show labels
            
        Returns:
            Annotated frame
        """
        annotated = frame.copy()
        
        for detection in detections:
            bbox = detection['bbox']
            conf = detection['confidence']
            
            x1, y1, x2, y2 = map(int, bbox)
            
            # Draw bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)
            
            if show_labels:
                # Build label with track_id if available
                label = f"{detection.get('class_name', 'person')}: {conf:.2f}"
                if 'track_id' in detection:
                    label = f"ID{detection['track_id']} - {label}"
                
                # Draw label background
                (text_width, text_height), baseline = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
                )
                cv2.rectangle(
                    annotated,
                    (x1, y1 - text_height - baseline - 2),
                    (x1 + text_width, y1),
                    color,
                    -1
                )
                
                # Draw label text
                cv2.putText(
                    annotated,
                    label,
                    (x1, y1 - baseline),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 0),
                    1
                )
        
        return annotated
    
    def crop_person(
        self,
        frame: np.ndarray,
        bbox: np.ndarray
    ) -> Optional[np.ndarray]:
        """
        Crop person region from frame.
        
        Args:
            frame: Input frame
            bbox: Bounding box [x1, y1, x2, y2]
            
        Returns:
            Cropped person region or None
        """
        x1, y1, x2, y2 = map(int, bbox)
        
        # Validate coordinates
        h, w = frame.shape[:2]
        x1 = max(0, min(x1, w))
        x2 = max(0, min(x2, w))
        y1 = max(0, min(y1, h))
        y2 = max(0, min(y2, h))
        
        if x2 <= x1 or y2 <= y1:
            return None
        
        return frame[y1:y2, x1:x2]


if __name__ == "__main__":
    # Test the module
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        processor = ImageProcessor()
        
        # Create test image
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Test preprocessing
        preprocessed = processor.preprocess(test_frame)
        print(f"Original size: {test_frame.shape}")
        print(f"Preprocessed size: {preprocessed.shape}")
        
        # Test detections (dummy)
        detections = [
            {
                'bbox': np.array([100, 100, 200, 300]),
                'confidence': 0.85,
                'class_name': 'person'
            }
        ]
        
        annotated = processor.draw_detections(test_frame, detections)
        print(f"Annotated frame shape: {annotated.shape}")
        
        print("\n✅ Image processor test passed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

