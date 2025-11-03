#!/usr/bin/env python3
"""
Gender classification using OpenCV DNN (Caffe models).

Uses pretrained Caffe models trained on Adience dataset for high accuracy.
Optimized for face crops with OpenCL GPU acceleration support.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class GenderOpenCV:
    """Gender classifier using OpenCV DNN Caffe models."""

    # Model URLs - using Isfhan repository (verified working)
    GENDER_PROTO = (
        "https://raw.githubusercontent.com/Isfhan/age-gender-detection/master/"
        "models/gender_deploy.prototxt"
    )
    GENDER_MODEL = (
        "https://raw.githubusercontent.com/Isfhan/age-gender-detection/master/"
        "models/gender_net.caffemodel"
    )

    # Age ranges for reference (not used in classification, only for documentation)
    GENDER_LIST = ["Male", "Female"]

    def __init__(
        self,
        device: str = "cpu",
        min_confidence: float = 0.5,
    ) -> None:
        """
        Initialize OpenCV DNN gender classifier.

        Args:
            device: Backend device ('cpu', 'opencl', 'cuda')
            min_confidence: Minimum confidence threshold for prediction
        """
        self.device = device
        self.min_confidence = min_confidence
        self.gender_net = None

        # Model directory - use existing age_gender_opencv directory (models already there)
        # Path: src/modules/demographics/gender_opencv.py -> go up 3 levels to project root
        model_dir = Path(__file__).parent.parent.parent.parent / "models" / "age_gender_opencv"
        model_dir.mkdir(parents=True, exist_ok=True)

        # Load gender model
        self._load_gender_model(model_dir)

    def _load_gender_model(self, model_dir: Path) -> None:
        """Load gender classification model."""
        proto_path = model_dir / "gender_deploy.prototxt"
        model_path = model_dir / "gender_net.caffemodel"

        # Download if not exists
        if not proto_path.exists() or not model_path.exists():
            logger.warning(
                "Gender models not found. Please download manually from: %s",
                "https://github.com/Isfhan/age-gender-detection",
            )
            logger.warning(
                "Place files in: %s", model_dir
            )
            return

        try:
            # Load model
            self.gender_net = cv2.dnn.readNetFromCaffe(str(proto_path), str(model_path))

            # Set backend
            if self.device == "opencl" and cv2.ocl.haveOpenCL():
                self.gender_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
                self.gender_net.setPreferableTarget(cv2.dnn.DNN_TARGET_OPENCL)
                logger.info("Gender model loaded with OpenCL backend")
            elif self.device == "cuda" and cv2.cuda.getCudaEnabledDeviceCount() > 0:
                self.gender_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
                self.gender_net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
                logger.info("Gender model loaded with CUDA backend")
            else:
                self.gender_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_DEFAULT)
                self.gender_net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
                logger.info("Gender model loaded with CPU backend")

            logger.info("Gender OpenCV DNN model loaded successfully")
        except Exception as e:
            logger.error("Failed to load gender model: %s", e, exc_info=True)
            self.gender_net = None

    def classify(self, face_crop: np.ndarray) -> Tuple[str, float]:
        """
        Classify gender from face crop.

        Args:
            face_crop: Face crop image (BGR format from OpenCV)

        Returns:
            Tuple of (gender, confidence) - ('M' or 'F', confidence score)
        """
        if self.gender_net is None:
            return "Unknown", 0.0

        try:
            # Validate face crop
            if face_crop is None or face_crop.size == 0:
                logger.debug("Face crop is None or empty")
                return "Unknown", 0.0

            h, w = face_crop.shape[:2]
            if h < 48 or w < 48:  # Minimum size for reasonable classification
                logger.debug("Face crop too small: %dx%d", w, h)
                return "Unknown", 0.0

            # Model expects 227x227 input
            # Use better interpolation for small crops
            interpolation = cv2.INTER_LINEAR if min(h, w) >= 64 else cv2.INTER_CUBIC
            blob = cv2.dnn.blobFromImage(
                face_crop,
                1.0,
                (227, 227),
                (78.4263377603, 87.7689143744, 114.895847746),
                swapRB=False,
                crop=False,
            )

            # Set input
            self.gender_net.setInput(blob)

            # Run inference
            predictions = self.gender_net.forward()

            # Get gender prediction
            # Model outputs: [Male_prob, Female_prob]
            male_prob = float(predictions[0, 0])
            female_prob = float(predictions[0, 1])

            # Determine gender and confidence
            if male_prob > female_prob:
                gender = "M"
                confidence = male_prob
            else:
                gender = "F"
                confidence = female_prob

            logger.debug(
                "Gender OpenCV: %s (conf=%.3f, M=%.3f, F=%.3f)",
                gender,
                confidence,
                male_prob,
                female_prob,
            )

            # Apply minimum confidence threshold
            if confidence < self.min_confidence:
                logger.debug(
                    "Low confidence: %.2f < %.2f, returning 'Unknown'",
                    confidence,
                    self.min_confidence,
                )
                return "Unknown", confidence

            return gender, confidence

        except Exception as e:
            logger.error("Error classifying gender with OpenCV DNN: %s", e, exc_info=True)
            return "Unknown", 0.0

    def release(self) -> None:
        """Release resources."""
        if self.gender_net is not None:
            self.gender_net = None
        logger.debug("GenderOpenCV resources released")


if __name__ == "__main__":
    # Test the module
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        classifier = GenderOpenCV(device="opencl", min_confidence=0.5)

        if classifier.gender_net is None:
            print("❌ Gender model not loaded")
            sys.exit(1)

        print("✅ Gender OpenCV classifier initialized")

        # Test with random face crop
        test_face = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)

        gender, conf = classifier.classify(test_face)
        print(f"Test result: gender={gender}, confidence={conf:.2f}")

        classifier.release()
        print("\n✅ Gender OpenCV classifier test completed")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

