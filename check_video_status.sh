#!/bin/bash
while true; do
    if [ -f "output/reid_conf2_med_sim_hi_iou/report_Binh Xa-Thach That_ch4_20251024102450_20251024112450.json" ]; then
        echo "✅ Video processing completed!"
        python3 << 'PYEOF'
import json
from pathlib import Path

report_path = Path("output/reid_conf2_med_sim_hi_iou/report_Binh Xa-Thach That_ch4_20251024102450_20251024112450.json")
with open(report_path) as f:
    data = json.load(f)
summary = data.get('summary', {})
unique = summary.get('unique_tracks_total', 0)
print(f"\nUnique Tracks: {unique}")
print(f"Video: output/reid_conf2_med_sim_hi_iou/annotated_Binh Xa-Thach That_ch4_20251024102450_20251024112450.mp4")
PYEOF
        break
    fi
    progress=$(tail -1 logs/reid_conf2_med_sim_hi_iou.log 2>/dev/null | grep -oP 'Progress: \K[\d.]+' || echo "0")
    if [ ! -z "$progress" ]; then
        echo "Progress: ${progress}%"
    fi
    sleep 30
done
