#!/bin/bash
# Monitor Channel 4 test in real-time

LOG_DIR="logs"
LATEST_LOG=$(ls -t "$LOG_DIR"/channel_4_staff_test_*.log 2>/dev/null | head -1)

if [ -z "$LATEST_LOG" ]; then
    echo "❌ No log file found. Start test first with: ./scripts/test_channel4_staff.sh"
    exit 1
fi

echo "📊 Monitoring: $LATEST_LOG"
echo "Press Ctrl+C to stop monitoring"
echo ""

tail -f "$LATEST_LOG" | grep -E "Staff|staff|Voting|voting|Filtering|filtering|Counter|counter|ERROR|Error|Processed|frames"

