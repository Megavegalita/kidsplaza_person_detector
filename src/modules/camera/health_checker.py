#!/usr/bin/env python3
"""
Camera health checker module.

This module provides functionality to check camera stream health and status.
"""

import logging
import time
from typing import Dict, List, Optional, Tuple

from camera_reader import CameraReader, CameraReaderError

logger = logging.getLogger(__name__)


class HealthStatus:
    """Represents camera health status."""

    def __init__(
        self,
        is_healthy: bool,
        error_message: Optional[str] = None,
        frame_size: Optional[Tuple[int, int]] = None,
        fps: Optional[float] = None,
        response_time_ms: Optional[float] = None,
    ) -> None:
        """
        Initialize health status.

        Args:
            is_healthy: Whether camera is healthy
            error_message: Error message if not healthy
            frame_size: Frame dimensions (width, height)
            fps: Frame rate
            response_time_ms: Response time in milliseconds
        """
        self.is_healthy = is_healthy
        self.error_message = error_message
        self.frame_size = frame_size
        self.fps = fps
        self.response_time_ms = response_time_ms

    def to_dict(self) -> Dict:
        """Convert health status to dictionary."""
        return {
            "is_healthy": self.is_healthy,
            "error_message": self.error_message,
            "frame_size": self.frame_size,
            "fps": self.fps,
            "response_time_ms": self.response_time_ms,
        }

    def __repr__(self) -> str:
        """String representation."""
        if self.is_healthy:
            return f"Healthy (FPS: {self.fps}, Size: {self.frame_size})"
        return f"Unhealthy: {self.error_message}"


class CameraHealthChecker:
    """Checks health of camera streams."""

    def __init__(self, rtsp_url: str, timeout: int = 10, min_fps: float = 15.0) -> None:
        """
        Initialize camera health checker.

        Args:
            rtsp_url: RTSP URL to check
            timeout: Connection timeout in seconds
            min_fps: Minimum acceptable FPS
        """
        self.rtsp_url = rtsp_url
        self.timeout = timeout
        self.min_fps = min_fps

    def check_health(self) -> HealthStatus:
        """
        Check camera stream health.

        Returns:
            HealthStatus object with health information
        """
        start_time = time.time()

        try:
            reader = CameraReader(self.rtsp_url, timeout=self.timeout)

            # Read a test frame
            frame = reader.read_frame()

            if frame is None:
                return HealthStatus(
                    is_healthy=False,
                    error_message="Failed to read frame",
                    response_time_ms=(time.time() - start_time) * 1000,
                )

            # Get frame size and FPS
            frame_size = reader.get_frame_size()
            fps = reader.get_fps()

            # Check if FPS is acceptable
            if fps is not None and fps < self.min_fps:
                logger.warning(f"Low FPS detected: {fps} < {self.min_fps}")

            # Cleanup
            reader.release()

            response_time = (time.time() - start_time) * 1000

            return HealthStatus(
                is_healthy=True,
                frame_size=frame_size,
                fps=fps,
                response_time_ms=response_time,
            )

        except CameraReaderError as e:
            return HealthStatus(
                is_healthy=False,
                error_message=str(e),
                response_time_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            logger.error(f"Unexpected error during health check: {e}")
            return HealthStatus(
                is_healthy=False,
                error_message=f"Unexpected error: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000,
            )

    def check_connection(self) -> Tuple[bool, str]:
        """
        Quick connection check.

        Returns:
            Tuple of (is_connected, message)
        """
        try:
            reader = CameraReader(self.rtsp_url, timeout=5)
            reader.release()
            return (True, "Connection successful")
        except Exception as e:
            return (False, str(e))


def check_all_channels(config_path: str, timeout: int = 10) -> Dict[int, HealthStatus]:
    """
    Check health of all camera channels.

    Args:
        config_path: Path to camera configuration file
        timeout: Connection timeout in seconds

    Returns:
        Dictionary mapping channel IDs to health statuses
    """
    from pathlib import Path

    from camera_config import load_camera_config

    config = load_camera_config(Path(config_path))
    channels = config.get_channels()

    results = {}

    logger.info(f"Checking health of {len(channels)} channels...")

    for channel in channels:
        channel_id = channel["channel_id"]
        rtsp_url = channel["rtsp_url"]

        logger.info(f"Checking channel {channel_id}...")

        checker = CameraHealthChecker(rtsp_url, timeout=timeout)
        status = checker.check_health()
        results[channel_id] = status

        if status.is_healthy:
            logger.info(f"✅ Channel {channel_id}: Healthy")
        else:
            logger.warning(f"❌ Channel {channel_id}: {status.error_message}")

    return results


if __name__ == "__main__":
    # Test the module
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        config_path = "input/cameras_config/kidsplaza_thanhxuan.json"

        print("Testing camera health checker...")
        print("=" * 50)

        results = check_all_channels(config_path)

        print("\nResults:")
        print("=" * 50)

        healthy_count = sum(1 for s in results.values() if s.is_healthy)

        for channel_id, status in results.items():
            status_str = (
                "✅ Healthy" if status.is_healthy else f"❌ {status.error_message}"
            )
            print(f"Channel {channel_id}: {status_str}")
            if status.is_healthy:
                print(f"  Size: {status.frame_size}")
                print(f"  FPS: {status.fps}")

        print(f"\nSummary: {healthy_count}/{len(results)} channels healthy")

        if healthy_count == len(results):
            print("✅ All channels healthy")
            sys.exit(0)
        else:
            print(f"❌ {len(results) - healthy_count} channel(s) unhealthy")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
