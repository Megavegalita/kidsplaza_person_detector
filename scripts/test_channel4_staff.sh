#!/bin/bash
# Test script for Channel 4 with staff detection and display enabled

CONFIG_FILE="input/cameras_config/kidsplaza_thanhxuan.json"
SCRIPT="src/scripts/process_live_camera.py"
LOG_DIR="logs"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Create log file with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/channel_4_staff_test_${TIMESTAMP}.log"

echo "============================================================"
echo "Channel 4 Staff Detection Test"
echo "============================================================"
echo "Config: $CONFIG_FILE"
echo "Log file: $LOG_FILE"
echo "Display: ENABLED (press 'q' to quit)"
echo "============================================================"
echo ""

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Config file not found: $CONFIG_FILE"
    exit 1
fi

# Check if script exists
if [ ! -f "$SCRIPT" ]; then
    echo "❌ Script not found: $SCRIPT"
    exit 1
fi

# Stop any existing channel 4 process
echo "Stopping any existing channel 4 processes..."
pkill -f "process_live_camera.py.*channel-id.*4" 2>/dev/null
sleep 2

echo "Starting test..."
echo "Press 'q' in the display window to stop."
echo ""

# Run the script with display enabled
python3 "$SCRIPT" \
    --config "$CONFIG_FILE" \
    --channel-id 4 \
    --display \
    --display-fps 15.0 \
    --log-level INFO \
    2>&1 | tee "$LOG_FILE"

EXIT_CODE=${PIPESTATUS[0]}

echo ""
echo "============================================================"
echo "Test completed"
echo "Log file: $LOG_FILE"
echo "Exit code: $EXIT_CODE"
echo "============================================================"
echo ""
echo "To analyze the log, run:"
echo "  python3 scripts/analyze_staff_log.py $LOG_FILE"
echo ""
