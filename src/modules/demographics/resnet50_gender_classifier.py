#!/usr/bin/env python3
"""
ResNet50-based gender classifier.

Uses ResNet50 for high-accuracy gender classification.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
import torch
import torch.nn as nn
from torchvision import models

logger = logging.getLogger(__name__)


class ResNet50GenderClassifier:
    """Gender classifier using ResNet50."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        device: Optional[str] = None,
        min_confidence: float = 0.5,
    ) -> None:
        """
        Initialize ResNet50 gender classifier.

        Args:
            model_path: Path to the .pth model file
            device: Device for inference ('mps', 'cpu', 'cuda')
            min_confidence: Minimum confidence threshold for prediction
        """
        self.device = device or ("mps" if torch.backends.mps.is_available() else "cpu")
        self.min_confidence = min_confidence

        # Default model path
        if model_path is None:
            model_path = (
                Path(__file__).parent.parent.parent.parent
                / "models"
                / "resnet50_gender_pytorch.pth"
            )

        self.model_path = Path(model_path)

        # Load model
        self.model = self._load_model()

        logger.info(f"ResNet50GenderClassifier initialized on {self.device}")
        logger.info(f"Model path: {self.model_path}")
        logger.info(f"Min confidence threshold: {min_confidence}")

    def _load_model(self) -> nn.Module:
        """Load ResNet50 PyTorch model."""
        # Build model architecture
        model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)
        model.fc = nn.Linear(model.fc.in_features, 2)

        # Load custom weights if available
        if self.model_path.exists():
            try:
                state_dict = torch.load(str(self.model_path), map_location=self.device)
                model.load_state_dict(state_dict, strict=False)
                logger.info("✅ Loaded custom ResNet50 gender weights")
            except Exception as e:
                logger.warning(
                    f"Could not load custom weights: {e}, using ImageNet weights"
                )
        else:
            logger.info("Using ImageNet pretrained weights")

        model = model.to(self.device)
        model.eval()

        return model

    def classify(self, face_crop: np.ndarray) -> Tuple[str, float]:
        """
        Classify gender from person crop (full body or upper body).

        Args:
            face_crop: Person crop image (BGR format from OpenCV)

        Returns:
            Tuple of (gender, confidence) - ('M' or 'F', confidence score)
        """
        try:
            # Convert BGR to RGB
            crop_rgb = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)

            # Resize to 224x224 (ResNet50 input size)
            crop_resized = cv2.resize(crop_rgb, (224, 224))

            # Normalize to [0, 1]
            crop_normalized = crop_resized.astype(np.float32) / 255.0

            # Convert to tensor and normalize with ImageNet stats
            crop_tensor = (
                torch.from_numpy(crop_normalized).permute(2, 0, 1).unsqueeze(0).float()
            )
            crop_tensor = crop_tensor.to(self.device)

            # ImageNet normalization
            mean = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1).to(self.device)
            std = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1).to(self.device)
            crop_tensor = (crop_tensor - mean) / std

            # Run inference
            with torch.no_grad():
                outputs = self.model(crop_tensor)

                # Apply softmax to get probabilities
                prob = torch.softmax(outputs, dim=1).squeeze()

                # Get probabilities
                male_prob = prob[0].item()
                female_prob = prob[1].item()

                # Get prediction and confidence
                # Standard mapping: class 0=M, class 1=F
                if male_prob > female_prob:
                    predicted_gender = "M"
                    confidence = float(male_prob)
                else:
                    predicted_gender = "F"
                    confidence = float(female_prob)

                logger.debug(
                    f"ResNet50 gender: {predicted_gender} (conf={confidence:.3f}, M={male_prob:.3f}, F={female_prob:.3f})"
                )

                # Apply minimum confidence threshold
                if confidence < self.min_confidence:
                    logger.debug(
                        f"Low confidence: {confidence:.2f}, returning 'Unknown'"
                    )
                    return "Unknown", confidence

                return predicted_gender, confidence

        except Exception as e:
            logger.error(f"Error classifying gender with ResNet50: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return "Unknown", 0.0

    def release(self) -> None:
        """Release resources."""
        if hasattr(self, "model") and self.model is not None:
            del self.model
            self.model = None
        logger.debug("ResNet50GenderClassifier resources released")


if __name__ == "__main__":
    # Test the module
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        classifier = ResNet50GenderClassifier()

        print("✅ ResNet50 gender classifier initialized")

        # Test with random person crop
        test_person = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)

        gender, conf = classifier.classify(test_person)
        print(f"Test result: gender={gender}, confidence={conf:.2f}")

        classifier.release()
        print("\n✅ ResNet50 gender classifier test completed")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
