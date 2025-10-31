#!/usr/bin/env python3
"""
Gender classification module for person detection.

Provides lightweight gender classification with majority voting for stability.
"""

import logging
from typing import Dict, Optional, Tuple

import cv2
import numpy as np
import torch
import torch.nn as nn
from torchvision import models, transforms
from .label_mapping import map_logits_to_gender

try:
    import timm

    TIMM_AVAILABLE = True
except ImportError:
    TIMM_AVAILABLE = False
    logger.warning("timm not available, will use simple CNN")

logger = logging.getLogger(__name__)


class GenderClassifier:
    """
    Lightweight gender classifier with stability features.

    Uses a simple CNN architecture for fast inference on person crops.
    Implements majority voting to prevent label flickering.
    """

    def __init__(
        self,
        model_type: str = "simple",
        device: Optional[str] = None,
        voting_window: int = 10,  # Increased for better stability
        min_confidence: float = 0.5,
        female_min_confidence: Optional[float] = None,
        male_min_confidence: Optional[float] = None,
    ) -> None:
        """
        Initialize gender classifier.

        Args:
            model_type: 'simple' for basic CNN, 'timm_mobile' for MobileNetV3, 'timm_efficient' for EfficientNet, 'resnet18_face' for torchvision ResNet-18
            device: Device for inference ('mps', 'cpu', 'cuda')
            voting_window: Number of recent predictions for majority voting
            min_confidence: Minimum confidence threshold for prediction
        """
        self.device = device or ("mps" if torch.backends.mps.is_available() else "cpu")
        self.voting_window = voting_window
        # Allow configurable min_confidence
        self.min_confidence = min_confidence
        self.female_min_confidence = female_min_confidence
        self.male_min_confidence = male_min_confidence
        self.model_type = model_type

        # Initialize model
        self.model = self._build_model(model_type)
        self.model.eval()

        # Transform for input images
        input_size = (64, 64)
        if self.model_type in ("timm_mobile", "timm_efficient", "resnet18_face"):
            input_size = (224, 224)
        self.transform = transforms.Compose(
            [
                transforms.ToPILImage(),
                transforms.Resize(input_size),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                ),
            ]
        )

        # Prediction history for voting
        self._prediction_history = {}  # track_id -> list of recent predictions

        logger.info(f"GenderClassifier initialized on {self.device}")
        logger.info(
            f"Voting window: {voting_window}, min confidence: {min_confidence}, "
            f"female_min_conf={female_min_confidence}, male_min_conf={male_min_confidence}"
        )

    def _build_model(self, model_type: str) -> nn.Module:
        """Build model for gender classification."""
        if model_type == "timm_mobile" and TIMM_AVAILABLE:
            logger.info(
                "Using MobileNetV3-Small from timm for gender classification (RECOMMENDED)"
            )
            model = timm.create_model(
                "mobilenetv3_small_100", pretrained=True, num_classes=2, in_chans=3
            )
        else:
            logger.warning(
                f"Unsupported model_type: {model_type}, falling back to simple CNN"
            )
            model = nn.Sequential(
                # Input: 3x64x64
                nn.Conv2d(3, 32, kernel_size=3, padding=1),  # 32x64x64
                nn.BatchNorm2d(32),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(2),  # 32x32x32
                nn.Conv2d(32, 64, kernel_size=3, padding=1),  # 64x32x32
                nn.BatchNorm2d(64),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(2),  # 64x16x16
                nn.Conv2d(64, 128, kernel_size=3, padding=1),  # 128x16x16
                nn.BatchNorm2d(128),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(2),  # 128x8x8
                nn.AdaptiveAvgPool2d((4, 4)),  # 128x4x4
                nn.Flatten(),  # 2048
                nn.Linear(2048, 512),
                nn.ReLU(inplace=True),
                nn.Dropout(0.5),
                nn.Linear(512, 2),  # 2 classes: Male, Female
                nn.Softmax(dim=1),
            )

        # Move to device
        model = model.to(self.device)

        return model

    def classify(
        self, crop: np.ndarray, track_id: Optional[int] = None
    ) -> Tuple[str, float]:
        """
        Classify gender from person crop.

        Args:
            crop: Person crop image (BGR format from OpenCV)
            track_id: Optional track ID for voting stability

        Returns:
            Tuple of (gender, confidence) - ('M' or 'F', confidence score)
        """
        try:
            # Debug: log crop properties
            logger.debug(
                f"Classifying gender for track_id={track_id}, crop shape={crop.shape}"
            )

            # Convert BGR to RGB
            crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)

            # Transform and prepare input
            input_tensor = self.transform(crop_rgb)
            input_batch = input_tensor.unsqueeze(0).to(self.device)

            # Run inference
            with torch.no_grad():
                outputs = self.model(input_batch)

                # Apply softmax to get probabilities
                prob = torch.softmax(outputs, dim=1).squeeze()
                class_0_prob = prob[0].item()
                class_1_prob = prob[1].item()

                # DEBUG: Track probability distribution to diagnose mislabeling
                logger.debug(
                    f"Track_id={track_id}: Raw probs class0={class_0_prob:.3f} class1={class_1_prob:.3f}"
                )

            # Map logits using shared utility; this classifier uses female0_male1 convention
            gender, confidence_val = map_logits_to_gender(
                class_0_prob,
                class_1_prob,
                "female0_male1",
                min_confidence=self.min_confidence,
                female_min_confidence=self.female_min_confidence,
                male_min_confidence=self.male_min_confidence,
            )
            logger.debug(
                f"Track_id={track_id}: Mapped prediction -> gender={gender}, conf={confidence_val:.3f}"
            )

            if gender == "Unknown":
                return gender, confidence_val

            # Update prediction history for voting
            if track_id is not None:
                if track_id not in self._prediction_history:
                    self._prediction_history[track_id] = []

                self._prediction_history[track_id].append(
                    {"gender": gender, "confidence": confidence_val}
                )

                # Keep only recent predictions
                if len(self._prediction_history[track_id]) > self.voting_window:
                    self._prediction_history[track_id].pop(0)

                # Return majority vote if we have enough history
                if len(self._prediction_history[track_id]) >= 3:
                    recent_genders = [
                        p["gender"] for p in self._prediction_history[track_id]
                    ]
                    gender_counts = {}
                    for g in recent_genders:
                        gender_counts[g] = gender_counts.get(g, 0) + 1
                    vote_gender = max(gender_counts.items(), key=lambda x: x[1])[0]

                    # Only change if confidence is high
                    last_confidence = self._prediction_history[track_id][-1][
                        "confidence"
                    ]
                    if last_confidence > 0.7:
                        logger.debug(
                            f"Track_id={track_id}: Majority vote={vote_gender} (history: {recent_genders}), confidence={last_confidence:.2f}"
                        )
                        return vote_gender, last_confidence

            logger.debug(
                f"Track_id={track_id}: Direct prediction={gender}, confidence={confidence_val:.2f}"
            )
            return gender, confidence_val

        except Exception as e:
            logger.error(f"Error classifying gender: {e}")
            return "Unknown", 0.0

    def get_stable_prediction(self, track_id: int) -> Optional[Tuple[str, float]]:
        """
        Get stable gender prediction for a track.

        Uses majority voting on recent predictions.

        Args:
            track_id: Track ID

        Returns:
            Tuple of (gender, confidence) or None if not enough history
        """
        if track_id not in self._prediction_history:
            return None

        history = self._prediction_history[track_id]
        if len(history) < 3:
            return None

        # Get majority vote
        gender_counts = {}
        for pred in history[-self.voting_window :]:
            g = pred["gender"]
            gender_counts[g] = gender_counts.get(g, 0) + 1

        vote_gender = max(gender_counts.items(), key=lambda x: x[1])[0]
        avg_confidence = np.mean(
            [p["confidence"] for p in history[-self.voting_window :]]
        )

        return vote_gender, avg_confidence

    def clear_history(self, track_id: Optional[int] = None) -> None:
        """
        Clear prediction history.

        Args:
            track_id: Specific track ID to clear, or None to clear all
        """
        if track_id is None:
            self._prediction_history.clear()
        elif track_id in self._prediction_history:
            del self._prediction_history[track_id]

        logger.debug(f"Cleared prediction history for track_id={track_id}")
