#!/usr/bin/env python3
"""
Test staff detection với full pipeline: YOLOv8 detection -> Staff classification.

Test với video thực tế và nhiều threshold để tìm giá trị tối ưu.
"""

import argparse
import json
import logging
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

import cv2
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.modules.detection.detector import Detector
from src.modules.detection.staff_classifier import StaffClassifier
from src.modules.detection.image_processor import ImageProcessor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def process_video_with_threshold(
    video_path: Path,
    threshold: float,
    max_duration_seconds: int = 60,
    frame_skip: int = 30,
) -> Dict:
    """
    Process video với full pipeline: YOLOv8 -> Staff classification.

    Args:
        video_path: Path to video file
        threshold: Confidence threshold for staff classification
        max_duration_seconds: Maximum duration to process
        frame_skip: Process every N frames

    Returns:
        Dictionary with statistics
    """
    print(f"\n{'='*60}")
    print(f"Testing with threshold: {threshold:.2f}")
    print(f"{'='*60}")

    # Initialize components
    detector = Detector(model_path="yolov8n.pt", conf_threshold=0.5)
    classifier = StaffClassifier(
        model_path="models/kidsplaza/best.pt",
        conf_threshold=threshold,
    )
    processor = ImageProcessor()

    # Open video
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    max_frames = int(fps * max_duration_seconds)

    print(f"Video: {video_path.name}")
    print(f"FPS: {fps:.2f}")
    print(f"Total frames: {total_frames}")
    print(f"Processing: {max_frames} frames ({max_duration_seconds}s)")

    # Statistics
    stats = {
        "threshold": threshold,
        "total_frames_processed": 0,
        "total_person_detections": 0,
        "total_classifications": 0,
        "staff_count": 0,
        "customer_count": 0,
        "no_classification": 0,
        "staff_confidences": [],
        "customer_confidences": [],
        "processing_time": 0.0,
        "detections_by_frame": [],
    }

    frame_num = 0
    start_time = time.time()

    while frame_num < max_frames:
        ret, frame = cap.read()
        if not ret:
            break

        # Skip frames
        if frame_num % frame_skip != 0:
            frame_num += 1
            continue

        stats["total_frames_processed"] += 1

        try:
            # Step 1: Detect persons with YOLOv8
            detections, _ = detector.detect(frame, return_image=False)
            person_detections = [
                det for det in detections
                if det.get("class_id", -1) == 0  # Person class
            ]

            stats["total_person_detections"] += len(person_detections)

            frame_stats = {
                "frame": frame_num,
                "persons": len(person_detections),
                "staff": 0,
                "customer": 0,
            }

            # Step 2: Classify each person as staff or customer
            for det in person_detections:
                bbox = det.get("bbox")
                if bbox is None:
                    continue

                # Crop person region
                x1, y1, x2, y2 = map(int, bbox)
                person_crop = processor.crop_person(
                    frame, np.array([x1, y1, x2, y2], dtype=np.int32)
                )

                if person_crop is not None and person_crop.size > 0:
                    try:
                        person_type, confidence = classifier.classify(person_crop)
                        stats["total_classifications"] += 1

                        if person_type == "staff":
                            stats["staff_count"] += 1
                            stats["staff_confidences"].append(confidence)
                            frame_stats["staff"] += 1
                        elif person_type == "customer":
                            stats["customer_count"] += 1
                            stats["customer_confidences"].append(confidence)
                            frame_stats["customer"] += 1
                        else:
                            stats["no_classification"] += 1

                    except Exception as e:
                        logger.debug(f"Classification failed: {e}")

            if frame_stats["persons"] > 0:
                stats["detections_by_frame"].append(frame_stats)

        except Exception as e:
            logger.warning(f"Frame {frame_num} processing failed: {e}")

        frame_num += 1

        # Progress update
        if frame_num % (frame_skip * 10) == 0:
            elapsed = time.time() - start_time
            progress = (frame_num / max_frames) * 100
            print(f"  Progress: {progress:.1f}% ({frame_num}/{max_frames} frames, {elapsed:.1f}s)")

    cap.release()

    stats["processing_time"] = time.time() - start_time

    # Calculate averages
    if stats["staff_confidences"]:
        stats["avg_staff_confidence"] = np.mean(stats["staff_confidences"])
        stats["max_staff_confidence"] = np.max(stats["staff_confidences"])
        stats["min_staff_confidence"] = np.min(stats["staff_confidences"])
        stats["std_staff_confidence"] = np.std(stats["staff_confidences"])
    else:
        stats["avg_staff_confidence"] = 0.0
        stats["max_staff_confidence"] = 0.0
        stats["min_staff_confidence"] = 0.0
        stats["std_staff_confidence"] = 0.0

    if stats["customer_confidences"]:
        stats["avg_customer_confidence"] = np.mean(stats["customer_confidences"])
        stats["max_customer_confidence"] = np.max(stats["customer_confidences"])
        stats["min_customer_confidence"] = np.min(stats["customer_confidences"])
        stats["std_customer_confidence"] = np.std(stats["customer_confidences"])
    else:
        stats["avg_customer_confidence"] = 0.0
        stats["max_customer_confidence"] = 0.0
        stats["min_customer_confidence"] = 0.0
        stats["std_customer_confidence"] = 0.0

    # Print summary
    print(f"\nResults for threshold {threshold:.2f}:")
    print(f"  Frames processed: {stats['total_frames_processed']}")
    print(f"  Person detections: {stats['total_person_detections']}")
    print(f"  Classifications: {stats['total_classifications']}")
    print(f"  Staff: {stats['staff_count']} ({stats['staff_count']/max(stats['total_classifications'],1)*100:.1f}%)")
    print(f"  Customer: {stats['customer_count']} ({stats['customer_count']/max(stats['total_classifications'],1)*100:.1f}%)")
    print(f"  No classification: {stats['no_classification']}")
    if stats["staff_confidences"]:
        print(f"  Staff confidence: avg={stats['avg_staff_confidence']:.3f}±{stats['std_staff_confidence']:.3f}, "
              f"min={stats['min_staff_confidence']:.3f}, max={stats['max_staff_confidence']:.3f}")
    if stats["customer_confidences"]:
        print(f"  Customer confidence: avg={stats['avg_customer_confidence']:.3f}±{stats['std_customer_confidence']:.3f}, "
              f"min={stats['min_customer_confidence']:.3f}, max={stats['max_customer_confidence']:.3f}")
    print(f"  Processing time: {stats['processing_time']:.2f}s")

    return stats


