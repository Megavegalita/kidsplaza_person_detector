#!/usr/bin/env python3
"""
Unit tests for camera configuration module.
"""

import pytest
from pathlib import Path
import tempfile
import json

from src.modules.camera.camera_config import (
    CameraConfig,
    CameraConfigError,
    load_camera_config,
    validate_config
)


class TestCameraConfig:
    """Test cases for CameraConfig class."""
    
    @pytest.fixture
    def valid_config_data(self):
        """Create valid configuration data."""
        return {
            "company": "Test Company",
            "address": "Test Address",
            "server": {
                "host": "192.168.1.100",
                "port": 554
            },
            "credentials": {
                "username": "test_user",
                "password": "test_pass"
            },
            "channels": [
                {
                    "channel_id": 1,
                    "name": "channel_1",
                    "rtsp_url": "rtsp://test@192.168.1.100:554/stream1",
                    "description": "Test Channel 1"
                }
            ],
            "metadata": {
                "total_channels": 1
            }
        }
    
    @pytest.fixture
    def temp_config_file(self, valid_config_data):
        """Create temporary config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(valid_config_data, f)
            f.flush()
            temp_path = Path(f.name)
        
        yield temp_path
        
        # Cleanup after test
        if temp_path.exists():
            temp_path.unlink()
    
    def test_load_valid_config(self, temp_config_file):
        """Test loading valid configuration."""
        config = CameraConfig(temp_config_file)
        
        assert config.config_data is not None
        assert config.get_total_channels() == 1
        assert config.get_company_info()['company'] == "Test Company"
    
    def test_get_channels(self, temp_config_file):
        """Test getting channels."""
        config = CameraConfig(temp_config_file)
        channels = config.get_channels()
        
        assert len(channels) == 1
        assert channels[0]['channel_id'] == 1
    
    def test_get_channel(self, temp_config_file):
        """Test getting specific channel."""
        config = CameraConfig(temp_config_file)
        channel = config.get_channel(1)
        
        assert channel is not None
        assert channel['channel_id'] == 1
        assert 'rtsp_url' in channel
    
    def test_get_nonexistent_channel(self, temp_config_file):
        """Test getting non-existent channel."""
        config = CameraConfig(temp_config_file)
        channel = config.get_channel(999)
        
        assert channel is None
    
    def test_get_server_info(self, temp_config_file):
        """Test getting server info."""
        config = CameraConfig(temp_config_file)
        server = config.get_server_info()
        
        assert server['host'] == "192.168.1.100"
        assert server['port'] == 554
    
    def test_get_credentials(self, temp_config_file):
        """Test getting credentials."""
        config = CameraConfig(temp_config_file)
        creds = config.get_credentials()
        
        assert creds['username'] == "test_user"
        assert creds['password'] == "test_pass"
    
    def test_config_file_not_found(self):
        """Test with non-existent config file."""
        with pytest.raises(CameraConfigError):
            CameraConfig(Path("nonexistent.json"))
    
    def test_invalid_json(self):
        """Test with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("Invalid JSON content {")
            f.flush()
            temp_path = Path(f.name)
        
        with pytest.raises(CameraConfigError):
            CameraConfig(temp_path)
        
        temp_path.unlink()
    
    def test_missing_required_keys(self, valid_config_data):
        """Test with missing required keys."""
        # Remove 'channels' key
        del valid_config_data['channels']
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(valid_config_data, f)
            f.flush()
            temp_path = Path(f.name)
        
        config = CameraConfig(temp_path)
        
        with pytest.raises(CameraConfigError):
            config.get_channels()
        
        temp_path.unlink()


class TestValidateConfig:
    """Test cases for validate_config function."""
    
    def test_valid_config(self):
        """Test validating valid configuration."""
        config_data = {
            "server": {"host": "192.168.1.1", "port": 554},
            "credentials": {"username": "user", "password": "pass"},
            "channels": [
                {"channel_id": 1, "rtsp_url": "rtsp://test"}
            ]
        }
        
        result = validate_config(config_data)
        assert result is True
    
    def test_missing_server(self):
        """Test with missing server key."""
        config_data = {
            "credentials": {"username": "user", "password": "pass"},
            "channels": [{"channel_id": 1, "rtsp_url": "rtsp://test"}]
        }
        
        with pytest.raises(CameraConfigError):
            validate_config(config_data)
    
    def test_missing_channels(self):
        """Test with missing channels key."""
        config_data = {
            "server": {"host": "192.168.1.1", "port": 554},
            "credentials": {"username": "user", "password": "pass"}
        }
        
        with pytest.raises(CameraConfigError):
            validate_config(config_data)
    
    def test_empty_channels(self):
        """Test with empty channels list."""
        config_data = {
            "server": {"host": "192.168.1.1", "port": 554},
            "credentials": {"username": "user", "password": "pass"},
            "channels": []
        }
        
        with pytest.raises(CameraConfigError):
            validate_config(config_data)


class TestLoadCameraConfig:
    """Test cases for load_camera_config function."""
    
    @pytest.fixture
    def temp_config_file(self):
        """Create temporary config file."""
        config_data = {
            "server": {"host": "192.168.1.1", "port": 554},
            "credentials": {"username": "user", "password": "pass"},
            "channels": [
                {"channel_id": 1, "rtsp_url": "rtsp://test"}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            f.flush()
            temp_path = Path(f.name)
        
        yield temp_path
        
        # Cleanup after test
        if temp_path.exists():
            temp_path.unlink()
    
    def test_load_config_function(self, temp_config_file):
        """Test load_camera_config function."""
        config = load_camera_config(temp_config_file)
        
        assert isinstance(config, CameraConfig)
        assert config.get_total_channels() == 1
    
    def test_load_nonexistent(self):
        """Test loading non-existent config."""
        with pytest.raises(CameraConfigError):
            load_camera_config(Path("nonexistent.json"))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

