#!/bin/bash
# Script to test a single channel with Phase 8 counter and dynamic config

CHANNEL_ID=${1:-1}
CONFIG_FILE="input/cameras_config/kidsplaza_thanhxuan.json"
SCRIPT="src/scripts/process_live_camera.py"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Config file not found: $CONFIG_FILE"
    exit 1
fi

echo "=========================================="
echo "Testing Channel $CHANNEL_ID"
echo "=========================================="
echo ""
echo "Configurations loaded from: $CONFIG_FILE"
echo "Counter zones: Auto-loaded from config"
echo ""
echo "Starting channel $CHANNEL_ID..."
echo "Press Ctrl+C to stop"
echo ""

# Activate venv if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start channel
python "$SCRIPT" \
    --config "$CONFIG_FILE" \
    --channel-id "$CHANNEL_ID" \
    --preset gender_main_v1 \
    --display \
    --display-fps 12 \
    --log-level INFO

