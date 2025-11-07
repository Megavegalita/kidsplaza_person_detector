#!/usr/bin/env bash
# Start Counter Events Web Dashboard

cd "$(dirname "$0")/.."
source venv/bin/activate

echo "Starting Counter Events Dashboard..."
echo "Dashboard will be available at: http://localhost:5000"
echo "Press Ctrl+C to stop"
echo ""

cd web_dashboard
python app.py

