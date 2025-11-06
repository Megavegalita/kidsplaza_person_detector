#!/usr/bin/env python3
"""
Benchmark YOLOv8n performance with MPS support.

This script tests YOLOv8n model performance on CPU and MPS (Metal GPU).
"""

import logging
import time

import torch
from ultralytics import YOLO

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_test_image(size: tuple = (640, 480)):
    """Create a test image for benchmarking."""
    import numpy as np

    img = np.random.randint(0, 255, (*size, 3), dtype=np.uint8)
    return img


def benchmark_model_inference(
    model: YOLO, device: str, num_runs: int = 10, image_size: tuple = (640, 480)
) -> dict:
    """Benchmark model inference on specified device."""
    logger.info(f"Benchmarking on {device} device...")

    # Create test image
    test_image = create_test_image(image_size)

    times = []

    # Warmup runs
    for _ in range(3):
        _ = model.predict(test_image, device=device, verbose=False)

    # Actual benchmark runs
    for i in range(num_runs):
        start_time = time.time()
        _ = model.predict(test_image, device=device, verbose=False)
        elapsed = time.time() - start_time
        times.append(elapsed)

        if (i + 1) % 5 == 0:
            logger.info(f"  Run {i + 1}/{num_runs} completed")

    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    fps = 1 / avg_time

    logger.info(f"  Average time: {avg_time*1000:.2f} ms")
    logger.info(f"  FPS: {fps:.2f}")
    logger.info(f"  Min time: {min_time*1000:.2f} ms")
    logger.info(f"  Max time: {max_time*1000:.2f} ms")

    return {
        "device": device,
        "average_time_ms": avg_time * 1000,
        "fps": fps,
        "min_time_ms": min_time * 1000,
        "max_time_ms": max_time * 1000,
        "num_runs": num_runs,
    }


def main():
    """Main benchmark function."""
    logger.info("Starting YOLOv8n Benchmark")
    logger.info("=" * 50)

    # Load model
    logger.info("Loading YOLOv8n model...")
    model = YOLO("yolov8n.pt")
    logger.info("Model loaded successfully")

    # Check available devices
    device_cpu = "cpu"
    device_mps = "mps" if torch.backends.mps.is_available() else None

    logger.info("CPU available: True")
    logger.info(f"MPS available: {torch.backends.mps.is_available()}")
    logger.info("")

    results = []

    # Benchmark on CPU
    logger.info("Testing on CPU...")
    cpu_result = benchmark_model_inference(model, device_cpu, num_runs=20)
    results.append(cpu_result)
    logger.info("")

    # Benchmark on MPS if available
    if device_mps:
        logger.info("Testing on MPS (Metal GPU)...")
        mps_result = benchmark_model_inference(model, device_mps, num_runs=20)
        results.append(mps_result)
        logger.info("")
    else:
        logger.warning("MPS not available, skipping GPU test")

    # Print summary
    logger.info("=" * 50)
    logger.info("BENCHMARK RESULTS SUMMARY")
    logger.info("=" * 50)

    for result in results:
        logger.info(f"\nDevice: {result['device'].upper()}")
        logger.info(f"  Average inference time: {result['average_time_ms']:.2f} ms")
        logger.info(f"  FPS: {result['fps']:.2f}")
        logger.info(
            f"  Time range: {result['min_time_ms']:.2f} - {result['max_time_ms']:.2f} ms"
        )

    # Compare devices if both tested
    if len(results) == 2:
        speedup = results[0]["average_time_ms"] / results[1]["average_time_ms"]
        logger.info(f"\nSpeedup (MPS vs CPU): {speedup:.2f}x")

        if speedup > 1:
            logger.info("✅ MPS is faster than CPU")
        else:
            logger.info("⚠️  CPU is faster than MPS (unusual)")

    logger.info("=" * 50)
    logger.info("Benchmark completed")

    return results


if __name__ == "__main__":
    main()
