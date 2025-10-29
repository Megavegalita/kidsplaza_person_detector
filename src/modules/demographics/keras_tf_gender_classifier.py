#!/usr/bin/env python3
"""
TensorFlow/Keras wrapper for your trained gender classification model.

Uses your existing trained model: cctv_full_body_gender_classification.h5
"""

import logging
from pathlib import Path
from typing import Optional, Tuple
import numpy as np
import cv2

try:
    import tensorflow as tf
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

logger = logging.getLogger(__name__)


class KerasTFGenderClassifier:
    """TensorFlow/Keras gender classifier wrapper."""
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        min_confidence: float = 0.3
    ) -> None:
        """
        Initialize Keras gender classifier.
        
        Args:
            model_path: Path to .h5 model file
            min_confidence: Minimum confidence threshold
        """
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow required. Install with: pip install tensorflow")
        
        self.min_confidence = min_confidence
        
        # Default model path
        if model_path is None:
            model_path = Path(__file__).parent.parent.parent.parent / 'models' / 'gender_classification' / 'cctv_full_body_gender_classification.h5'
        
        self.model_path = Path(model_path)
        self.model = self._load_model()
        
        logger.info(f"KerasTFGenderClassifier initialized")
        logger.info(f"Model path: {self.model_path}")
        logger.info(f"Min confidence: {min_confidence}")
    
    def _load_model(self):
        """Load Keras model."""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {self.model_path}")
        
        try:
            # Suppress TensorFlow warnings
            import os
            os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
            tf.get_logger().setLevel('ERROR')
            
            logger.info(f"Loading Keras model from {self.model_path}...")
            model = tf.keras.models.load_model(str(self.model_path), compile=False)
            
            # Determine model type
            output_shape = model.output_shape if hasattr(model, 'output_shape') else model.compute_output_shape(input_shape=(None, None, None, 3))
            if isinstance(output_shape, (list, tuple)) and len(output_shape) == 2:
                self.is_binary = output_shape[1] == 1
            else:
                self.is_binary = False
            
            logger.info(f"✅ Model loaded")
            logger.info(f"   Input shape: {model.input_shape}")
            logger.info(f"   Output shape: {output_shape}")
            
            return model
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def classify(self, crop: np.ndarray) -> Tuple[str, float]:
        """
        Classify gender from person crop.
        
        Args:
            crop: Person crop (BGR format from OpenCV)
            
        Returns:
            Tuple of (gender, confidence)
        """
        try:
            # Convert BGR to RGB
            crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
            
            # Get model input size from model.input_shape
            # Model expects: (None, 200, 100, 3) which means (height=200, width=100)
            # cv2.resize uses (width, height), so we need (100, 200)
            target_size = (100, 200)  # width=100, height=200
            
            # Resize to model's expected input size
            crop_resized = cv2.resize(crop_rgb, target_size)
            
            # Normalize to [0, 1]
            crop_normalized = crop_resized.astype(np.float32) / 255.0
            
            # Add batch dimension
            crop_batch = np.expand_dims(crop_normalized, axis=0)
            
            # Run inference
            prediction = self.model.predict(crop_batch, verbose=0)
            
            # Handle different output formats
            # Model has 2 outputs: [class_0_prob, class_1_prob]
            # Need to determine which is M and which is F
            outputs = prediction[0]
            
            class_0_prob = float(outputs[0])
            class_1_prob = float(outputs[1])
            
            # Mapping: Based on conf0.4_vote25 results M:60, F:14
            # Video shows M and F are reversed, need to swap back
            # class_0_prob > class_1_prob should give: M
            # class_0_prob <= class_1_prob should give: F
            if class_0_prob > class_1_prob:
                gender = 'M'  # class_0 -> Male
                confidence = class_0_prob
            else:
                gender = 'F'  # class_1 -> Female
                confidence = class_1_prob
            
            logger.debug(f"KerasTF outputs: class0={class_0_prob:.3f}, class1={class_1_prob:.3f} -> {gender}")
            
            logger.debug(f"KerasTF gender: {gender} (conf={confidence:.3f})")
            
            # Apply threshold
            if confidence < self.min_confidence:
                return 'Unknown', confidence
            
            return gender, confidence
            
        except Exception as e:
            logger.error(f"Error classifying: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return 'Unknown', 0.0
    
    def release(self) -> None:
        """Release resources."""
        if hasattr(self, 'model') and self.model is not None:
            del self.model
            self.model = None
        logger.debug("KerasTFGenderClassifier resources released")


if __name__ == "__main__":
    # Test
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        classifier = KerasTFGenderClassifier()
        print("✅ KerasTF gender classifier initialized")
        
        test_crop = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)
        gender, conf = classifier.classify(test_crop)
        
        print(f"Test result: {gender} (confidence={conf:.2f})")
        classifier.release()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

