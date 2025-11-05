#!/bin/bash
# Script to start all camera channels with Phase 8 dynamic configuration

CONFIG_FILE="input/cameras_config/kidsplaza_thanhxuan.json"
SCRIPT="src/scripts/process_live_camera.py"
LOG_DIR="logs"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Starting All Camera Channels"
echo "=========================================="
echo ""

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Config file not found: $CONFIG_FILE"
    exit 1
fi

# Function to start a channel
start_channel() {
    local channel_id=$1
    local log_file="$LOG_DIR/channel_${channel_id}_$(date +%Y%m%d_%H%M%S).log"
    
    echo -e "${GREEN}Starting Channel ${channel_id}...${NC}"
    
    # Start process in background
    # Note: Counter zones are loaded from config automatically
    nohup python "$SCRIPT" \
        --config "$CONFIG_FILE" \
        --channel-id "$channel_id" \
        --display \
        --display-fps 12 \
        --log-level INFO \
        > "$log_file" 2>&1 &
    
    local pid=$!
    echo "  PID: $pid"
    echo "  Log: $log_file"
    
    # Wait a bit to see if it starts successfully
    sleep 2
    
    if ps -p $pid > /dev/null; then
        echo -e "${GREEN}  ✅ Channel ${channel_id} started successfully${NC}"
    else
        echo -e "${YELLOW}  ⚠️  Channel ${channel_id} may have failed - check log${NC}"
    fi
    
    echo ""
}

# Stop any existing processes first
echo "Stopping existing processes..."
pkill -f "process_live_camera.py" 2>/dev/null
sleep 2

# Start all channels
for channel_id in 1 2 3 4; do
    start_channel $channel_id
    sleep 1  # Small delay between starts
done

echo "=========================================="
echo "All channels started"
echo "=========================================="
echo ""
echo "To check status:"
echo "  ps aux | grep process_live_camera"
echo ""
echo "To stop all channels:"
echo "  pkill -f process_live_camera.py"
echo ""
echo "To view logs:"
echo "  tail -f logs/channel_*_*.log"
echo ""

