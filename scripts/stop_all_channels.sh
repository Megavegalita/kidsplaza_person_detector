#!/bin/bash
# Script to stop all camera channels

echo "Stopping all camera channels..."

# Kill all processes
pkill -f "process_live_camera.py"

# Wait a bit
sleep 2

# Check if any are still running
REMAINING=$(ps aux | grep -E "process_live_camera" | grep -v grep | wc -l | tr -d ' ')

if [ "$REMAINING" -eq 0 ]; then
    echo "✅ All channels stopped"
else
    echo "⚠️  Some processes may still be running:"
    ps aux | grep -E "process_live_camera" | grep -v grep
    echo ""
    echo "Force kill remaining processes? (y/n)"
    read -r response
    if [ "$response" = "y" ]; then
        pkill -9 -f "process_live_camera.py"
        echo "✅ Force stopped"
    fi
fi

