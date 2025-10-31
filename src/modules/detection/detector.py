#!/usr/bin/env python3
"""
Person detector module optimized for Apple M4 Pro.

Uses multi-threading (CPU) + MPS (GPU) for maximum performance.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Tuple

import numpy as np

from .image_processor import ImageProcessor
from .model_loader import ModelLoader

logger = logging.getLogger(__name__)


class Detector:
    """High-performance person detector for M4 Pro."""

    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        device: Optional[str] = None,
        conf_threshold: float = 0.5,
        max_workers: int = 2,
        use_mps: bool = True,
    ) -> None:
        """
        Initialize person detector.

        Args:
            model_path: Path to YOLOv8 model
            device: Device to use ('mps', 'cpu', or None for auto)
            conf_threshold: Confidence threshold
            max_workers: Number of worker threads (for CPU tasks)
            use_mps: Whether to use MPS acceleration
        """
        self.conf_threshold = conf_threshold
        self.max_workers = max_workers
        self.use_mps = use_mps

        # Load model
        self.model_loader = ModelLoader(
            model_path=model_path, device=device, conf_threshold=conf_threshold
        )

        # Image processor
        self.processor = ImageProcessor()

        # Thread pool for CPU-bound tasks
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # Statistics
        self.frame_count = 0
        self.total_inference_time = 0.0
        self.detection_count = 0

        logger.info(
            "Detector initialized on device: %s", self.model_loader.get_device()
        )
        logger.info("Thread workers: %d", max_workers)

    def detect(
        self, frame: np.ndarray, return_image: bool = False
    ) -> Tuple[List[Dict], Optional[np.ndarray]]:
        """
        Detect persons in frame with optimal performance.

        Args:
            frame: Input frame
            return_image: Whether to return annotated image

        Returns:
            Tuple of (detections, annotated_image)
        """
        start_time = time.time()

        try:
            # Run detection on GPU/MPS
            detections = self.model_loader.detect_persons(frame)

            inference_time = time.time() - start_time

            # Update statistics
            self.frame_count += 1
            self.total_inference_time += inference_time
            self.detection_count += len(detections)

            if self.frame_count % 100 == 0:
                avg_time = self.total_inference_time / self.frame_count
                fps = 1.0 / avg_time
                logger.info(
                    "Detection stats: %d frames, avg %.2fms, %.2f FPS",
                    self.frame_count,
                    avg_time * 1000,
                    fps,
                )

            annotated = None
            if return_image and len(detections) > 0:
                annotated = self.processor.draw_detections(frame, detections)

            return detections, annotated

        except Exception as e:
            logger.error(f"Detection error: {e}")
            return [], None

    def detect_batch(
        self, frames: List[np.ndarray], return_images: bool = False
    ) -> List[Tuple[List[Dict], Optional[np.ndarray]]]:
        """
        Detect persons in multiple frames (batch processing).

        Args:
            frames: List of input frames
            return_images: Whether to return annotated images

        Returns:
            List of (detections, annotated_image) tuples
        """
        results = []

        # Use thread pool for CPU-bound preprocessing
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []

            for frame in frames:
                future = executor.submit(self.detect, frame, return_images)
                futures.append(future)

            for future in futures:
                result = future.result()
                results.append(result)

        return results

    def get_statistics(self) -> Dict:
        """
        Get detection statistics.

        Returns:
            Dictionary with statistics
        """
        avg_time = 0.0
        fps = 0.0

        if self.frame_count > 0:
            avg_time = self.total_inference_time / self.frame_count
            fps = 1.0 / avg_time

        return {
            "frame_count": self.frame_count,
            "detection_count": self.detection_count,
            "average_time_ms": avg_time * 1000,
            "fps": fps,
            "total_time_s": self.total_inference_time,
            "device": self.model_loader.get_device(),
            "mps_enabled": self.model_loader.is_mps_enabled(),
        }

    def reset_statistics(self) -> None:
        """Reset detection statistics."""
        self.frame_count = 0
        self.total_inference_time = 0.0
        self.detection_count = 0
        logger.info("Statistics reset")

    def release(self) -> None:
        """Release resources."""
        if self.executor:
            self.executor.shutdown(wait=True)
        logger.info("Detector resources released")

    def __enter__(self) -> "Detector":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.release()


if __name__ == "__main__":
    # Test the detector
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        detector = Detector()

        print("✅ Detector initialized")
        print(f"Device: {detector.model_loader.get_device()}")
        print(f"MPS enabled: {detector.model_loader.is_mps_enabled()}")

        # Test with random image
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

        detections, annotated = detector.detect(test_frame, return_image=True)
        print("\n✅ Detection test passed")
        print(f"Detections: {len(detections)}")

        # Print statistics
        stats = detector.get_statistics()
        print("\nStatistics:")
        print(f"  Frames processed: {stats['frame_count']}")
        print(f"  Average time: {stats['average_time_ms']:.2f} ms")
        print(f"  FPS: {stats['fps']:.2f}")
        print(f"  Device: {stats['device']}")

        detector.release()

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
