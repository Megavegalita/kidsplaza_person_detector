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
