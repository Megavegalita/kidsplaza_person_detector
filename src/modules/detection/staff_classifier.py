#!/usr/bin/env python3
"""
Staff Classifier module - Classifies detected persons as staff or customer.

Uses a custom YOLOv8 model trained specifically for Kidsplaza staff detection.
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

import cv2
import numpy as np
import torch
from ultralytics import YOLO

logger = logging.getLogger(__name__)


class StaffClassifierError(Exception):
    """Raised when staff classifier errors occur."""

    pass


class StaffClassifier:
    """
    Classifies person crops as staff (kidsplaza) or customer.

    Uses YOLOv8 model with 2 classes:
    - Class 0: customer
    - Class 1: kidsplaza (staff)
    """

    def __init__(
        self,
        model_path: str = "models/kidsplaza/best.pt",
        device: Optional[str] = None,
        conf_threshold: float = 0.5,
    ) -> None:
        """
        Initialize staff classifier.

        Args:
            model_path: Path to YOLOv8 staff detection model.
            device: Device to use ('mps', 'cpu', or None for auto-select).
            conf_threshold: Confidence threshold for classification.

        Raises:
            StaffClassifierError: If model loading fails.
        """
        self.model_path = Path(model_path)
        self.conf_threshold = conf_threshold

        # Auto-select device if not specified
        if device is None:
            self.device = self._select_device()
        else:
            self.device = device

        self.model: Optional[YOLO] = None
        self._load_model()

    def _select_device(self) -> str:
        """
        Select best device for inference.

        Returns:
            'mps' if available, otherwise 'cpu'.
        """
        if torch.backends.mps.is_available():
            logger.info("Staff classifier using MPS (Metal GPU) device")
            return "mps"
        else:
            logger.info("Staff classifier using CPU")
            return "cpu"

    def _load_model(self) -> None:
        """Load YOLOv8 staff detection model."""
        try:
            if not self.model_path.exists():
                raise StaffClassifierError(
                    f"Staff model not found at {self.model_path}"
                )

            logger.info("Loading staff detection model from %s", str(self.model_path))
            self.model = YOLO(str(self.model_path))

            # Set model to evaluation mode
            if hasattr(self.model.model, "eval"):
                self.model.model.eval()

            # Verify model has expected classes
            if not hasattr(self.model, "names") or len(self.model.names) < 2:
                logger.warning(
                    "Staff model may not have expected classes. "
                    "Expected: customer (0), kidsplaza (1)"
                )
            else:
                logger.info(
                    "Model classes: %s",
                    {k: v for k, v in self.model.names.items()},
                )

            logger.info(
                "Staff classifier loaded successfully on device: %s", self.device
            )

        except Exception as e:
            logger.error("Failed to load staff classifier: %s", e)
            raise StaffClassifierError(f"Staff classifier loading failed: {e}") from e

    def classify(
        self,
        person_crop: np.ndarray,
        conf: Optional[float] = None,
    ) -> Tuple[str, float]:
        """
        Classify person crop as staff or customer.

        Args:
            person_crop: Person crop image (BGR format from OpenCV).
            conf: Confidence threshold (uses default if None).

        Returns:
            Tuple of (person_type, confidence):
            - person_type: "staff" (kidsplaza) or "customer"
            - confidence: Confidence score (0.0-1.0).
        """
        if self.model is None:
            raise StaffClassifierError("Model is not loaded")

        conf_threshold = conf if conf is not None else self.conf_threshold

        try:
            # Run inference on person crop
            results = self.model.predict(
                person_crop,
                device=self.device,
                conf=conf_threshold,
                verbose=False,
            )

            if len(results) == 0 or results[0].boxes is None:
                # No detection, default to customer
                logger.debug("No staff detection found, defaulting to customer")
                return "customer", 0.0

            result = results[0]
            boxes = result.boxes

            # Check if boxes is empty
            if len(boxes) == 0:
                logger.debug("No detections in staff model, defaulting to customer")
                return "customer", 0.0

            # Get detection with highest confidence
            best_idx = 0
            best_conf = float(boxes.conf[0])
            for i in range(1, len(boxes)):
                if float(boxes.conf[i]) > best_conf:
                    best_conf = float(boxes.conf[i])
                    best_idx = i

            # Get class ID
            class_id = int(boxes.cls[best_idx])
            confidence = float(boxes.conf[best_idx])

            # Map class ID to person type
            # Class 0: customer, Class 1: kidsplaza (staff)
            if class_id == 1:  # kidsplaza
                person_type = "staff"
            elif class_id == 0:  # customer
                person_type = "customer"
            else:
                # Unknown class, default to customer
                logger.warning(
                    "Unknown class ID %d from staff model, defaulting to customer",
                    class_id,
                )
                person_type = "customer"
                confidence = 0.0

            logger.debug(
                "Staff classification: type=%s, confidence=%.3f, class_id=%d",
                person_type,
                confidence,
                class_id,
            )

            return person_type, confidence

        except Exception as e:
            logger.error("Staff classification failed: %s", e)
            # Default to customer on error
            return "customer", 0.0

    def classify_batch(
        self,
        person_crops: list[np.ndarray],
        conf: Optional[float] = None,
    ) -> list[Tuple[str, float]]:
        """
        Classify multiple person crops.

        Args:
            person_crops: List of person crop images.
            conf: Confidence threshold.

        Returns:
            List of (person_type, confidence) tuples.
        """
        results = []
        for crop in person_crops:
            result = self.classify(crop, conf=conf)
            results.append(result)
        return results

    def get_device(self) -> str:
        """Get current device."""
        return self.device

    def is_mps_enabled(self) -> bool:
        """Check if MPS is enabled."""
        return self.device == "mps"


if __name__ == "__main__":
    # Test the module
    import sys

    logging.basicConfig(level=logging.INFO)

    try:
        classifier = StaffClassifier()

        # Create dummy test crop
        test_crop = np.random.randint(0, 255, (200, 150, 3), dtype=np.uint8)

        person_type, confidence = classifier.classify(test_crop)
        print(f"Classification result: {person_type} (confidence: {confidence:.3f})")
        print(f"Device: {classifier.get_device()}")
        print(f"MPS enabled: {classifier.is_mps_enabled()}")

        print("\n✅ Staff classifier test passed")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
