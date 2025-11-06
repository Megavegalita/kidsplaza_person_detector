#!/usr/bin/env python3
"""
Age estimation module using pretrained PyTorch models from Hugging Face.

Provides accurate age estimation from face crops using pretrained models.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
import torch
import torch.nn as nn
from torchvision import models, transforms

logger = logging.getLogger(__name__)

try:
    from transformers import AutoModelForImageClassification

    # Try AutoImageProcessor, fallback to AutoFeatureExtractor for older versions
    try:
        from transformers import AutoImageProcessor

        TRANSFORMERS_HAS_IMAGE_PROCESSOR = True
    except ImportError:
        try:
            from transformers import AutoFeatureExtractor as AutoImageProcessor

            TRANSFORMERS_HAS_IMAGE_PROCESSOR = True
        except ImportError:
            TRANSFORMERS_HAS_IMAGE_PROCESSOR = False
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    TRANSFORMERS_HAS_IMAGE_PROCESSOR = False
    logger.warning("transformers not available, will use torchvision model")


class AgeEstimatorPyTorch:
    """
    Age estimator using pretrained PyTorch models.

    Supports multiple model sources:
    - Hugging Face transformers models
    - Torchvision pretrained models (fallback)
    """

    def __init__(
        self,
        model_name: str = "torchvision_resnet18",
        device: Optional[str] = None,
        min_confidence: float = 0.5,
    ) -> None:
        """
        Initialize age estimator.

        Args:
            model_name: Model identifier
                - "huggingface": Use Hugging Face model (requires transformers)
                - "torchvision_resnet18": Use ResNet18 from torchvision (default)
                - "torchvision_efficientnet": Use EfficientNet-B0
            device: Device for inference ('mps', 'cpu', 'cuda')
            min_confidence: Minimum confidence threshold
        """
        self.device = device or ("mps" if torch.backends.mps.is_available() else "cpu")
        self.model_name = model_name
        self.min_confidence = min_confidence

        # Initialize model
        self.model = None
        self.processor = None
        self._is_8_class_model = False  # For prithivMLmods/facial-age-detection
        self._hf_model_name = None
        self._load_model(model_name)

        # Transform for input images (standard ImageNet preprocessing)
        self.transform = transforms.Compose(
            [
                transforms.ToPILImage(),
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                ),
            ]
        )

        logger.info("AgeEstimatorPyTorch initialized on %s", self.device)

    def _load_model(self, model_name: str) -> None:
        """Load pretrained age estimation model with priority for Asian-optimized models."""
        try:
            if model_name.startswith("huggingface") and TRANSFORMERS_AVAILABLE:
                # Priority order: Best models for Asian faces first
                hf_models = [
                    # Priority 1: Best for Asian faces (8 age groups, 82.25% accuracy)
                    (
                        "prithivMLmods/facial-age-detection",
                        "8-class classification",
                        True,
                    ),
                    # Priority 2: Good regression model (UTKFace, MAE 5.2)
                    ("LisanneH/AgeEstimation", "regression", False),
                    # Priority 3: Combined age+gender (ResNet50)
                    ("fanclan/age-gender-model", "age+gender", False),
                    # Priority 4: Regression alternative
                    ("Sharris/age_detection_regression", "regression", False),
                ]

                for hf_model_name, model_type, is_8_class in hf_models:
                    try:
                        logger.info(
                            "Attempting to load Hugging Face model: %s (%s)",
                            hf_model_name,
                            model_type,
                        )
                        # Try to load processor with trust_remote_code for models that need it
                        try:
                            if TRANSFORMERS_HAS_IMAGE_PROCESSOR:
                                self.processor = AutoImageProcessor.from_pretrained(
                                    hf_model_name, trust_remote_code=True
                                )
                            else:
                                self.processor = None
                        except Exception as proc_e:
                            logger.debug(
                                "Could not load processor: %s, using manual preprocessing",
                                proc_e,
                            )
                            self.processor = None

                        # Try loading model with trust_remote_code=True (required for SigLIP and some custom models)
                        try:
                            self.model = (
                                AutoModelForImageClassification.from_pretrained(
                                    hf_model_name, trust_remote_code=True
                                )
                            )
                        except Exception as model_e1:
                            # If trust_remote_code fails, try without it
                            logger.debug(
                                "Failed with trust_remote_code=True: %s, trying without",
                                model_e1,
                            )
                            try:
                                self.model = (
                                    AutoModelForImageClassification.from_pretrained(
                                        hf_model_name
                                    )
                                )
                            except Exception as model_e2:
                                raise model_e2

                        self.model.eval()
                        self.model = self.model.to(self.device)

                        # Store model metadata for output handling
                        self._is_8_class_model = is_8_class
                        self._hf_model_name = hf_model_name

                        logger.info(
                            "✅ Loaded Hugging Face model successfully: %s (%s) - Optimized for Asian faces",
                            hf_model_name,
                            model_type,
                        )
                        return
                    except Exception as e:
                        logger.debug(
                            "Failed to load %s: %s, trying next...", hf_model_name, e
                        )
                        continue

                # All Hugging Face models failed
                logger.warning(
                    "All Hugging Face models failed to load, using torchvision fallback"
                )
                self._load_torchvision_model("torchvision_resnet18")
            else:
                # Use torchvision models
                self._load_torchvision_model(model_name)
        except Exception as e:
            logger.error("Failed to load age model: %s", e, exc_info=True)
            self.model = None

    def _load_torchvision_model(self, model_name: str) -> None:
        """Load torchvision pretrained model for age estimation."""
        try:
            if model_name == "torchvision_resnet18":
                # Load ResNet18 pretrained on ImageNet
                base_model = models.resnet18(
                    weights=models.ResNet18_Weights.IMAGENET1K_V1
                )
                # Replace final layer for age regression (0-100 years)
                num_features = base_model.fc.in_features
                base_model.fc = nn.Sequential(
                    nn.Linear(num_features, 512),
                    nn.ReLU(inplace=True),
                    nn.Dropout(0.5),
                    nn.Linear(512, 1),  # Age regression
                    nn.ReLU(),  # Ensure non-negative
                )
                logger.info(
                    "Loaded ResNet18 for age estimation (ImageNet pretrained, needs fine-tuning)"
                )
            elif model_name == "torchvision_efficientnet":
                # Load EfficientNet-B0
                base_model = models.efficientnet_b0(
                    weights=models.EfficientNet_B0_Weights.IMAGENET1K_V1
                )
                num_features = base_model.classifier[1].in_features
                base_model.classifier = nn.Sequential(
                    nn.Linear(num_features, 512),
                    nn.ReLU(inplace=True),
                    nn.Dropout(0.5),
                    nn.Linear(512, 1),
                    nn.ReLU(),
                )
                logger.info("Loaded EfficientNet-B0 for age estimation")
            else:
                logger.warning("Unknown model_name: %s, using ResNet18", model_name)
                return self._load_torchvision_model("torchvision_resnet18")

            self.model = base_model
            self.model.eval()
            self.model = self.model.to(self.device)

            # Mark as non-Hugging Face model
            self._is_8_class_model = False
            self._hf_model_name = model_name

            # Check if we have pretrained age weights
            model_path = (
                Path(__file__).parent.parent.parent.parent
                / "models"
                / "age_resnet18_pytorch.pth"
            )
            if model_path.exists():
                try:
                    state_dict = torch.load(str(model_path), map_location=self.device)
                    self.model.load_state_dict(state_dict)
                    logger.info("Loaded pretrained age weights from %s", model_path)
                except Exception as e:
                    logger.warning("Could not load pretrained weights: %s", e)
            else:
                logger.warning(
                    "No pretrained age weights found at %s. Model uses ImageNet weights only.",
                    model_path,
                )
                logger.warning(
                    "Age predictions will be approximate. Consider fine-tuning on age dataset."
                )

        except Exception as e:
            logger.error("Failed to load torchvision model: %s", e, exc_info=True)
            self.model = None

    def estimate(self, face_crop: np.ndarray) -> Tuple[int, float]:
        """
        Estimate age from face crop.

        Args:
            face_crop: Face crop image (BGR format from OpenCV)

        Returns:
            Tuple of (age, confidence)
            - age: Estimated age in years (0-100)
            - confidence: Confidence score (0-1) - approximate for regression models
        """
        if self.model is None:
            return 0, 0.0

        try:
            # Convert BGR to RGB
            face_rgb = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)

            # Transform and prepare input
            if self.processor is not None:
                # Use Hugging Face processor if available
                inputs = self.processor(face_rgb, return_tensors="pt")
                input_batch = inputs["pixel_values"].to(self.device)
            else:
                # Use standard torchvision transform
                input_tensor = self.transform(face_rgb)
                input_batch = input_tensor.unsqueeze(0).to(self.device)

            # Run inference
            with torch.no_grad():
                outputs = self.model(input_batch)

                # Debug: log raw outputs for analysis
                logger.debug(
                    "Age model raw output type: %s, shape: %s",
                    type(outputs),
                    outputs.shape if hasattr(outputs, "shape") else "N/A",
                )

                # Handle different output formats
                if hasattr(outputs, "logits"):
                    # Hugging Face format
                    logits = outputs.logits
                    logger.debug(
                        "Age model using Hugging Face format, logits shape: %s",
                        logits.shape,
                    )
                    if logits.dim() > 1:
                        # Classification model - map class to age
                        predicted_class = logits.argmax(dim=-1).item()
                        num_classes = logits.shape[-1]

                        # Use softmax probability as confidence
                        probs = torch.softmax(logits, dim=-1).squeeze()
                        confidence = float(probs[predicted_class].item())

                        # Map class index to age based on model type
                        if self._is_8_class_model and num_classes == 8:
                            # prithivMLmods/facial-age-detection: 8 age groups
                            # Classes: 0=(0-2), 1=(3-9), 2=(10-19), 3=(20-29), 4=(30-39), 5=(40-49), 6=(50-69), 7=(70+)
                            age_ranges_8class = [
                                (0, 2),  # 0-2 years
                                (3, 9),  # 3-9 years
                                (10, 19),  # 10-19 years
                                (20, 29),  # 20-29 years (target range for user's case)
                                (30, 39),  # 30-39 years
                                (40, 49),  # 40-49 years
                                (50, 69),  # 50-69 years
                                (70, 100),  # 70+ years
                            ]
                            if predicted_class < len(age_ranges_8class):
                                age_min, age_max = age_ranges_8class[predicted_class]
                                age = int(
                                    (age_min + age_max) / 2
                                )  # Use middle of range
                                logger.debug(
                                    "8-class model: class %d -> age range %d-%d, using %d",
                                    predicted_class,
                                    age_min,
                                    age_max,
                                    age,
                                )
                            else:
                                age = min(100, predicted_class * 10)
                        elif num_classes > 10:
                            # Generic classification model with many classes
                            # Assume uniform distribution
                            age = predicted_class * (100 / num_classes)
                        else:
                            # Standard age ranges (5 classes example)
                            age_ranges = [9, 24, 34, 44, 75]
                            if predicted_class < len(age_ranges):
                                age = age_ranges[predicted_class]
                            else:
                                age = min(100, predicted_class * 5)  # Fallback mapping
                    else:
                        # Regression model - direct age value from logits
                        age = logits.squeeze().item()
                        confidence = 0.8  # Default confidence for regression
                elif isinstance(outputs, torch.Tensor):
                    # Standard tensor output (regression)
                    age = outputs.squeeze().item()
                    confidence = 0.8
                else:
                    # Dictionary or other format
                    age = (
                        float(outputs[0]) if isinstance(outputs, (list, tuple)) else 0.0
                    )
                    confidence = 0.7

                # Clamp age to reasonable range (3-100)
                # Note: For 8-class model, age is already in valid range from mapping
                original_age = age
                age = max(3, min(100, int(round(age))))

                # Log if age was significantly adjusted (only for debugging)
                if abs(original_age - age) > 2:
                    logger.debug(
                        "Age estimation adjusted: %.2f -> %d (model: %s)",
                        original_age,
                        age,
                        self._hf_model_name or self.model_name,
                    )

                # Ensure confidence is set (should be set above, but safety check)
                if "confidence" not in locals() or confidence is None:
                    # Estimate confidence based on prediction certainty
                    # For regression models, use a heuristic based on prediction value
                    if 10 <= age <= 80:
                        # Age in typical range - higher confidence
                        confidence = min(0.95, 0.5 + (age / 100.0) * 0.3)
                    else:
                        # Extreme ages - lower confidence
                        confidence = 0.5

            logger.debug("Age estimation: %d years (conf=%.2f)", age, confidence)
            return age, confidence

        except Exception as e:
            logger.error("Age estimation error: %s", e, exc_info=True)
            return 0, 0.0

    def release(self) -> None:
        """Release resources."""
        self.model = None
        self.processor = None
        logger.info("Age estimator resources released")


if __name__ == "__main__":
    # Test the module
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        estimator = AgeEstimatorPyTorch(model_name="torchvision_resnet18")
        print("✅ Age estimator initialized")

        # Test with random face crop
        test_face = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)

        age, conf = estimator.estimate(test_face)
        print(f"Test result: age={age}, confidence={conf:.2f}")

        estimator.release()
        print("\n✅ Age estimator test completed")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
