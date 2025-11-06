#!/usr/bin/env python3
"""
Test script for direction-based line counter with video.
Processes video and displays line zone with enter/exit events.
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import cv2
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.modules.counter.daily_person_counter import DailyPersonCounter
from src.modules.counter.person_identity_manager import PersonIdentityManager
from src.modules.counter.zone_counter import ZoneCounter
from src.modules.detection.detector import Detector
from src.modules.detection.image_processor import ImageProcessor
from src.modules.tracking.tracker import Tracker

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def draw_line_zone(
    frame: np.ndarray,
    zone: Dict,
    frame_width: int,
    frame_height: int,
    color: tuple = (0, 255, 255),
    thickness: int = 2,
) -> np.ndarray:
    """Draw line zone on frame."""
    # Get parsed zone from ZoneCounter (it converts percentage to absolute internally)
    # For drawing, we need to convert manually
    if zone.get("coordinate_type") == "percentage":
        start_percent = zone.get("start_point", (0, 0))
        end_percent = zone.get("end_point", (0, 0))
        start = (
            int(start_percent[0] * frame_width / 100.0),
            int(start_percent[1] * frame_height / 100.0),
        )
        end = (
            int(end_percent[0] * frame_width / 100.0),
            int(end_percent[1] * frame_height / 100.0),
        )
    else:
        start = tuple(map(int, zone.get("start_point", (0, 0))))
        end = tuple(map(int, zone.get("end_point", (0, 0))))

    # Draw line only (no arrow)
    cv2.line(frame, start, end, color, thickness)

    # Draw label with direction info
    direction = zone.get("direction", "one_way")
    label = f"{zone['name']} ({direction})"
    label_pos = ((start[0] + end[0]) // 2, (start[1] + end[1]) // 2 - 10)
    cv2.putText(
        frame,
        label,
        label_pos,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        color,
        2,
    )

    return frame


def main():
    parser = argparse.ArgumentParser(
        description="Test line direction counter with video"
    )
    parser.add_argument("video_path", type=str, help="Path to input video file")
    parser.add_argument(
        "--max-seconds",
        type=int,
        default=60,
        help="Process only first N seconds (default: 60)",
    )
    parser.add_argument(
        "--display", action="store_true", help="Display frames in window"
    )
    parser.add_argument(
        "--output-video",
        type=str,
        default=None,
        help="Output video path (default: output/videos/test_line_counter_<timestamp>.mp4)",
    )
    parser.add_argument(
        "--conf-threshold",
        type=float,
        default=0.35,
        help="Detection confidence threshold (default: 0.35)",
    )
    parser.add_argument(
        "--line-start",
        type=str,
        default="20,50",
        help="Line start point as 'x,y' percentage (default: 20,50)",
    )
    parser.add_argument(
        "--line-end",
        type=str,
        default="80,50",
        help="Line end point as 'x,y' percentage (default: 80,50)",
    )
    parser.add_argument(
        "--direction",
        type=str,
        default="left_to_right",
        choices=["left_to_right", "right_to_left", "top_to_bottom", "bottom_to_top"],
        help="Line direction (default: left_to_right)",
    )

    args = parser.parse_args()

    video_path = Path(args.video_path)
    if not video_path.exists():
        logger.error(f"Video file not found: {video_path}")
        return

    # Parse line points
    start_xy = tuple(map(float, args.line_start.split(",")))
    end_xy = tuple(map(float, args.line_end.split(",")))

    # Override for horizontal line in middle of screen, top_to_bottom direction
    if args.direction == "top_to_bottom":
        start_xy = (10.0, 50.0)  # Left side, middle height
        end_xy = (90.0, 50.0)  # Right side, middle height
        logger.info(
            "Using horizontal line in middle of screen for top_to_bottom direction"
        )

    # Open video
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        logger.error(f"Cannot open video: {video_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    logger.info(f"Video: {video_path.name} ({width}x{height} @ {fps:.2f} FPS)")

    # Setup detector and tracker
    detector = Detector(model_path="yolov8n.pt", conf_threshold=args.conf_threshold)
    tracker = Tracker(
        max_age=60,
        min_hits=2,
        iou_threshold=0.3,
        ema_alpha=0.5,
        reid_enable=False,
    )
    imgproc = ImageProcessor()

    # Setup zone counter with line zone
    line_zone = {
        "zone_id": "line_entrance",
        "name": "Entrance Line",
        "type": "line",
        "coordinate_type": "percentage",
        "start_point": list(start_xy),  # Use start_point for validation
        "end_point": list(end_xy),  # Use end_point for validation
        "direction": args.direction,
        "enter_threshold": 1,
        "exit_threshold": 1,
    }

    zone_counter = ZoneCounter([line_zone])
    identity_manager = PersonIdentityManager(redis_url=None)  # No Redis for test
    daily_counter = DailyPersonCounter([line_zone], identity_manager)

    logger.info(
        f"Line zone configured: {start_xy} -> {end_xy}, direction: {args.direction}"
    )

    # Setup video writer
    output_path = args.output_video
    if output_path is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_dir = Path("output/videos")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"test_line_counter_{timestamp}.mp4"
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video_writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
    logger.info(f"Output video: {output_path}")

    # Process video
    start_time = time.time()
    frame_num = 0
    total_enter = 0
    total_exit = 0
    events_log: List[Dict] = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_num += 1

        # Limit duration
        if time.time() - start_time >= args.max_seconds:
            logger.info(f"Reached max_seconds={args.max_seconds}, stopping")
            break

        # Detect persons
        detections, annotated = detector.detect(frame, return_image=True)

        # Track
        detections = tracker.update(detections, frame=frame, session_id="video_test")

        # Add track_id to detections for counter
        for det in detections:
            if "track_id" not in det:
                continue

        # Update counter
        counter_result = daily_counter.update(detections, frame, frame_num=frame_num)

        # Log events
        if counter_result.get("events"):
            for event in counter_result["events"]:
                event_type = event.get("type")
                track_id = event.get("track_id")
                zone_id = event.get("zone_id")

                if event_type == "enter":
                    total_enter += 1
                    logger.info(f"ENTER: Track {track_id} at frame {frame_num}")
                elif event_type == "exit":
                    total_exit += 1
                    logger.info(f"EXIT: Track {track_id} at frame {frame_num}")

                events_log.append(
                    {
                        "frame": frame_num,
                        "type": event_type,
                        "track_id": track_id,
                        "zone_id": zone_id,
                    }
                )

        # Draw detections
        if annotated is None:
            annotated = frame.copy()

        if len(detections) > 0:
            annotated = imgproc.draw_detections(annotated, detections)

        # Draw zone
        annotated = draw_line_zone(annotated, line_zone, width, height)

        # Draw counter info
        counts = counter_result.get("counts", {})
        zone_counts = counts.get("line_entrance", {})
        enter_count = zone_counts.get("enter", 0)
        exit_count = zone_counts.get("exit", 0)

        info_text = [
            f"Frame: {frame_num}",
            f"Enter: {enter_count}",
            f"Exit: {exit_count}",
            f"Direction: {args.direction}",
        ]

        y_offset = 30
        for text in info_text:
            cv2.putText(
                annotated,
                text,
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )
            y_offset += 30

        # Write frame to video
        video_writer.write(annotated)

        # Display
        if args.display:
            cv2.imshow("Line Direction Counter Test", annotated)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                logger.info("User pressed 'q', stopping")
                break

    cap.release()
    video_writer.release()
    if args.display:
        cv2.destroyAllWindows()

    logger.info(f"Video saved to: {output_path}")

    # Print summary
    elapsed = time.time() - start_time
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Video: {video_path.name}")
    logger.info(f"Frames processed: {frame_num}")
    logger.info(f"Processing time: {elapsed:.2f}s")
    logger.info(f"FPS: {frame_num / elapsed:.2f}")
    logger.info(f"Total ENTER events: {total_enter}")
    logger.info(f"Total EXIT events: {total_exit}")
    logger.info(f"Line zone: {start_xy} -> {end_xy}")
    logger.info(f"Direction: {args.direction}")
    logger.info("=" * 60)

    if events_log:
        logger.info("\nEvent log:")
        for event in events_log[:20]:  # Show first 20 events
            logger.info(
                f"  Frame {event['frame']}: {event['type'].upper()} - Track {event['track_id']}"
            )


if __name__ == "__main__":
    main()
