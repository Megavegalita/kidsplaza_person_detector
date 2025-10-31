#!/usr/bin/env python3
"""
Camera reader module for RTSP streams.

This module provides functionality to read frames from RTSP camera streams.
"""

import logging
from typing import Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class CameraReaderError(Exception):
    """Raised when camera reading errors occur."""

    pass


class CameraReader:
    """Manages RTSP camera stream reading."""

    def __init__(
        self, rtsp_url: str, reconnect_delay: int = 5, timeout: int = 10
    ) -> None:
        """
        Initialize camera reader.

        Args:
            rtsp_url: RTSP URL of the camera
            reconnect_delay: Delay in seconds before reconnecting
            timeout: Connection timeout in seconds

        Raises:
            CameraReaderError: If initialization fails
        """
        self.rtsp_url = rtsp_url
        self.reconnect_delay = reconnect_delay
        self.timeout = timeout
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_connected = False
        self.last_frame: Optional[np.ndarray] = None
        self.frame_count = 0
        self._connect()

    def _connect(self) -> None:
        """Connect to RTSP stream."""
        try:
            logger.info(f"Connecting to RTSP stream: {self.rtsp_url}")

            # Create VideoCapture with RTSP URL
            self.cap = cv2.VideoCapture(self.rtsp_url)

            # Set buffer size to reduce latency
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            if not self.cap.isOpened():
                raise CameraReaderError(f"Failed to open RTSP stream: {self.rtsp_url}")

            # Test frame read to verify connection
            assert self.cap is not None
            assert self.cap is not None
            cap = self.cap
            if cap is None:
                raise CameraReaderError("VideoCapture not initialized after connect")
            ret, frame = cap.read()
            if not ret:
                raise CameraReaderError(
                    f"Failed to read initial frame from: {self.rtsp_url}"
                )

            self.is_connected = True
            self.last_frame = frame
            logger.info("Successfully connected to RTSP stream")

        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.is_connected = False
            raise CameraReaderError(f"Connection failed: {e}") from e

    def read_frame(self) -> Optional[np.ndarray]:
        """
        Read a frame from the camera stream.

        Returns:
            Frame as numpy array or None if read failed

        Raises:
            CameraReaderError: If connection is lost and reconnect fails
        """
        try:
            if not self.is_connected or self.cap is None:
                logger.warning("Camera not connected, attempting reconnect...")
                self._connect()

            cap = self.cap
            if cap is None:
                raise CameraReaderError("VideoCapture not initialized")
            ret, frame = cap.read()

            if not ret:
                logger.warning("Failed to read frame, trying reconnect...")
                self._connect()
                cap = self.cap
                if cap is None:
                    raise CameraReaderError(
                        "VideoCapture not initialized after reconnect"
                    )
                ret, frame = cap.read()

                if not ret:
                    raise CameraReaderError("Failed to read frame after reconnect")

            self.last_frame = frame
            self.frame_count += 1
            return frame

        except Exception as e:
            logger.error(f"Error reading frame: {e}")
            return None

    def get_frame_size(self) -> Optional[Tuple[int, int]]:
        """
        Get current frame dimensions.

        Returns:
            Tuple of (width, height) or None if no frame available
        """
        if self.last_frame is not None:
            height, width = self.last_frame.shape[:2]
            return (width, height)
        return None

    def get_fps(self) -> float:
        """
        Get camera frame rate.

        Returns:
            FPS value
        """
        if self.cap is not None:
            return self.cap.get(cv2.CAP_PROP_FPS)
        return 0.0

    def is_streaming(self) -> bool:
        """
        Check if stream is active.

        Returns:
            True if streaming, False otherwise
        """
        return self.is_connected and self.cap is not None and self.cap.isOpened()

    def release(self) -> None:
        """Release camera resources."""
        if self.cap is not None:
            self.cap.release()
            self.is_connected = False
            logger.info("Camera resources released")

    def __enter__(self) -> "CameraReader":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.release()

    def __del__(self) -> None:
        """Cleanup on deletion."""
        self.release()


if __name__ == "__main__":
    # Test the module
    import sys

    logging.basicConfig(level=logging.INFO)

    try:
        # Test with first channel
        rtsp_url = "rtsp://user1:cam12345@14.177.236.96:554/cam/realmonitor?channel=1&subtype=0"

        print(f"Testing RTSP connection: {rtsp_url[:50]}...")

        with CameraReader(rtsp_url) as reader:
            print("✅ Connected successfully")
            print(f"Frame size: {reader.get_frame_size()}")
            print(f"FPS: {reader.get_fps()}")

            # Test reading a frame
            frame = reader.read_frame()
            if frame is not None:
                print(f"✅ Frame read successfully (shape: {frame.shape})")
            else:
                print("❌ Failed to read frame")
                sys.exit(1)

        print("\n✅ Camera reader test passed")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
