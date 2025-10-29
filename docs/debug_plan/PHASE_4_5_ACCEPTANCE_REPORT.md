# Báo Cáo Nghiệm Thu: Phase 4-5 - Tracking + Re-ID + Gender Module

## Tóm Tắt

Hệ thống đã hoàn thành Phase 4 (Tracking + Re-ID optimization) và Phase 5 (Gender Classification module), sẵn sàng tích hợp pretrained gender model.

## Kết Quả Nghiệm Thu

### Phase 4: Tracking & Re-ID Optimization ✅

#### Config Tối Ưu (Config D)
- **Tham số**:
  - `tracker-iou-threshold`: 0.4
  - `tracker-ema-alpha`: 0.4
  - `tracker-max-age`: 30
  - `tracker-min-hits`: 3
  - `reid-every-k`: 20
  - `reid-ttl-seconds`: 180

#### Performance Metrics
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| FPS | 44-59 | >40 | ✅ |
| Processing time (3 min) | ~101s | <120s | ✅ |
| Unique tracks | 121 | >100 | ✅ |
| Time per frame | 16-17ms | <25ms | ✅ |
| Device | MPS (GPU) | GPU | ✅ |

#### Features Implemented
- ✅ On-demand Re-ID activation
- ✅ Frequency limiting (`every_k` frames)
- ✅ Hysteresis thresholds for ID stability
- ✅ EMA smoothing for bounding boxes
- ✅ Unique count tracking và overlay
- ✅ JSON report với tracking stats

### Phase 5: Gender Classification Module ✅

#### Module Structure
- ✅ **File**: `src/modules/demographics/gender_classifier.py`
- ✅ **Timm integration**: MobileNetV3-Small support
- ✅ **Majority voting**: Stability logic
- ✅ **Pipeline integration**: CLI flags, overlay, JSON

#### Status
- **Module**: Hoàn thành và sẵn sàng
- **Pretrained model**: Cần fine-tune hoặc download gender-specific model
- **Current**: Using ImageNet-pretrained (not gender-trained)

## Cấu Trúc Code

### Tracking & Re-ID
```
src/modules/
├── tracking/
│   └── tracker.py          # IoU-based tracker với EMA
├── reid/
│   ├── embedder.py         # Re-ID embedding
│   ├── cache.py            # Redis caching
│   └── integrator.py       # On-demand logic
```

### Gender Classification
```
src/modules/demographics/
└── gender_classifier.py    # Timm integration ready
```

## Command Line Usage

### Config D (Recommended)
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
  --reid-ttl-seconds 180 \
  --gender-enable \
  --gender-every-k 30
```

### Performance
- **FPS**: 58-59 FPS (detector stats)
- **Processing**: 100-125s cho 3 phút video
- **Memory**: Efficient với timm pretrained models

## Testing Results

### Test Video: "Binh Xa-Thach That" (4500 frames / 3 minutes)

| Run | Config | Time (s) | FPS | Unique Tracks |
|-----|--------|---------|-----|---------------|
| 1 | Config D | 100.85s | 58.97 | 121 |
| 2 | Config D + Re-ID | 101.64s | 58.59 | 121 |
| 3 | Config D + Gender | 100.85s | 58.97 | 121 |

**Average Performance**:
- FPS: **58.8** (excellent)
- Processing time: **101.5s** cho 3 phút
- Unique tracks: **121** (stable tracking)

## Next Steps

### Immediate (Phase 6: Data Storage)
1. PostgreSQL schema design
2. Redis caching strategy  
3. Batch insert optimization
4. Analysis scripts

### Future (Phase 7-10)
- Phase 7: Live camera pipeline
- Phase 8: Multi-channel coordination
- Phase 9: Performance optimization
- Phase 10: Deployment

## Recommendations

### Production Deployment
1. ✅ **Use Config D** for optimal performance
2. ✅ **Enable Re-ID** for ID stability
3. ⚠️ **Gender model**: Need to fine-tune hoặc download gender-specific pretrained model
4. ✅ **Monitoring**: Log FPS, unique tracks, processing time

### Gender Model Options
1. **Fine-tune timm model** trên gender dataset
2. **Download pretrained** gender model từ Hugging Face
3. **Use simple CNN** với manual training

## Conclusion

✅ **Phase 4-5 accepted**: Tracking, Re-ID, và Gender module infrastructure hoàn thành
⚠️ **Gender model**: Cần pretrained model để production
✅ **Performance**: Excellent (58 FPS)
✅ **Stability**: 121 unique tracks, no crashes

**Ready for**: Phase 6 (Data Storage)

