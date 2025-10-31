#!/usr/bin/env python3
"""
Unit tests for camera reader module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from src.modules.camera.camera_reader import (
    CameraReader,
    CameraReaderError
)


class TestCameraReader:
    """Test cases for CameraReader class."""
    
    @pytest.fixture
    def sample_rtsp_url(self):
        """Sample RTSP URL."""
        return "rtsp://user:pass@192.168.1.100:554/stream"
    
    @pytest.fixture
    def mock_frame(self):
        """Create mock frame."""
        return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    @patch('cv2.VideoCapture')
    def test_initialization_success(self, mock_videocapture, sample_rtsp_url):
        """Test successful initialization."""
        # Mock successful connection
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_cap.get.return_value = 30.0
        mock_videocapture.return_value = mock_cap
        
        reader = CameraReader(sample_rtsp_url, timeout=1)
        
        assert reader.is_connected is True
        assert reader.cap is not None
    
    @patch('cv2.VideoCapture')
    def test_initialization_failure(self, mock_videocapture, sample_rtsp_url):
        """Test initialization failure."""
        # Mock failed connection
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_videocapture.return_value = mock_cap
        
        with pytest.raises(CameraReaderError):
            CameraReader(sample_rtsp_url, timeout=1)
    
    @patch('cv2.VideoCapture')
    def test_read_frame_success(self, mock_videocapture, sample_rtsp_url, mock_frame):
        """Test successful frame read."""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, mock_frame)
        mock_cap.get.return_value = 30.0
        mock_videocapture.return_value = mock_cap
        
        reader = CameraReader(sample_rtsp_url, timeout=1)
        frame = reader.read_frame()
        
        assert frame is not None
        assert frame.shape == mock_frame.shape
    
    @patch('cv2.VideoCapture')
    def test_read_frame_failure(self, mock_videocapture, sample_rtsp_url, mock_frame):
        """Test frame read failure."""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        # First read succeeds (in _connect), subsequent reads fail
        mock_cap.read.side_effect = [
            (True, mock_frame),  # Initial read in _connect
            (False, None)        # Subsequent reads fail
        ]
        mock_cap.get.return_value = 30.0
        mock_videocapture.return_value = mock_cap
        
        reader = CameraReader(sample_rtsp_url, timeout=1)
        
        # Now trying to read again should attempt reconnect and fail
        frame = reader.read_frame()
        # Should return None after reconnection attempt
        assert frame is None
    
    @patch('cv2.VideoCapture')
    def test_get_frame_size(self, mock_videocapture, sample_rtsp_url):
        """Test getting frame size."""
        mock_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, mock_frame)
        mock_cap.get.return_value = 30.0
        mock_videocapture.return_value = mock_cap
        
        reader = CameraReader(sample_rtsp_url, timeout=1)
        reader.read_frame()  # Need to read a frame first
        
        size = reader.get_frame_size()
        assert size == (640, 480)
    
    @patch('cv2.VideoCapture')
    def test_get_frame_size_no_frame(self, mock_videocapture, sample_rtsp_url):
        """Test getting frame size when no frame available."""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3)))
        mock_cap.get.return_value = 30.0
        mock_videocapture.return_value = mock_cap
        
        reader = CameraReader(sample_rtsp_url, timeout=1)
        
        # Without reading a frame
        size = reader.get_frame_size()
        assert size == (640, 480)  # Will have frame after init
    
    @patch('cv2.VideoCapture')
    def test_get_fps(self, mock_videocapture, sample_rtsp_url):
        """Test getting FPS."""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3)))
        mock_cap.get.return_value = 30.0
        mock_videocapture.return_value = mock_cap
        
        reader = CameraReader(sample_rtsp_url, timeout=1)
        fps = reader.get_fps()
        
        assert fps == 30.0
    
    @patch('cv2.VideoCapture')
    def test_is_streaming(self, mock_videocapture, sample_rtsp_url):
        """Test streaming status."""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3)))
        mock_videocapture.return_value = mock_cap
        
        reader = CameraReader(sample_rtsp_url, timeout=1)
        
        assert reader.is_streaming() is True
    
    @patch('cv2.VideoCapture')
    def test_release(self, mock_videocapture, sample_rtsp_url):
        """Test resource release."""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3)))
        mock_videocapture.return_value = mock_cap
        
        reader = CameraReader(sample_rtsp_url, timeout=1)
        reader.release()
        
        mock_cap.release.assert_called_once()
        assert reader.is_connected is False
    
    @patch('cv2.VideoCapture')
    def test_context_manager(self, mock_videocapture, sample_rtsp_url):
        """Test context manager usage."""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3)))
        mock_videocapture.return_value = mock_cap
        
        with CameraReader(sample_rtsp_url, timeout=1) as reader:
            assert reader.is_connected is True
        
        # Should be released after context exit
        mock_cap.release.assert_called()


class TestCameraReaderError:
    """Test cases for CameraReaderError."""
    
    def test_error_message(self):
        """Test error message."""
        error = CameraReaderError("Test error message")
        assert str(error) == "Test error message"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

