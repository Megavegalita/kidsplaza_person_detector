#!/usr/bin/env python3
"""
Model loader for YOLOv8 with MPS optimization.

Optimized for Apple M4 Pro with Metal Performance Shaders.
"""

import logging
from pathlib import Path
from typing import Optional

import torch
from ultralytics import YOLO

logger = logging.getLogger(__name__)


class ModelLoaderError(Exception):
    """Raised when model loading errors occur."""

    pass


class ModelLoader:
    """Loads and manages YOLOv8 model with MPS optimization."""

    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        device: Optional[str] = None,
        conf_threshold: float = 0.5,
        iou_threshold: float = 0.45,
    ) -> None:
        """
        Initialize model loader.

        Args:
            model_path: Path to YOLOv8 model file
            device: Device to use ('mps', 'cpu', or None for auto-select)
            conf_threshold: Confidence threshold for detections
            iou_threshold: IOU threshold for NMS

        Raises:
            ModelLoaderError: If model loading fails
        """
        self.model_path = Path(model_path)
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold

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
            'mps' if available, otherwise 'cpu'
        """
        if torch.backends.mps.is_available():
            logger.info("Using MPS (Metal GPU) device for acceleration")
            return "mps"
        else:
            logger.warning("MPS not available, using CPU")
            return "cpu"

    def _load_model(self) -> None:
        """Load YOLOv8 model."""
        try:
            logger.info("Loading YOLOv8 model from %s", str(self.model_path))

            if not self.model_path.exists():
                # Download model if not exists
                logger.info("Model file not found, downloading...")

            self.model = YOLO(str(self.model_path))

            # Move model to selected device
            logger.info("Model loaded on device: %s", self.device)

            # Set model to evaluation mode for inference
            if hasattr(self.model.model, "eval"):
                self.model.model.eval()

            logger.info("Model loaded successfully")

        except Exception as e:
            logger.error("Failed to load model: %s", e)
            raise ModelLoaderError(f"Model loading failed: {e}") from e

    def detect(self, frame, conf: Optional[float] = None, iou: Optional[float] = None):
        """
        Run detection on frame.

        Args:
            frame: Input frame (numpy array or path)
            conf: Confidence threshold (uses default if None)
            iou: IOU threshold (uses default if None)

        Returns:
            Detection results
        """
        conf = conf if conf is not None else self.conf_threshold
        iou = iou if iou is not None else self.iou_threshold

        try:
            if self.model is None:
                raise ModelLoaderError("Model is not loaded")
            results = self.model.predict(
                frame, device=self.device, conf=conf, iou=iou, verbose=False
            )
            return results

        except Exception as e:
            logger.error("Detection failed: %s", e)
            raise ModelLoaderError(f"Detection failed: {e}") from e

    def detect_persons(self, frame, conf: Optional[float] = None) -> list:
        """
        Detect persons in frame.

        Args:
            frame: Input frame
            conf: Confidence threshold

        Returns:
            List of person detections
        """
        results = self.detect(frame, conf=conf)

        if len(results) == 0:
            return []

        result = results[0]
        person_detections = []

        # Filter for person class (class 0 in COCO dataset)
        if result.boxes is not None:
            for box in result.boxes:
                class_id = int(box.cls[0])

                # Class 0 is 'person' in COCO dataset
                if class_id == 0:
                    detection = {
                        "bbox": box.xyxy[0].cpu().numpy(),
                        "confidence": float(box.conf[0]),
                        "class_id": class_id,
                        "class_name": "person",
                    }
                    person_detections.append(detection)

        return person_detections

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
        loader = ModelLoader()

        print("✅ Model loaded successfully")
        print(f"Device: {loader.get_device()}")
        print(f"MPS enabled: {loader.is_mps_enabled()}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
