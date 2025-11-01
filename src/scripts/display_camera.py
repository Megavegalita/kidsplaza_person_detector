#!/usr/bin/env python3
"""
Camera Display Script
Displays RTSP stream from specified camera channel.
"""

import argparse
import sys
from pathlib import Path
from typing import Dict

try:
    import cv2
except ImportError:
    print("Error: OpenCV (cv2) is not installed.")
    print("Please install it using: pip install opencv-python")
    sys.exit(1)


def load_camera_config(config_path: Path) -> Dict:
    """
    Load camera configuration from JSON file.

    Args:
        config_path: Path to the configuration JSON file

    Returns:
        Dictionary containing camera configuration
    """
    import json

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as file:
        config = json.load(file)

    return config


def display_camera_stream(rtsp_url: str, channel_name: str):
    """
    Display camera RTSP stream using OpenCV.

    Args:
        rtsp_url: Complete RTSP URL with credentials
        channel_name: Name of the camera channel
    """
    print(f"\n{'='*60}")
    print(f"Displaying: {channel_name}")
    print(f"URL: {rtsp_url}")
    print(f"{'='*60}")
    print("Press 'q' to quit")
    print("=" * 60)

    cap = cv2.VideoCapture(rtsp_url)

    if not cap.isOpened():
        print(f"Error: Could not open stream from {rtsp_url}")
        return

    # Set buffer size to reduce latency
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    frame_count = 0

    try:
        while True:
            ret, frame = cap.read()

            if not ret:
                print("Error: Failed to read frame from stream")
                break

            if frame is None or frame.size == 0:
                print("Error: Received empty frame")
                break

            frame_count += 1

            # Get frame properties
            height, width = frame.shape[:2]

            # Add text overlay with frame info
            fps_text = f"Frame: {frame_count}, Size: {width}x{height}"
            cv2.putText(
                frame, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2
            )
            cv2.putText(
                frame,
                channel_name,
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

            # Display the frame
            cv2.imshow("Camera Stream", frame)

            # Press 'q' to quit
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except KeyboardInterrupt:
        print("\nStream interrupted by user")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print(f"\nStream closed. Total frames: {frame_count}")


def main():
    """Main entry point for the camera display script."""
    parser = argparse.ArgumentParser(description="Display camera RTSP stream")
    parser.add_argument("channel", type=int, help="Camera channel number (1-4)")
    parser.add_argument(
        "--config",
        type=str,
        default="input/cameras_config/kidsplaza_thanhxuan.json",
        help="Path to camera configuration file",
    )

    args = parser.parse_args()

    # Validate channel number
    if not 1 <= args.channel <= 4:
        print(f"Error: Channel must be between 1 and 4, got {args.channel}")
        sys.exit(1)

    # Load configuration
    config_path = Path(args.config)
    try:
        config = load_camera_config(config_path)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)

    # Find the specified channel
    channel_config = None
    for channel in config["channels"]:
        if channel["channel_id"] == args.channel:
            channel_config = channel
            break

    if not channel_config:
        print(f"Error: Channel {args.channel} not found in configuration")
        sys.exit(1)

    # Display the camera stream
    display_camera_stream(channel_config["rtsp_url"], channel_config["name"])


if __name__ == "__main__":
    main()
