#!/usr/bin/env python3
"""
Camera Health Verification Script
Verifies RTSP connectivity and health status for Kidsplaza Thanh Xuan cameras.
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

try:
    import cv2
except ImportError:
    print("Error: OpenCV (cv2) is not installed.")
    print("Please install it using: pip install opencv-python")
    sys.exit(1)


def generate_alternative_urls(server: Dict, credentials: Dict, channel_id: int) -> List[str]:
    """
    Generate alternative RTSP URL patterns for testing.
    
    Args:
        server: Server configuration with host and port
        credentials: Credentials with username and password
        channel_id: Camera channel number
        
    Returns:
        List of alternative RTSP URL patterns
    """
    host = server['host']
    port = server['port']
    username = credentials['username']
    password = credentials['password']
    
    urls = [
        f"rtsp://{username}:{password}@{host}:{port}/Streaming/Channels/{channel_id}01",  # Hikvision main
        f"rtsp://{username}:{password}@{host}:{port}/Streaming/Channels/{channel_id}02",  # Hikvision sub
        f"rtsp://{username}:{password}@{host}:{port}/cam/realmonitor?channel={channel_id}&subtype=0",
        f"rtsp://{username}:{password}@{host}:{port}/h264/ch{channel_id}/main/av_stream",
        f"rtsp://{username}:{password}@{host}:{port}/h264/ch{channel_id}/sub/av_stream",
        f"rtsp://{username}:{password}@{host}:{port}/channel{channel_id}",
        f"rtsp://{username}:{password}@{host}:{port}/live?channel={channel_id}&stream=0",
        f"rtsp://{username}:{password}@{host}:{port}/streaming/channels/{channel_id}",
        f"rtsp://{username}:{password}@{host}:{port}/cam{channel_id}/",
    ]
    
    return urls


def load_camera_config(config_path: Path) -> Dict:
    """
    Load camera configuration from JSON file.
    
    Args:
        config_path: Path to the configuration JSON file
        
    Returns:
        Dictionary containing camera configuration
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as file:
        config = json.load(file)
    
    return config


def verify_rtsp_connection(rtsp_url: str, timeout: int = 10) -> Tuple[bool, str]:
    """
    Verify RTSP camera connection and health.
    
    Args:
        rtsp_url: Complete RTSP URL with credentials
        timeout: Connection timeout in seconds
        
    Returns:
        Tuple of (is_healthy, status_message)
    """
    cap = None
    
    try:
        # Attempt to open RTSP stream
        cap = cv2.VideoCapture(rtsp_url)
        
        # Try to read a frame to verify stream is active
        start_time = time.time()
        ret, frame = cap.read()
        elapsed_time = time.time() - start_time
        
        if not ret:
            return False, "Failed to read frame from stream"
        
        if frame is None or frame.size == 0:
            return False, "Received empty frame"
        
        # Check if frame has valid dimensions
        height, width = frame.shape[:2]
        if width == 0 or height == 0:
            return False, "Invalid frame dimensions"
        
        return True, f"Stream active - Frame: {width}x{height}, Latency: {elapsed_time:.2f}s"
        
    except cv2.error as e:
        return False, f"OpenCV error: {str(e)}"
    except AttributeError as e:
        return False, f"OpenCV version compatibility issue: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"
    finally:
        if cap is not None:
            cap.release()


def verify_camera_channel(
    channel: Dict,
    timeout: int = 10
) -> Dict:
    """
    Verify a single camera channel.
    
    Args:
        channel: Channel configuration dictionary
        timeout: Connection timeout in seconds
        
    Returns:
        Dictionary with verification results
    """
    channel_id = channel.get('channel_id', 'unknown')
    name = channel.get('name', 'Unknown')
    rtsp_url = channel.get('rtsp_url', '')
    
    print(f"\n{'='*60}")
    print(f"Verifying Channel {channel_id}: {name}")
    print(f"URL: {rtsp_url}")
    print(f"{'='*60}")
    
    start_time = time.time()
    is_healthy, status_message = verify_rtsp_connection(rtsp_url, timeout)
    elapsed_time = time.time() - start_time
    
    result = {
        'channel_id': channel_id,
        'name': name,
        'rtsp_url': rtsp_url,
        'is_healthy': is_healthy,
        'status': 'HEALTHY' if is_healthy else 'UNHEALTHY',
        'message': status_message,
        'response_time': f"{elapsed_time:.2f}s",
        'timestamp': datetime.now().isoformat()
    }
    
    # Print results
    status_symbol = "✓" if is_healthy else "✗"
    print(f"Status: {status_symbol} {result['status']}")
    print(f"Message: {status_message}")
    print(f"Response Time: {elapsed_time:.2f}s")
    
    return result


def verify_all_cameras(config_path: str, timeout: int = 10) -> Dict:
    """
    Verify all camera channels in the configuration.
    
    Args:
        config_path: Path to camera configuration JSON file
        timeout: Connection timeout per channel in seconds
        
    Returns:
        Dictionary with overall results and per-channel details
    """
    config_path_obj = Path(config_path)
    config = load_camera_config(config_path_obj)
    
    print("\n" + "="*60)
    print(f"Camera Health Verification - {config['location']}")
    print(f"Server: {config['server']['host']}:{config['server']['port']}")
    print(f"Total Channels: {config['metadata']['total_channels']}")
    print("="*60)
    
    results = []
    healthy_count = 0
    unhealthy_count = 0
    
    for channel in config['channels']:
        result = verify_camera_channel(channel, timeout)
        results.append(result)
        
        if result['is_healthy']:
            healthy_count += 1
        else:
            unhealthy_count += 1
    
    # Print summary
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    print(f"Total Channels: {len(results)}")
    print(f"Healthy: {healthy_count} ✓")
    print(f"Unhealthy: {unhealthy_count} ✗")
    print(f"Health Rate: {(healthy_count / len(results) * 100):.1f}%")
    print("="*60)
    
    return {
        'location': config['location'],
        'server': config['server'],
        'total_channels': len(results),
        'healthy_count': healthy_count,
        'unhealthy_count': unhealthy_count,
        'health_rate': f"{(healthy_count / len(results) * 100):.1f}%",
        'timestamp': datetime.now().isoformat(),
        'channels': results
    }


def main():
    """Main entry point for the camera verification script."""
    # Default configuration path
    default_config_path = Path(__file__).parent.parent.parent / "input" / "cameras_config" / "kidsplaza_thanhxuan.json"
    
    # Allow command-line override
    config_path = sys.argv[1] if len(sys.argv) > 1 else str(default_config_path)
    
    try:
        results = verify_all_cameras(config_path, timeout=10)
        
        # Exit with appropriate code
        if results['unhealthy_count'] > 0:
            sys.exit(1)  # Exit with error if any cameras are unhealthy
        else:
            sys.exit(0)  # Exit successfully if all cameras are healthy
            
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"\nError: Invalid JSON in configuration file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: Unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
