# Tóm Tắt Session: Tối Ưu Re-ID và Tracking

## Thành Tựu Đạt Được

### 1. Tối Ưu Re-ID và Tracking ✅
- **Config D** được chọn làm phương án tối ưu
- **Tham số**: `iou=0.4`, `ema=0.4`, `reid-k=20`, `ttl=180`
- **Hiệu năng**: 44.8 FPS, 121 unique tracks, 124.8s processing time

### 2. Tính Năng Mới ✅
- **Unique count tracking**: Hiển thị số người duy nhất trên overlay
- **On-demand Re-ID**: Chỉ chạy khi cần thiết
- **Frequency limiting**: Giảm overhead của Re-ID

### 3. Files Đã Tạo
- `docs/debug_plan/REID_OPTIMIZATION_FINAL_REPORT.md` - Báo cáo chi tiết
- `src/modules/demographics/gender_classifier.py` - Gender classifier skeleton
- Video outputs với overlay updated

## Next Steps

### Phase 5: Gender Classification
**Status**: Skeleton created, needs training/integration

**Để hoàn thành**:
1. ❌ Train/load pretrained gender model
2. ❌ Integrate vào pipeline
3. ❌ Add gender labels to overlay
4. ❌ Test và benchmark

**Action items cho lần sau**:
```bash
# 1. Train gender model hoặc load pretrained
# 2. Test standalone
python -m modules.demographics.gender_classifier

# 3. Integrate vào process_video_file.py
# 4. Chạy test với gender enabled
python src/scripts/process_video_file.py \
  "input/video/test.mp4" \
  --gender-enable

# 5. Evaluate accuracy và performance impact
```

## Config Tối Ưu Hiện Tại

```bash
python src/scripts/process_video_file.py \
  "input/video/video.mp4" \
  --model yolov8n.pt \
  --output output/videos \
  --tracker-iou-threshold 0.4 \
  --tracker-ema-alpha 0.4 \
  --tracker-max-age 30 \
  --tracker-min-hits 3 \
  --reid-enable \
  --reid-every-k 20 \
  --reid-ttl-seconds 180
```

## Notes
- Re-ID hoạt động tốt với on-demand logic
- Tracking ổn định với Config D (121 unique tracks)
- FPS cao (~45) phù hợp real-time
- Gender classification cần training/pretrained model

