#!/usr/bin/env python3
"""
Test staff detection với video và nhiều mức confidence threshold.

So sánh kết quả classification với các threshold khác nhau để tìm giá trị tối ưu.
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
    frame_skip: int = 30,  # Process every 30 frames (~1 second at 30fps)
) -> Dict:
    """
    Process video với một threshold cụ thể.

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

    # Initialize classifier
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
        "total_detections": 0,
        "staff_count": 0,
        "customer_count": 0,
        "no_classification": 0,
        "staff_confidences": [],
        "customer_confidences": [],
        "processing_time": 0.0,
    }

    frame_num = 0
    detections_by_type = defaultdict(list)

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

        # Simulate detections (you would normally use YOLOv8 here)
        # For testing, we'll use a simple approach: treat entire frame as detection
        # In real scenario, this would be person detections from YOLOv8

        # Create dummy detection (center region of frame)
        h, w = frame.shape[:2]
        crop_size = min(h, w) // 3
        x1 = w // 2 - crop_size // 2
        y1 = h // 2 - crop_size // 2
        x2 = x1 + crop_size
        y2 = y1 + crop_size

        crop = frame[y1:y2, x1:x2]

        if crop.size > 0:
            try:
                person_type, confidence = classifier.classify(crop)
                stats["total_detections"] += 1

                if person_type == "staff":
                    stats["staff_count"] += 1
                    stats["staff_confidences"].append(confidence)
                    detections_by_type["staff"].append({
                        "frame": frame_num,
                        "confidence": confidence,
                    })
                elif person_type == "customer":
                    stats["customer_count"] += 1
                    stats["customer_confidences"].append(confidence)
                    detections_by_type["customer"].append({
                        "frame": frame_num,
                        "confidence": confidence,
                    })
                else:
                    stats["no_classification"] += 1

            except Exception as e:
                logger.warning(f"Classification failed at frame {frame_num}: {e}")

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
    else:
        stats["avg_staff_confidence"] = 0.0
        stats["max_staff_confidence"] = 0.0
        stats["min_staff_confidence"] = 0.0

    if stats["customer_confidences"]:
        stats["avg_customer_confidence"] = np.mean(stats["customer_confidences"])
        stats["max_customer_confidence"] = np.max(stats["customer_confidences"])
        stats["min_customer_confidence"] = np.min(stats["customer_confidences"])
    else:
        stats["avg_customer_confidence"] = 0.0
        stats["max_customer_confidence"] = 0.0
        stats["min_customer_confidence"] = 0.0

    # Print summary
    print(f"\nResults for threshold {threshold:.2f}:")
    print(f"  Frames processed: {stats['total_frames_processed']}")
    print(f"  Total detections: {stats['total_detections']}")
    print(f"  Staff: {stats['staff_count']} ({stats['staff_count']/max(stats['total_detections'],1)*100:.1f}%)")
    print(f"  Customer: {stats['customer_count']} ({stats['customer_count']/max(stats['total_detections'],1)*100:.1f}%)")
    print(f"  No classification: {stats['no_classification']}")
    if stats["staff_confidences"]:
        print(f"  Staff confidence: avg={stats['avg_staff_confidence']:.3f}, "
              f"min={stats['min_staff_confidence']:.3f}, max={stats['max_staff_confidence']:.3f}")
    if stats["customer_confidences"]:
        print(f"  Customer confidence: avg={stats['avg_customer_confidence']:.3f}, "
              f"min={stats['min_customer_confidence']:.3f}, max={stats['max_customer_confidence']:.3f}")
    print(f"  Processing time: {stats['processing_time']:.2f}s")

    return stats


def compare_results(all_results: List[Dict]) -> None:
    """So sánh và in kết quả từ nhiều threshold."""
    print("\n" + "="*80)
    print("COMPARISON SUMMARY")
    print("="*80)

    # Create comparison table
    print(f"\n{'Threshold':<12} {'Staff':<8} {'Customer':<10} {'Staff%':<10} {'Avg Staff Conf':<15} {'Avg Cust Conf':<15}")
    print("-" * 80)

    for result in all_results:
        threshold = result["threshold"]
        staff = result["staff_count"]
        customer = result["customer_count"]
        total = result["total_detections"]
        staff_pct = (staff / max(total, 1)) * 100
        avg_staff_conf = result.get("avg_staff_confidence", 0.0)
        avg_cust_conf = result.get("avg_customer_confidence", 0.0)

        print(f"{threshold:<12.2f} {staff:<8} {customer:<10} {staff_pct:<10.1f} "
              f"{avg_staff_conf:<15.3f} {avg_cust_conf:<15.3f}")

    # Find recommended threshold
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)

    # Find threshold with balanced results
    best_threshold = None
    best_score = -1

    for result in all_results:
        # Score based on: reasonable staff detection rate + good confidence
        staff_rate = result["staff_count"] / max(result["total_detections"], 1)
        avg_conf = result.get("avg_staff_confidence", 0.0)

        # Ideal: 10-30% staff detection rate with confidence > 0.5
        if 0.1 <= staff_rate <= 0.3 and avg_conf > 0.5:
            score = avg_conf * (1 - abs(staff_rate - 0.2))  # Prefer ~20% staff rate
            if score > best_score:
                best_score = score
                best_threshold = result["threshold"]

    if best_threshold is not None:
        print(f"\n✅ Recommended threshold: {best_threshold:.2f}")
        print(f"   (Based on balanced staff detection rate and confidence)")
    else:
        print("\n⚠️  No threshold found with ideal balance")
        print("   Consider:")
        print("   - Lower threshold if too few staff detected")
        print("   - Higher threshold if too many false positives")

    # Save results to JSON
    output_file = Path("output/test_staff/threshold_comparison.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n📄 Detailed results saved to: {output_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test staff detection with multiple confidence thresholds"
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

    print("="*80)
    print("STAFF DETECTION THRESHOLD TESTING")
    print("="*80)
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