def compare_results(all_results: List[Dict]) -> None:
    """So sánh và in kết quả từ nhiều threshold."""
    print("\n" + "="*90)
    print("COMPARISON SUMMARY")
    print("="*90)

    # Create comparison table
    print(f"\n{'Threshold':<12} {'Persons':<10} {'Staff':<8} {'Customer':<10} {'Staff%':<10} "
          f"{'Avg Staff Conf':<15} {'Avg Cust Conf':<15}")
    print("-" * 90)

    for result in all_results:
        threshold = result["threshold"]
        persons = result["total_person_detections"]
        staff = result["staff_count"]
        customer = result["customer_count"]
        total_class = result["total_classifications"]
        staff_pct = (staff / max(total_class, 1)) * 100
        avg_staff_conf = result.get("avg_staff_confidence", 0.0)
        avg_cust_conf = result.get("avg_customer_confidence", 0.0)

        print(f"{threshold:<12.2f} {persons:<10} {staff:<8} {customer:<10} {staff_pct:<10.1f} "
              f"{avg_staff_conf:<15.3f} {avg_cust_conf:<15.3f}")

    # Find recommended threshold
    print("\n" + "="*90)
    print("RECOMMENDATIONS")
    print("="*90)

    # Find threshold with balanced results
    best_threshold = None
    best_score = -1

    for result in all_results:
        # Score based on: reasonable staff detection rate + good confidence + consistency
        total_class = result["total_classifications"]
        if total_class == 0:
            continue

        staff_rate = result["staff_count"] / total_class
        avg_staff_conf = result.get("avg_staff_confidence", 0.0)
        std_staff_conf = result.get("std_staff_confidence", 0.0)

        # Ideal: 10-30% staff detection rate with confidence > 0.5 and low std
        if 0.1 <= staff_rate <= 0.3 and avg_staff_conf > 0.5:
            # Score: higher confidence * (1 - deviation from 20% staff rate) * (1 - std)
            score = avg_staff_conf * (1 - abs(staff_rate - 0.2)) * (1 - min(std_staff_conf, 0.3))
            if score > best_score:
                best_score = score
                best_threshold = result["threshold"]

    if best_threshold is not None:
        print(f"\n✅ Recommended threshold: {best_threshold:.2f}")
        print(f"   (Based on balanced staff detection rate (~20%), confidence > 0.5, and consistency)")
    else:
        print("\n⚠️  No threshold found with ideal balance")
        print("   Consider:")
        print("   - Lower threshold (0.3-0.4) if too few staff detected")
        print("   - Higher threshold (0.6-0.7) if too many false positives")

    # Save results to JSON
    output_file = Path("output/test_staff/threshold_comparison_full.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n📄 Detailed results saved to: {output_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test staff detection with full pipeline (YOLOv8 + Staff Classifier)"
    )
    parser.add_argument(
        "--video",
        type=str,
        default="input/video/Binh Xa-Thach That_ch4_20251024102450_20251024112450.mp4",
        help="Path to video file",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Duration to process in seconds",
    )
    parser.add_argument(
        "--thresholds",
        type=float,
        nargs="+",
        default=[0.3, 0.4, 0.5, 0.6, 0.7],
        help="Confidence thresholds to test",
    )
    parser.add_argument(
        "--frame-skip",
        type=int,
        default=30,
        help="Process every N frames",
    )

    args = parser.parse_args()

    video_path = Path(args.video)
    if not video_path.exists():
        print(f"❌ Video not found: {video_path}")
        sys.exit(1)

    print("="*90)
    print("STAFF DETECTION THRESHOLD TESTING (Full Pipeline)")
    print("="*90)
    print(f"Video: {video_path}")
    print(f"Duration: {args.duration}s")
    print(f"Thresholds to test: {args.thresholds}")
    print(f"Frame skip: {args.frame_skip}")

    # Process with each threshold
    all_results = []
    for threshold in args.thresholds:
        try:
            result = process_video_with_threshold(
                video_path=video_path,
                threshold=threshold,
                max_duration_seconds=args.duration,
                frame_skip=args.frame_skip,
            )
            all_results.append(result)
        except Exception as e:
            logger.error(f"Failed to process with threshold {threshold}: {e}")
            import traceback
            traceback.print_exc()

    # Compare results
    if all_results:
        compare_results(all_results)
    else:
        print("❌ No results to compare")
        sys.exit(1)


if __name__ == "__main__":
    main()

