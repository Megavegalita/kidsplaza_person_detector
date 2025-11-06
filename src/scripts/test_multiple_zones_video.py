#!/usr/bin/env python3
"""
Test multiple counter zones with video.

Loads zones from camera config, filters by active flag, and processes video.
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.modules.camera.camera_config import load_camera_config
from src.modules.counter.daily_person_counter import DailyPersonCounter
from src.modules.counter.person_identity_manager import PersonIdentityManager
from src.modules.counter.zone_counter import ZoneCounter
from src.modules.detection.detector import Detector
from src.modules.detection.image_processor import ImageProcessor
from src.modules.tracking.tracker import Tracker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def draw_zone_polygon(
    frame: np.ndarray,
    zone: Dict,
    frame_width: int,
    frame_height: int,
    color: tuple = (0, 255, 255),
    thickness: int = 2,
) -> np.ndarray:
    """Draw polygon zone on frame."""
    if zone.get("coordinate_type") == "percentage":
        points_percent = zone.get("points_percent", [])
        points = [
            (
                int(x_percent * frame_width / 100.0),
                int(y_percent * frame_height / 100.0),
            )
            for x_percent, y_percent in points_percent
        ]
    else:
        points = [tuple(map(int, pt)) for pt in zone.get("points", [])]

    # Draw polygon
    pts = np.array(points, np.int32)
    pts = pts.reshape((-1, 1, 2))
    cv2.polylines(frame, [pts], True, color, thickness)

    # Draw label
    label = f"{zone['name']} ({zone.get('zone_id', 'unknown')})"
    # Find center point
    center_x = int(sum(p[0] for p in points) / len(points))
    center_y = int(sum(p[1] for p in points) / len(points))
    cv2.putText(
        frame,
        label,
        (center_x - 50, center_y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        color,
        2,
    )

    return frame


def draw_line_zone(
    frame: np.ndarray,
    zone: Dict,
    frame_width: int,
    frame_height: int,
    color: tuple = (0, 255, 255),
    thickness: int = 2,
) -> np.ndarray:
    """Draw line zone on frame."""
    # Handle both parsed zones (from ZoneCounter) and raw config zones
    if zone.get("coordinate_type") == "percentage":
        # Check for parsed zone format (from ZoneCounter)
        if "start_point_percent" in zone:
            start_percent = zone.get("start_point_percent", (0, 0))
            end_percent = zone.get("end_point_percent", (0, 0))
        else:
            # Raw config format
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
        # Absolute coordinates
        start = tuple(map(int, zone.get("start_point", (0, 0))))
        end = tuple(map(int, zone.get("end_point", (0, 0))))

    # Draw line only (no arrow) - make it thicker and more visible
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
        description="Test multiple counter zones with video from config"
    )
    parser.add_argument(
        "video_path",
        type=str,
        help="Path to input video file",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="input/cameras_config/kidsplaza_thanhxuan.json",
        help="Path to camera config file",
    )
    parser.add_argument(
        "--channel-id",
        type=int,
        default=4,
        help="Channel ID to load zones from",
    )
    parser.add_argument(
        "--max-seconds",
        type=int,
        default=60,
        help="Process only first N seconds (default: 60)",
    )
    parser.add_argument(
        "--conf-threshold",
        type=float,
        default=0.35,
        help="Detection confidence threshold (default: 0.35)",
    )
    parser.add_argument(
        "--output-video",
        type=str,
        default=None,
        help="Output video path (default: auto-generated)",
    )
    parser.add_argument(
        "--display",
        action="store_true",
        help="Display frames in window",
    )

    args = parser.parse_args()

    video_path = Path(args.video_path)
    if not video_path.exists():
        logger.error(f"Video file not found: {video_path}")
        return

    # Load camera config
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        return

    camera_config = load_camera_config(config_path)
    channel_features = camera_config.get_channel_features(args.channel_id)
    counter_config = channel_features.get("counter", {})

    if not counter_config.get("enabled", False):
        logger.error(f"Counter not enabled for channel {args.channel_id}")
        return

    # Get zones and filter by active
    all_zones = counter_config.get("zones", [])
    active_zones = [zone for zone in all_zones if zone.get("active", True) is True]

    if not active_zones:
        logger.error(f"No active zones found for channel {args.channel_id}")
        return

    logger.info(
        f"Loaded {len(active_zones)} active zones (out of {len(all_zones)} total)"
    )
    for zone in active_zones:
        logger.info(
            f"  - {zone.get('zone_id')}: {zone.get('name')} ({zone.get('type')})"
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

    # Setup zone counter with active zones
    zone_counter = ZoneCounter(active_zones)
    identity_manager = PersonIdentityManager(redis_url=None)  # No Redis for test
    daily_counter = DailyPersonCounter(active_zones, identity_manager)

    logger.info(f"Initialized ZoneCounter with {len(active_zones)} zones")

    # Setup video writer
    output_path = args.output_video
    if output_path is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_dir = Path("output/videos")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"test_multiple_zones_{timestamp}.mp4"
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video_writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
    logger.info(f"Output video: {output_path}")

    # Process video
    start_time = time.time()
    frame_num = 0
    events_log: List[Dict] = []
    zone_totals: Dict[str, Dict[str, int]] = {}

    # Initialize zone totals
    for zone in active_zones:
        zone_id = zone.get("zone_id")
        zone_totals[zone_id] = {"enter": 0, "exit": 0}

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

        # Log events and update totals
        if counter_result.get("events"):
            for event in counter_result["events"]:
                event_type = event.get("type")
                track_id = event.get("track_id")
                zone_id = event.get("zone_id")

                if zone_id in zone_totals:
                    zone_totals[zone_id][event_type] += 1

                logger.info(
                    f"Frame {frame_num}: {event_type.upper()} - Zone {zone_id} - Track {track_id}"
                )

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

        # Draw zones - use parsed zones from ZoneCounter
        parsed_zones = zone_counter.zones
        for zone in parsed_zones:
            zone_type = zone.get("type")
            if zone_type == "polygon":
                annotated = draw_zone_polygon(
                    annotated, zone, width, height, color=(0, 255, 255), thickness=3
                )
            elif zone_type == "line":
                annotated = draw_line_zone(
                    annotated, zone, width, height, color=(0, 255, 255), thickness=5
                )

        # Draw counter info
        counts = counter_result.get("counts", {})
        info_text = [f"Frame: {frame_num}"]

        for zone in active_zones:
            zone_id = zone.get("zone_id")
            zone_name = zone.get("name")
            zone_counts = counts.get(zone_id, {})
            enter_count = zone_counts.get("enter", 0)
            exit_count = zone_counts.get("exit", 0)
            info_text.append(f"{zone_name}: IN={enter_count} OUT={exit_count}")

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

        # Display if requested
        if args.display:
            cv2.imshow("Multiple Zones Test", annotated)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                logger.info("User pressed 'q', stopping")
                break

        # Write frame to video
        video_writer.write(annotated)

    # Cleanup
    cap.release()
    video_writer.release()
    if args.display:
        cv2.destroyAllWindows()

    # Summary
    elapsed = time.time() - start_time
    logger.info("=" * 60)
    logger.info(f"Frames processed: {frame_num}")
    logger.info(f"Processing time: {elapsed:.2f}s")
    logger.info(f"FPS: {frame_num / elapsed:.2f}")
    logger.info("")
    logger.info("Zone totals:")
    for zone_id, totals in zone_totals.items():
        logger.info(f"  {zone_id}: ENTER={totals['enter']}, EXIT={totals['exit']}")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Event log:")
    for event in events_log[:50]:  # Show first 50 events
        logger.info(
            f"  Frame {event['frame']}: {event['type'].upper()} - Zone {event['zone_id']} - Track {event['track_id']}"
        )
    if len(events_log) > 50:
        logger.info(f"  ... and {len(events_log) - 50} more events")


if __name__ == "__main__":
    main()
