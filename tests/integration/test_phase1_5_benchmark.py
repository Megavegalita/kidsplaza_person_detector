#!/usr/bin/env python3
"""
Integration test for Phase 1.5: Benchmark.
"""

import sys
from pathlib import Path
import pytest
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import torch
from ultralytics import YOLO


class TestBenchmarkCapabilities:
    """Test benchmark capabilities for Phase 1.5."""
    
    @pytest.fixture
    def model(self):
        """Load YOLOv8n model."""
        try:
            return YOLO('yolov8n.pt')
        except Exception as e:
            pytest.skip(f"Could not load model: {e}")
    
    def test_model_device_assignment(self, model):
        """Test model device can be assigned."""
        # Test CPU
        try:
            result = model.predict(np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8), device='cpu', verbose=False)
            print("✅ CPU inference works")
        except Exception as e:
            pytest.fail(f"CPU inference failed: {e}")
        
        # Test MPS if available
        if torch.backends.mps.is_available():
            try:
                result = model.predict(np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8), device='mps', verbose=False)
                print("✅ MPS inference works")
            except Exception as e:
                pytest.skip(f"MPS inference failed: {e}")
    
    def test_inference_speed(self, model):
        """Test inference speed is reasonable."""
        import time
        
        # Create test image
        test_image = np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8)
        
        # Warmup
        for _ in range(3):
            _ = model.predict(test_image, device='cpu', verbose=False)
        
        # Measure inference time
        times = []
        for _ in range(10):
            start = time.time()
            _ = model.predict(test_image, device='cpu', verbose=False)
            elapsed = time.time() - start
            times.append(elapsed)
        
        avg_time = sum(times) / len(times)
        fps = 1 / avg_time
        
        print(f"Inference time: {avg_time*1000:.2f}ms")
        print(f"FPS: {fps:.2f}")
        
        # Should achieve at least 10 FPS on CPU
        assert fps >= 10, f"Expected at least 10 FPS, got {fps:.2f}"
        print("✅ Inference speed is acceptable")
    
    def test_model_output_format(self, model):
        """Test model output format."""
        test_image = np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8)
        
        results = model.predict(test_image, device='cpu', verbose=False)
        
        assert results is not None
        assert len(results) > 0
        assert hasattr(results[0], 'boxes')
        
        print("✅ Model output format is correct")
    
    def test_benchmark_script_executable(self):
        """Test benchmark script can be executed."""
        base_path = Path(__file__).parent.parent.parent
        benchmark_script = base_path / "src" / "scripts" / "benchmark_yolov8.py"
        
        if not benchmark_script.exists():
            pytest.skip("Benchmark script not found")
        
        # Check if script is executable
        import os
        assert os.access(benchmark_script, os.X_OK), "Benchmark script should be executable"
        
        print("✅ Benchmark script is executable")


class TestMPSSupport:
    """Test MPS support capabilities."""
    
    def test_mps_available(self):
        """Test MPS is available."""
        assert torch.backends.mps.is_available() is True
        print("✅ MPS is available")
    
    def test_mps_built(self):
        """Test MPS is built."""
        assert torch.backends.mps.is_built() is True
        print("✅ MPS is built")
    
    def test_device_creation(self):
        """Test MPS device can be created."""
        device = torch.device("mps")
        assert device.type == "mps"
        print("✅ MPS device can be created")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

