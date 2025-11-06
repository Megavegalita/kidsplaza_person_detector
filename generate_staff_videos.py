#!/usr/bin/env python3
"""
Generate video output với staff detection annotations cho các threshold khác nhau.

Tạo video output với bounding boxes màu đỏ cho staff và màu xanh cho customer.
"""

import argparse
import logging
import sys
import time
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
    output_path: Path,
    max_duration_seconds: int = 60,
    frame_skip: int = 1,  # Process every frame for video output
) -> Dict:
    """
    Process video và tạo output video với annotations.

    Args:
        video_path: Path to input video file
        threshold: Confidence threshold for staff classification
        output_path: Path to output video file
        max_duration_seconds: Maximum duration to process
        frame_skip: Process every N frames (1 = all frames)

    Returns:
        Dictionary with statistics
    """
    print(f"\n{'='*60}")
    print(f"Processing with threshold: {threshold:.2f}")
    print(f"Output: {output_path}")
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
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    max_frames = int(fps * max_duration_seconds)

    print(f"Input: {video_path.name}")
    print(f"Resolution: {width}x{height}")
    print(f"FPS: {fps:.2f}")
    print(f"Processing: {max_frames} frames ({max_duration_seconds}s)")

    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(
        str(output_path),
        fourcc,
        fps,
        (width, height),
    )

    # Statistics
    stats = {
        "threshold": threshold,
        "total_frames_processed": 0,
        "total_person_detections": 0,
        "total_classifications": 0,
        "staff_count": 0,
        "customer_count": 0,
    }

    frame_num = 0
    start_time = time.time()

    while frame_num < max_frames:
        ret, frame = cap.read()
        if not ret:
            break

        # Skip frames if needed
        if frame_num % frame_skip != 0:
            frame_num += 1
            continue

        stats["total_frames_processed"] += 1
        annotated_frame = frame.copy()

        try:
            # Step 1: Detect persons with YOLOv8
            detections, _ = detector.detect(frame, return_image=False)
            person_detections = [
                det for det in detections
                if det.get("class_id", -1) == 0  # Person class
            ]

            stats["total_person_detections"] += len(person_detections)

            # Step 2: Classify each person as staff or customer
            display_detections = []
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

                        # Add to detection for drawing
                        det_copy = det.copy()
                        det_copy["person_type"] = person_type
                        det_copy["staff_confidence"] = confidence
                        display_detections.append(det_copy)

                        if person_type == "staff":
                            stats["staff_count"] += 1
                        elif person_type == "customer":
                            stats["customer_count"] += 1

                    except Exception as e:
                        logger.debug(f"Classification failed: {e}")
                        # Still add detection without classification
                        display_detections.append(det)

            # Draw detections with color coding
            if display_detections:
                annotated_frame = processor.draw_detections(
                    annotated_frame,
                    display_detections,
                )

            # Add text overlay with statistics
            overlay_text = [
                f"Threshold: {threshold:.2f}",
                f"Frame: {frame_num}",
                f"Staff: {stats['staff_count']}",
                f"Customer: {stats['customer_count']}",
            ]
            y_offset = 30
            for text in overlay_text:
                cv2.putText(
                    annotated_frame,
                    text,
                    (10, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2,
                )
                cv2.putText(
                    annotated_frame,
                    text,
                    (10, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 0),
                    1,
                )
                y_offset += 30

            # Write frame to output video
            out.write(annotated_frame)

        except Exception as e:
            logger.warning(f"Frame {frame_num} processing failed: {e}")
            # Write original frame if processing fails
            out.write(frame)

        frame_num += 1

        # Progress update
        if frame_num % (int(fps) * 5) == 0:  # Every 5 seconds
            elapsed = time.time() - start_time
            progress = (frame_num / max_frames) * 100
            print(f"  Progress: {progress:.1f}% ({frame_num}/{max_frames} frames, {elapsed:.1f}s)")

    cap.release()
    out.release()

    stats["processing_time"] = time.time() - start_time

    # Print summary
    print(f"\n✅ Completed: {output_path.name}")
    print(f"  Frames processed: {stats['total_frames_processed']}")
    print(f"  Person detections: {stats['total_person_detections']}")
    print(f"  Classifications: {stats['total_classifications']}")
    print(f"  Staff: {stats['staff_count']} ({stats['staff_count']/max(stats['total_classifications'],1)*100:.1f}%)")
    print(f"  Customer: {stats['customer_count']} ({stats['customer_count']/max(stats['total_classifications'],1)*100:.1f}%)")
    print(f"  Processing time: {stats['processing_time']:.2f}s")

    return stats


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate video output with staff detection annotations"
    )
    parser.add_argument(
        "--video",
        type=str,
        default="input/video/Binh Xa-Thach That_ch4_20251024102450_20251024112450.mp4",
        help="Path to input video file",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output/test_staff/videos",
        help="Output directory for videos",
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
        default=1,
        help="Process every N frames (1 = all frames)",
    )

    args = parser.parse_args()

    video_path = Path(args.video)
    if not video_path.exists():
        print(f"❌ Video not found: {video_path}")
        sys.exit(1)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print("STAFF DETECTION VIDEO OUTPUT GENERATION")
    print("="*80)
    print(f"Input video: {video_path}")
    print(f"Output directory: {output_dir}")
    print(f"Duration: {args.duration}s")
    print(f"Thresholds: {args.thresholds}")
    print(f"Frame skip: {args.frame_skip}")

    # Process with each threshold
    all_stats = []
    for threshold in args.thresholds:
        try:
            output_filename = f"staff_detection_threshold_{threshold:.2f}.mp4"
            output_path = output_dir / output_filename

            stats = process_video_with_threshold(
                video_path=video_path,
                threshold=threshold,
                output_path=output_path,
                max_duration_seconds=args.duration,
                frame_skip=args.frame_skip,
            )
            all_stats.append(stats)

        except Exception as e:
            logger.error(f"Failed to process with threshold {threshold}: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"\nGenerated {len(all_stats)} videos:")
    for stats in all_stats:
        threshold = stats["threshold"]
        output_file = output_dir / f"staff_detection_threshold_{threshold:.2f}.mp4"
        print(f"  Threshold {threshold:.2f}: {output_file}")
        print(f"    Staff: {stats['staff_count']} ({stats['staff_count']/max(stats['total_classifications'],1)*100:.1f}%)")
        print(f"    Customer: {stats['customer_count']} ({stats['customer_count']/max(stats['total_classifications'],1)*100:.1f}%)")

    print(f"\n✅ All videos saved to: {output_dir}")


if __name__ == "__main__":
    main()

