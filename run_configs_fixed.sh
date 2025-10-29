#!/bin/bash

cd /Users/autoeyes/Project/kidsplaza/person_detector
source venv/bin/activate

VIDEO="input/video/Binh Xa-Thach That_ch4_20251024102450_20251024112450.mp4"
MODEL="yolov8n.pt"

# Common parameters
COMMON="--tracker-iou-threshold 0.35 --tracker-ema-alpha 0.4 --tracker-max-age 30 --tracker-min-hits 3 --reid-enable --reid-every-k 20 --gender-enable --gender-enable-face-detection --gender-every-k 30 --gender-model-type timm_mobile --gender-max-per-frame 4 --gender-timeout-ms 50 --gender-queue-size 256 --gender-workers 2"

echo "Running 5 configurations sequentially..."

# Config A: Strict
python src/scripts/process_video_file.py "$VIDEO" --model $MODEL $COMMON --output output/gender_face_configs/Config_A --gender-min-confidence 0.6 --gender-voting-window 15 > logs/gender_face_configs/Config_A.log 2>&1 &

# Config B: Balanced
python src/scripts/process_video_file.py "$VIDEO" --model $MODEL $COMMON --output output/gender_face_configs/Config_B --gender-min-confidence 0.4 --gender-voting-window 10 > logs/gender_face_configs/Config_B.log 2>&1 &

# Config C: Permissive  
python src/scripts/process_video_file.py "$VIDEO" --model $MODEL $COMMON --output output/gender_face_configs/Config_C --gender-min-confidence 0.3 --gender-voting-window 7 > logs/gender_face_configs/Config_C.log 2>&1 &

# Config D: Aggressive
python src/scripts/process_video_file.py "$VIDEO" --model $MODEL $COMMON --output output/gender_face_configs/Config_D --gender-min-confidence 0.25 --gender-voting-window 5 > logs/gender_face_configs/Config_D.log 2>&1 &

# Config E: Conservative
python src/scripts/process_video_file.py "$VIDEO" --model $MODEL $COMMON --output output/gender_face_configs/Config_E --gender-min-confidence 0.5 --gender-voting-window 12 > logs/gender_face_configs/Config_E.log 2>&1 &

echo "All jobs started. Waiting for completion..."
wait

echo ""
echo "Completed! Checking output videos..."
ls -lh output/gender_face_configs/*/annotated*.mp4 2>/dev/null

