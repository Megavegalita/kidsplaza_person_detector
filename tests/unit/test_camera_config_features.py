#!/usr/bin/env python3
"""
Unit tests for camera config feature system.

This module tests feature configuration loading and management.
"""

import pytest
from pathlib import Path
import json
import tempfile

from src.modules.camera.camera_config import CameraConfig, CameraConfigError


class TestCameraConfigFeatures:
    """Test suite for feature configuration."""

    @pytest.fixture
    def sample_config_dict(self):
        """Create sample config dictionary."""
        return {
            "company": "Test Company",
            "address": "Test Address",
            "server": {"host": "test.com", "port": 554},
            "credentials": {"username": "user", "password": "pass"},
            "channels": [
                {
                    "channel_id": 1,
                    "name": "channel_1",
                    "rtsp_url": "rtsp://test.com/1",
                    "features": {
                        "reid": {"enabled": False},
                        "counter": {
                            "enabled": True,
                            "zones": [{"zone_id": "zone_1", "name": "Test"}],
                        },
                    },
                },
                {
                    "channel_id": 2,
                    "name": "channel_2",
                    "rtsp_url": "rtsp://test.com/2",
                },
            ],
            "default_features": {
                "body_detection": {"enabled": True, "always": True},
                "tracking": {"enabled": True, "always": True},
                "reid": {"enabled": True, "always": False},
                "gender_classification": {"enabled": True, "always": False},
                "counter": {"enabled": True, "always": False},
            },
        }

    @pytest.fixture
    def config_file(self, sample_config_dict):
        """Create temporary config file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(sample_config_dict, f)
            temp_path = Path(f.name)

        yield temp_path

        # Cleanup
        temp_path.unlink(missing_ok=True)

    @pytest.fixture
    def config(self, config_file):
        """Create CameraConfig instance."""
        return CameraConfig(config_file)

    def test_get_default_features(self, config):
        """Test getting default features."""
        # Act
        defaults = config.get_default_features()

        # Assert
        assert "body_detection" in defaults
        assert "tracking" in defaults
        assert "reid" in defaults
        assert defaults["body_detection"]["enabled"] is True
        assert defaults["body_detection"]["always"] is True

    def test_get_channel_features_with_override(self, config):
        """Test getting channel features with override."""
        # Act
        features = config.get_channel_features(1)

        # Assert
        assert "reid" in features
        assert features["reid"]["enabled"] is False  # Overridden
        assert "counter" in features
        assert features["counter"]["enabled"] is True
        assert "zones" in features["counter"]

    def test_get_channel_features_defaults(self, config):
        """Test getting channel features using defaults."""
        # Act
        features = config.get_channel_features(2)

        # Assert
        assert "reid" in features
        assert features["reid"]["enabled"] is True  # From defaults
        assert "counter" in features
        assert features["counter"]["enabled"] is True

    def test_is_feature_enabled(self, config):
        """Test checking if feature is enabled."""
        # Act & Assert
        assert config.is_feature_enabled(1, "counter") is True
        assert config.is_feature_enabled(1, "reid") is False
        assert config.is_feature_enabled(2, "reid") is True

    def test_is_feature_always_enabled(self, config):
        """Test checking if feature is always enabled."""
        # Act & Assert
        assert config.is_feature_always_enabled("body_detection") is True
        assert config.is_feature_always_enabled("tracking") is True
        assert config.is_feature_always_enabled("reid") is False

    def test_get_feature_config(self, config):
        """Test getting specific feature config."""
        # Act
        counter_config = config.get_feature_config(1, "counter")

        # Assert
        assert counter_config is not None
        assert counter_config["enabled"] is True
        assert "zones" in counter_config

    def test_get_feature_config_not_found(self, config):
        """Test getting feature config that doesn't exist."""
        # Act
        config_result = config.get_feature_config(1, "nonexistent")

        # Assert
        assert config_result is None

    def test_get_channel_features_nonexistent_channel(self, config):
        """Test getting features for non-existent channel."""
        # Act & Assert
        with pytest.raises(CameraConfigError):
            config.get_channel_features(999)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

