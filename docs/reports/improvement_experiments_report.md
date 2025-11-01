# Improvement Experiments Comparison Report

**Baseline:** Baseline (Adaptive + Re-ID optimized)

| Scenario | Time(s) | Avg(ms) | FPS | Tracks | M | F | U | M% | F% | U% | P50(ms) | P95(ms) |
|----------|---------|---------|-----|--------|---|---|---|----|----|----|---------|---------|
| Baseline (Adaptive + Re-ID optimized) | 105.33 | 23.4 | 0.0 | 24 | 6 | 17 | 0 | 26.1 | 73.9 | 0.0 | 0.0 | 0.0 |
| More frequent gender (every-k=15) | 106.26 | 23.6 | 0.0 | 28 | 4 | 20 | 0 | 16.7 | 83.3 | 0.0 | 0.0 | 0.0 |
| More frequent Re-ID (every-k=15) | 105.94 | 23.5 | 0.0 | 27 | 15 | 10 | 0 | 60.0 | 40.0 | 0.0 | 0.0 | 0.0 |
| Stricter gender conf (0.45) | 106.08 | 23.6 | 0.0 | 28 | 17 | 8 | 0 | 68.0 | 32.0 | 0.0 | 0.0 | 0.0 |
| Stricter gender conf (0.50) | 105.82 | 23.5 | 0.0 | 23 | 2 | 20 | 0 | 9.1 | 90.9 | 0.0 | 0.0 | 0.0 |
| Relaxed Re-ID threshold (0.60) | 106.13 | 23.6 | 0.0 | 14 | 0 | 14 | 0 | 0.0 | 100.0 | 0.0 | 0.0 | 0.0 |
| Stricter Re-ID threshold (0.70) | 106.08 | 23.6 | 0.0 | 39 | 26 | 10 | 0 | 72.2 | 27.8 | 0.0 | 0.0 | 0.0 |
| More Re-ID embeddings (max=4) | 103.63 | 23.0 | 0.0 | 27 | 16 | 8 | 0 | 66.7 | 33.3 | 0.0 | 0.0 | 0.0 |
| Combined (gender_e15 + reid_e15 + c045) | 103.98 | 23.1 | 0.0 | 21 | 7 | 13 | 0 | 35.0 | 65.0 | 0.0 | 0.0 | 0.0 |
