#!/bin/bash
# Script to check status of all camera channels

echo "=========================================="
echo "Camera Channels Status"
echo "=========================================="
echo ""

# Check running processes
PROCESSES=$(ps aux | grep -E "process_live_camera.py.*--channel-id" | grep -v grep)

if [ -z "$PROCESSES" ]; then
    echo "❌ No channels are running"
else
    echo "Running Channels:"
    echo "$PROCESSES" | while read -r line; do
        # Extract channel ID from command line
        CHANNEL=$(echo "$line" | grep -oP '--channel-id \K\d+')
        PID=$(echo "$line" | awk '{print $2}')
        CPU=$(echo "$line" | awk '{print $3}')
        MEM=$(echo "$line" | awk '{print $4}')
        
        echo "  Channel $CHANNEL: PID=$PID, CPU=$CPU%, MEM=$MEM%"
    done
fi

echo ""
echo "Lock Files:"
for lock in /tmp/kidsplaza_live_camera_ch*.lock; do
    if [ -f "$lock" ]; then
        CHANNEL=$(basename "$lock" | sed 's/kidsplaza_live_camera_ch\([0-9]\)\.lock/\1/')
        echo "  Channel $CHANNEL: Lock file exists"
    fi
done

echo ""
echo "Recent Log Files:"
ls -t logs/channel_*.log 2>/dev/null | head -4 | while read -r log; do
    echo "  $(basename $log)"
done

echo ""

