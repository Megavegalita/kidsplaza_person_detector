#!/usr/bin/env python3
"""
Integration test for Phase 1: Environment Setup.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest


class TestEnvironmentSetup:
    """Test environment setup for Phase 1."""
    
    def test_python_version(self):
        """Test Python version is 3.11+."""
        assert sys.version_info.major == 3
        assert sys.version_info.minor >= 11
        print(f"✅ Python version: {sys.version}")
    
    def test_import_torch(self):
        """Test PyTorch installation."""
        import torch
        assert torch.__version__ is not None
        print(f"✅ PyTorch version: {torch.__version__}")
    
    def test_mps_available(self):
        """Test MPS backend is available."""
        import torch
        assert torch.backends.mps.is_available() is True
        assert torch.backends.mps.is_built() is True
        print("✅ MPS backend available and built")
    
    def test_import_opencv(self):
        """Test OpenCV installation."""
        import cv2
        assert cv2.__version__ is not None
        print(f"✅ OpenCV version: {cv2.__version__}")
    
    def test_import_ultralytics(self):
        """Test Ultralytics installation."""
        from ultralytics import YOLO
        assert YOLO is not None
        print("✅ Ultralytics installed")
    
    def test_import_postgresql(self):
        """Test PostgreSQL library installation."""
        import psycopg2
        assert psycopg2.__version__ is not None
        print("✅ psycopg2 installed")
    
    def test_import_redis(self):
        """Test Redis library installation."""
        import redis
        assert hasattr(redis, '__version__')
        print("✅ redis installed")
    
    def test_import_numpy(self):
        """Test NumPy installation."""
        import numpy as np
        assert np.__version__ is not None
        print(f"✅ NumPy version: {np.__version__}")
    
    def test_module_structure(self):
        """Test module structure exists."""
        base_path = Path(__file__).parent.parent.parent
        
        required_modules = [
            "src/modules/camera",
            "src/modules/detection",
            "src/modules/tracking",
            "src/modules/demographics",
            "src/modules/database",
            "src/modules/utils",
            "src/scripts"
        ]
        
        for module in required_modules:
            module_path = base_path / module
            assert module_path.exists(), f"Module {module} should exist"
            assert (module_path / "__init__.py").exists(), f"{module}/__init__.py should exist"
        
        print("✅ Module structure complete")
    
    def test_config_files_exist(self):
        """Test configuration files exist."""
        base_path = Path(__file__).parent.parent.parent
        
        config_files = [
            "input/cameras_config/kidsplaza_thanhxuan.json",
            "config/database.json"
        ]
        
        for config_file in config_files:
            config_path = base_path / config_file
            assert config_path.exists(), f"Config file {config_file} should exist"
        
        print("✅ Configuration files exist")


class TestPhase1Features:
    """Test specific Phase 1 features."""
    
    def test_yolov8n_loading(self):
        """Test YOLOv8n model can be loaded."""
        from ultralytics import YOLO
        import os
        
        # Load model (will download if not exists)
        model_path = "yolov8n.pt"
        
        if os.path.exists(model_path):
            model = YOLO(model_path)
            assert model is not None
            print("✅ YOLOv8n model loaded successfully")
        else:
            # Skip if model not downloaded yet
            pytest.skip("Model file not found, download it first")
    
    def test_benchmark_script_exists(self):
        """Test benchmark script exists."""
        base_path = Path(__file__).parent.parent.parent
        benchmark_path = base_path / "src" / "scripts" / "benchmark_yolov8.py"
        
        assert benchmark_path.exists(), "benchmark_yolov8.py should exist"
        assert os.access(benchmark_path, os.X_OK), "benchmark_yolov8.py should be executable"
        print("✅ Benchmark script exists and is executable")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

