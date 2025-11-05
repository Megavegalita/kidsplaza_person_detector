#!/usr/bin/env python3
"""
Camera configuration management module.

This module handles loading and management of camera configurations from JSON files.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class CameraConfigError(Exception):
    """Raised when camera configuration errors occur."""

    pass


class CameraConfig:
    """Manages camera configuration data."""

    def __init__(self, config_path: Path) -> None:
        """
        Initialize camera configuration.

        Args:
            config_path: Path to camera configuration JSON file

        Raises:
            CameraConfigError: If config file not found or invalid
        """
        self.config_path = config_path
        self.config_data: Dict = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from JSON file."""
        try:
            if not self.config_path.exists():
                raise CameraConfigError(f"Config file not found: {self.config_path}")

            with open(self.config_path, "r", encoding="utf-8") as file:
                self.config_data = json.load(file)

            logger.info(f"Loaded camera config from {self.config_path}")

        except json.JSONDecodeError as e:
            raise CameraConfigError(f"Invalid JSON in config: {e}") from e
        except Exception as e:
            raise CameraConfigError(f"Failed to load config: {e}") from e

    def get_channels(self) -> List[Dict]:
        """
        Get list of camera channels.

        Returns:
            List of channel configurations

        Raises:
            CameraConfigError: If 'channels' key not found
        """
        if "channels" not in self.config_data:
            raise CameraConfigError("'channels' key not found in config")

        return self.config_data["channels"]

    def get_channel(self, channel_id: int) -> Optional[Dict]:
        """
        Get configuration for specific channel.

        Args:
            channel_id: Channel ID to retrieve

        Returns:
            Channel configuration or None if not found
        """
        channels = self.get_channels()
        for channel in channels:
            if channel.get("channel_id") == channel_id:
                return channel
        return None

    def get_server_info(self) -> Dict:
        """Get server information."""
        return self.config_data.get("server", {})

    def get_credentials(self) -> Dict:
        """Get credentials information."""
        return self.config_data.get("credentials", {})

    def get_company_info(self) -> Dict:
        """Get company information."""
        return {
            "company": self.config_data.get("company", ""),
            "address": self.config_data.get("address", ""),
        }

    def get_total_channels(self) -> int:
        """Get total number of channels."""
        return len(self.get_channels())

    def get_default_features(self) -> Dict:
        """
        Get default feature configuration.

        Returns:
            Dictionary with default feature settings
        """
        default_features = self.config_data.get("default_features", {})
        
        # System defaults if not in config
        system_defaults = {
            "body_detection": {"enabled": True, "always": True},
            "tracking": {"enabled": True, "always": True},
            "reid": {"enabled": True, "always": False},
            "gender_classification": {"enabled": True, "always": False},
            "counter": {"enabled": True, "always": False},
        }
        
        # Merge config defaults with system defaults
        merged = system_defaults.copy()
        for feature_name, feature_config in default_features.items():
            merged[feature_name] = {**system_defaults.get(feature_name, {}), **feature_config}
        
        return merged

    def get_channel_features(self, channel_id: int) -> Dict:
        """
        Get feature configuration for specific channel.

        Args:
            channel_id: Channel ID to retrieve features for

        Returns:
            Dictionary with feature configurations, merged from channel-specific
            and default features

        Raises:
            CameraConfigError: If channel not found
        """
        channel = self.get_channel(channel_id)
        if channel is None:
            raise CameraConfigError(f"Channel {channel_id} not found")

        # Get default features
        default_features = self.get_default_features()
        
        # Get channel-specific features (if any)
        channel_features = channel.get("features", {})
        
        # Merge: channel-specific overrides defaults
        merged_features = default_features.copy()
        for feature_name, feature_config in channel_features.items():
            if feature_name in merged_features:
                # Merge nested dicts
                merged_features[feature_name] = {
                    **merged_features[feature_name],
                    **feature_config
                }
            else:
                merged_features[feature_name] = feature_config
        
        return merged_features

    def get_feature_config(
        self, channel_id: int, feature_name: str
    ) -> Optional[Dict]:
        """
        Get configuration for specific feature on specific channel.

        Args:
            channel_id: Channel ID
            feature_name: Name of feature (e.g., 'reid', 'gender_classification', 'counter')

        Returns:
            Feature configuration dictionary or None if not found
        """
        features = self.get_channel_features(channel_id)
        return features.get(feature_name)

    def is_feature_enabled(
        self, channel_id: int, feature_name: str
    ) -> bool:
        """
        Check if a feature is enabled for a specific channel.

        Args:
            channel_id: Channel ID
            feature_name: Name of feature to check

        Returns:
            True if feature is enabled, False otherwise
        """
        feature_config = self.get_feature_config(channel_id, feature_name)
        if feature_config is None:
            return False
        
        return feature_config.get("enabled", False)

    def is_feature_always_enabled(self, feature_name: str) -> bool:
        """
        Check if a feature is always enabled (cannot be disabled).

        Args:
            feature_name: Name of feature to check

        Returns:
            True if feature is always enabled, False otherwise
        """
        default_features = self.get_default_features()
        feature_config = default_features.get(feature_name, {})
        return feature_config.get("always", False)


def load_camera_config(config_path: Path) -> CameraConfig:
    """
    Load camera configuration from file.

    Args:
        config_path: Path to camera configuration file

    Returns:
        CameraConfig instance

    Raises:
        CameraConfigError: If config cannot be loaded
    """
    return CameraConfig(config_path)


def validate_config(config_data: Dict) -> bool:
    """
    Validate camera configuration data.

    Args:
        config_data: Configuration dictionary to validate

    Returns:
        True if valid, raises exception if invalid

    Raises:
        CameraConfigError: If validation fails
    """
    required_keys = ["server", "credentials", "channels"]

    for key in required_keys:
        if key not in config_data:
            raise CameraConfigError(f"Missing required key: {key}")

    # Validate server info
    server = config_data["server"]
    required_server_keys = ["host", "port"]
    for key in required_server_keys:
        if key not in server:
            raise CameraConfigError(f"Missing server key: {key}")

    # Validate credentials
    creds = config_data["credentials"]
    required_creds_keys = ["username", "password"]
    for key in required_creds_keys:
        if key not in creds:
            raise CameraConfigError(f"Missing credentials key: {key}")

    # Validate channels
    channels = config_data["channels"]
    if not isinstance(channels, list) or len(channels) == 0:
        raise CameraConfigError("Channels must be a non-empty list")

    for i, channel in enumerate(channels):
        required_channel_keys = ["channel_id", "rtsp_url"]
        for key in required_channel_keys:
            if key not in channel:
                raise CameraConfigError(f"Channel {i}: Missing required key: {key}")

    return True


if __name__ == "__main__":
    # Test the module
    import sys

    logging.basicConfig(level=logging.INFO)

    try:
        config_path = Path("input/cameras_config/kidsplaza_thanhxuan.json")
        config = load_camera_config(config_path)

        print(f"Company: {config.get_company_info()['company']}")
        print(f"Total Channels: {config.get_total_channels()}")

        for channel in config.get_channels():
            print(
                f"Channel {channel['channel_id']}: {channel.get('description', 'N/A')}"
            )

        # Validate
        validate_config(config.config_data)
        print("\n✅ Config validation passed")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
