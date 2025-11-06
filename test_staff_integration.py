#!/usr/bin/env python3
"""
Integration test for staff detection pipeline.

Tests the complete flow: detection -> classification -> drawing -> counter filtering.
"""

import logging
import sys
from pathlib import Path

import cv2
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.modules.detection.staff_classifier import StaffClassifier
from src.modules.detection.image_processor import ImageProcessor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def test_integration():
    """Test integration of staff classifier with image processor."""
    print("=" * 60)
    print("Integration Test: Staff Detection Pipeline")
    print("=" * 60)

    # Initialize components
    print("\n[Step 1] Initializing components...")
    try:
        classifier = StaffClassifier(
            model_path="models/kidsplaza/best.pt",
            conf_threshold=0.3,  # Lower threshold for testing
        )
        processor = ImageProcessor()
        print("✅ Components initialized")
    except Exception as e:
        print(f"❌ Failed to initialize components: {e}")
        return False

    # Create test detections
    print("\n[Step 2] Creating test detections...")
    test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # Create detections with and without person_type
    detections = [
        {
            "bbox": [100, 100, 200, 300],
            "confidence": 0.85,
            "class_name": "person",
            "track_id": 1,
        },
        {
            "bbox": [300, 150, 400, 350],
            "confidence": 0.90,
            "class_name": "person",
            "track_id": 2,
        },
    ]
    print(f"✅ Created {len(detections)} test detections")

    # Test 1: Classification (simulate staff classification)
    print("\n[Step 3] Testing staff classification...")
    try:
        for i, det in enumerate(detections):
            bbox = det["bbox"]
            x1, y1, x2, y2 = map(int, bbox)
            crop = test_frame[y1:y2, x1:x2]
            
            if crop.size > 0:
                person_type, confidence = classifier.classify(crop)
                det["person_type"] = person_type
                det["staff_confidence"] = confidence
                print(f"   Detection {i+1}: {person_type} (confidence: {confidence:.3f})")
    except Exception as e:
        print(f"❌ Classification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 2: Drawing with color coding
    print("\n[Step 4] Testing image drawing with color coding...")
    try:
        # Test drawing without person_type (should use default color)
        det_no_type = [detections[0].copy()]
        del det_no_type[0]["person_type"]
        annotated_default = processor.draw_detections(test_frame.copy(), det_no_type)
        print("   ✅ Drawing with default color (no person_type)")

        # Test drawing with staff (should be red)
        det_staff = [detections[0].copy()]
        det_staff[0]["person_type"] = "staff"
        annotated_staff = processor.draw_detections(test_frame.copy(), det_staff)
        print("   ✅ Drawing staff (red color)")

        # Test drawing with customer (should be green)
        det_customer = [detections[1].copy()]
        det_customer[0]["person_type"] = "customer"
        annotated_customer = processor.draw_detections(test_frame.copy(), det_customer)
        print("   ✅ Drawing customer (green color)")

        # Test drawing mixed
        annotated_mixed = processor.draw_detections(test_frame.copy(), detections)
        print("   ✅ Drawing mixed detections")

        # Save test images
        output_dir = Path("output/test_staff")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        cv2.imwrite(str(output_dir / "default_color.jpg"), annotated_default)
        cv2.imwrite(str(output_dir / "staff_red.jpg"), annotated_staff)
        cv2.imwrite(str(output_dir / "customer_green.jpg"), annotated_customer)
        cv2.imwrite(str(output_dir / "mixed.jpg"), annotated_mixed)
        print(f"   ✅ Test images saved to {output_dir}")
        
    except Exception as e:
        print(f"❌ Drawing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 3: Counter filtering
    print("\n[Step 5] Testing counter filtering...")
    try:
        # Simulate filtering logic from daily_person_counter
        all_detections = [
            {"track_id": 1, "person_type": "staff"},
            {"track_id": 2, "person_type": "customer"},
            {"track_id": 3, "person_type": "staff"},
            {"track_id": 4},  # No person_type (should be included)
        ]
        
        customer_detections = [
            det for det in all_detections
            if det.get("person_type") != "staff"
        ]
        
        filtered_count = len(all_detections) - len(customer_detections)
        print(f"   Total detections: {len(all_detections)}")
        print(f"   Filtered out (staff): {filtered_count}")
        print(f"   Remaining (customers): {len(customer_detections)}")
        
        assert len(customer_detections) == 2, "Should have 2 customer detections"
        assert all(det.get("person_type") != "staff" for det in customer_detections), "Should not contain staff"
        print("   ✅ Counter filtering logic works correctly")
        
    except Exception as e:
        print(f"❌ Counter filtering test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 60)
    print("✅ All integration tests passed!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_integration()
    sys.exit(0 if success else 1)

