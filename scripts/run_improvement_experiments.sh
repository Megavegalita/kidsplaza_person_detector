#!/bin/bash
# Run improvement experiments based on adapt_e20_c04_reid_opt_v2 baseline

set -e

PY="/Users/autoeyes/Project/kidsplaza/person_detector/venv/bin/python"
VID="/Users/autoeyes/Project/kidsplaza/person_detector/input/video/Binh Xa-Thach That_ch4_20251024102450_20251024112450.mp4"
MODEL="/Users/autoeyes/Project/kidsplaza/person_detector/yolov8n.pt"
OUT="/Users/autoeyes/Project/kidsplaza/person_detector/output/videos"

# Baseline Re-ID config
BASE_REID="--reid-enable --reid-every-k 20 --reid-ttl-seconds 60 --reid-similarity-threshold 0.65 --reid-aggregation-method avg_sim --reid-append-mode --reid-max-embeddings 3"

# Baseline gender config  
BASE_GENDER="--gender-enable --gender-every-k 20 --gender-max-per-frame 4 --gender-model-type timm_mobile --gender-min-confidence 0.4 --gender-adaptive-enabled --gender-queue-high-watermark 200 --gender-queue-low-watermark 100"

echo "============================================================"
echo "Running Improvement Experiments"
echo "Baseline: adapt_e20_c04_reid_opt_v2"
echo "============================================================"

# Experiment 1: More frequent gender classification (every-k=15)
echo ""
echo "[1/8] Testing more frequent gender (every-k=15)..."
$PY /Users/autoeyes/Project/kidsplaza/person_detector/src/scripts/process_video_file.py "$VID" \
    --model $MODEL --output $OUT \
    $BASE_REID \
    --run-id improv1_gender_e15 \
    $BASE_GENDER --gender-every-k 15

# Experiment 2: More frequent Re-ID (every-k=15)
echo ""
echo "[2/8] Testing more frequent Re-ID (every-k=15)..."
$PY /Users/autoeyes/Project/kidsplaza/person_detector/src/scripts/process_video_file.py "$VID" \
    --model $MODEL --output $OUT \
    --reid-enable --reid-every-k 15 --reid-ttl-seconds 60 --reid-similarity-threshold 0.65 --reid-aggregation-method avg_sim --reid-append-mode --reid-max-embeddings 3 \
    --run-id improv2_reid_e15 \
    $BASE_GENDER

# Experiment 3: Stricter gender confidence (0.45)
echo ""
echo "[3/8] Testing stricter gender confidence (0.45)..."
$PY /Users/autoeyes/Project/kidsplaza/person_detector/src/scripts/process_video_file.py "$VID" \
    --model $MODEL --output $OUT \
    $BASE_REID \
    --run-id improv3_gender_c045 \
    $BASE_GENDER --gender-min-confidence 0.45

# Experiment 4: Stricter gender confidence (0.50)
echo ""
echo "[4/8] Testing stricter gender confidence (0.50)..."
$PY /Users/autoeyes/Project/kidsplaza/person_detector/src/scripts/process_video_file.py "$VID" \
    --model $MODEL --output $OUT \
    $BASE_REID \
    --run-id improv4_gender_c050 \
    $BASE_GENDER --gender-min-confidence 0.50

# Experiment 5: More relaxed Re-ID threshold (0.60)
echo ""
echo "[5/8] Testing relaxed Re-ID threshold (0.60)..."
$PY /Users/autoeyes/Project/kidsplaza/person_detector/src/scripts/process_video_file.py "$VID" \
    --model $MODEL --output $OUT \
    --reid-enable --reid-every-k 20 --reid-ttl-seconds 60 --reid-similarity-threshold 0.60 --reid-aggregation-method avg_sim --reid-append-mode --reid-max-embeddings 3 \
    --run-id improv5_reid_t060 \
    $BASE_GENDER

# Experiment 6: Stricter Re-ID threshold (0.70)
echo ""
echo "[6/8] Testing stricter Re-ID threshold (0.70)..."
$PY /Users/autoeyes/Project/kidsplaza/person_detector/src/scripts/process_video_file.py "$VID" \
    --model $MODEL --output $OUT \
    --reid-enable --reid-every-k 20 --reid-ttl-seconds 60 --reid-similarity-threshold 0.70 --reid-aggregation-method avg_sim --reid-append-mode --reid-max-embeddings 3 \
    --run-id improv6_reid_t070 \
    $BASE_GENDER

# Experiment 7: More Re-ID embeddings (max=4)
echo ""
echo "[7/8] Testing more Re-ID embeddings (max=4)..."
$PY /Users/autoeyes/Project/kidsplaza/person_detector/src/scripts/process_video_file.py "$VID" \
    --model $MODEL --output $OUT \
    --reid-enable --reid-every-k 20 --reid-ttl-seconds 60 --reid-similarity-threshold 0.65 --reid-aggregation-method avg_sim --reid-append-mode --reid-max-embeddings 4 \
    --run-id improv7_reid_emb4 \
    $BASE_GENDER

# Experiment 8: Combined improvements (gender_e15 + reid_e15 + c045)
echo ""
echo "[8/8] Testing combined improvements (gender_e15 + reid_e15 + c045)..."
$PY /Users/autoeyes/Project/kidsplaza/person_detector/src/scripts/process_video_file.py "$VID" \
    --model $MODEL --output $OUT \
    --reid-enable --reid-every-k 15 --reid-ttl-seconds 60 --reid-similarity-threshold 0.65 --reid-aggregation-method avg_sim --reid-append-mode --reid-max-embeddings 3 \
    --run-id improv8_combined \
    $BASE_GENDER --gender-every-k 15 --gender-min-confidence 0.45

echo ""
echo "============================================================"
echo "All experiments completed!"
echo "Results saved in: $OUT"
echo "============================================================"


