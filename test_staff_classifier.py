#!/usr/bin/env python3
"""
Test script for Staff Classifier module.

Tests staff detection functionality before integration.
"""

import logging
import sys
from pathlib import Path

import cv2
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.modules.detection.staff_classifier import StaffClassifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def test_staff_classifier():
    """Test staff classifier initialization and classification."""
    print("=" * 60)
    print("Testing Staff Classifier")
    print("=" * 60)

    # Test 1: Initialize classifier
    print("\n[Test 1] Initializing staff classifier...")
    try:
        classifier = StaffClassifier(
            model_path="models/kidsplaza/best.pt",
            conf_threshold=0.5,
        )
        print("✅ Staff classifier initialized successfully")
        print(f"   Device: {classifier.get_device()}")
        print(f"   MPS enabled: {classifier.is_mps_enabled()}")
    except Exception as e:
        print(f"❌ Failed to initialize staff classifier: {e}")
        return False

    # Test 2: Test classification with dummy image
    print("\n[Test 2] Testing classification with dummy image...")
    try:
        # Create a dummy person crop (200x150 RGB image)
        dummy_crop = np.random.randint(0, 255, (200, 150, 3), dtype=np.uint8)
        
        person_type, confidence = classifier.classify(dummy_crop)
        print(f"✅ Classification result:")
        print(f"   Person type: {person_type}")
        print(f"   Confidence: {confidence:.3f}")
        
        if person_type not in ["staff", "customer"]:
            print(f"⚠️  Warning: Unexpected person_type: {person_type}")
        
    except Exception as e:
        print(f"❌ Classification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 3: Test batch classification
    print("\n[Test 3] Testing batch classification...")
    try:
        dummy_crops = [
            np.random.randint(0, 255, (200, 150, 3), dtype=np.uint8)
            for _ in range(3)
        ]
        
        results = classifier.classify_batch(dummy_crops)
        print(f"✅ Batch classification completed:")
        for i, (person_type, confidence) in enumerate(results):
            print(f"   Crop {i+1}: {person_type} (confidence: {confidence:.3f})")
        
    except Exception as e:
        print(f"❌ Batch classification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    return True


def test_with_real_image():
    """Test with a real image if available."""
    print("\n" + "=" * 60)
    print("Testing with real image (if available)")
    print("=" * 60)
    
    # Try to find a test image
    test_image_paths = [
        "input/video/test_frame.jpg",
        "output/test_frame.jpg",
        "test_images/person.jpg",
    ]
    
    test_image = None
    for path in test_image_paths:
        if Path(path).exists():
            test_image = cv2.imread(path)
            if test_image is not None:
                print(f"✅ Found test image: {path}")
                break
    
    if test_image is None:
        print("⚠️  No test image found, skipping real image test")
        return True
    
    try:
        classifier = StaffClassifier(
            model_path="models/kidsplaza/best.pt",
            conf_threshold=0.5,
        )
        
        # Use entire image as crop (or crop a region)
        h, w = test_image.shape[:2]
        crop = test_image[0:h, 0:w]  # Use full image
        
        person_type, confidence = classifier.classify(crop)
        print(f"✅ Real image classification:")
        print(f"   Person type: {person_type}")
        print(f"   Confidence: {confidence:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Real image test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_staff_classifier()
    
    if success:
        test_with_real_image()
    
    sys.exit(0 if success else 1)

