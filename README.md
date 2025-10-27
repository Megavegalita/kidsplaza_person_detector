# Kidsplaza Person Detector

Person detection system for Kidsplaza Thanh Xuan cameras.

## 📋 Features

- Camera configuration for Kidsplaza Thanh Xuan (4 channels)
- Camera health verification script
- Real-time camera display
- RTSP stream support

## 🎥 Camera Configuration

Location: Kidsplaza (Bích Xá, Thạch Thất, Thanh Xuân, Hà Nội)
Server: 14.177.236.96:554
Channels: 4 channels with full HD streaming

## 🚀 Quick Start

### 1. Setup Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate venv
source venv/bin/activate

# Install dependencies
pip install opencv-python
```

### 2. Verify Camera Health

```bash
python src/scripts/verify_camera_health.py
```

### 3. Display Camera Stream

```bash
# Display channel 1
python src/scripts/display_camera.py 1

# Display other channels (2, 3, 4)
python src/scripts/display_camera.py 2
```

## 📁 Project Structure

```
person_detector/
├── input/
│   └── cameras_config/      # Camera configurations
│       └── kidsplaza_thanhxuan.json
├── src/
│   └── scripts/
│       ├── verify_camera_health.py    # Health check script
│       └── display_camera.py           # Display camera stream
└── venv/                     # Virtual environment (not in git)
```

## 🔧 Camera RTSP Format

Standard RTSP URL format:
```
rtsp://username:password@ip:port/cam/realmonitor?channel=N&subtype=0
```

## 📊 Health Check Results

All 4 camera channels tested and verified:
- Channel 1: ✅ 1920x1080
- Channel 2: ✅ 1920x1080  
- Channel 3: ✅ 1920x1080
- Channel 4: ✅ 2304x1296

## 📝 Requirements

- Python 3.11+
- opencv-python
- Virtual environment (recommended)

## 🔒 Security

Credentials are stored in configuration files for local development only.
