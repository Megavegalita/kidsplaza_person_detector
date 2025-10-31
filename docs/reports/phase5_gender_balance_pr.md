# Phase 5: Gender Main V1 (Balance) – PR Summary

## Summary
- Integrate gender_main_v1 preset with balanced asymmetric thresholds (F=0.50, M=0.50)
- Re-ID optimized flow (avg_sim, append mode, max embeddings=3)
- Tracker stability improvements (one-to-one greedy IoU + fallback attach; early EMA)
- Type-safety and lint fixes across modules; configs for flake8 and mypy
- 3-minute smoke video and JSON report produced for verification

## Key Changes
- src/scripts/process_video_file.py: add preset; guards for Optional; video writer handling; face bbox cache typing; Re-ID integration typing
- modules/demographics: classifier typing and logging cleanup; Keras/ResNet classifiers Path handling
- modules/reid: cache URL typing; embedder safety; protocols in tracker for reid types
- modules/tracking/tracker.py: fallback association under low IoU; immediate EMA; link new tracks to detections in-frame
- modules/camera/camera_reader.py: robust None handling for cap
- detection/model_loader.py: Optional model guard
- .config/.flake8, .config/mypy.ini, .config/pytest.ini

## Quality Gates
- black/isort: PASS
- flake8: PASS (max-line-length=100)
- mypy: PASS (0 errors)
- pytest: PASS (templates excluded)  
- bandit: PASS (no high severity)

## Performance (Smoke Test 3m)
- Device: mps (MPS enabled: True)
- Processing time: 106.36s
- Avg/frame: 23.64ms
- Unique tracks: 59
- Gender totals: M=6, F=40, Unknown=0

## Artifacts
- Report JSON: output/videos/gender_main_v1_final_balance/report_..._Binh Xa-Thach That_ch4_20251024102450_20251024112450.json
- Annotated MP4: output/videos/gender_main_v1_final_balance/annotated_Binh Xa-Thach That_ch4_20251024102450_20251024112450.mp4

## Risks/Notes
- Fallback association may attach distant jumps; monitored via EMA and future thresholds
- Redis/Re-ID availability is optional; guarded paths
- Keras TF classifier optional depending on TF presence

## Checklist
- [x] Code formatted and linted
- [x] Types checked (mypy)
- [x] Unit/integration tests green
- [x] Security scan (bandit)
- [x] Docs updated

