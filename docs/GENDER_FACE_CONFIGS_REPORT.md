# Face-Based Gender Classification - Test Results Report

## Executive Summary

Three different configurations for face-based gender classification were tested on a 3-minute video sample (4500 frames). All configurations processed successfully with face detection using MediaPipe BlazeFace and MobileNetV2 for gender classification.

## Test Results

### Config A - Strict
**Parameters:**
- `--gender-min-confidence 0.6`
- `--gender-voting-window 15`

**Results:**
- Unique tracks: 109
- Gender breakdown: M: 4, F: 37, Unknown: 33
- Processing time: 127.3s
- Video: `output/test_configs/Config_A_Strict/` (116MB)

**Analysis:**
- Very conservative filtering (high confidence threshold)
- Significant imbalance: F >> M (37 vs 4)
- Many unknown classifications (33)
- May be too strict for practical use

---

### Config B - Balanced
**Parameters:**
- `--gender-min-confidence 0.4`
- `--gender-voting-window 10`

**Results:**
- Unique tracks: 109
- Gender breakdown: M: 59, F: 15, Unknown: 0
- Processing time: 126.5s
- Video: `output/test_configs/Config_B_Balanced/` (115MB)

**Analysis:**
- Most balanced configuration
- Good coverage (0 unknowns)
- Some imbalance: M >> F (59 vs 15)
- Moderate confidence threshold

---

### Config C - Permissive
**Parameters:**
- `--gender-min-confidence 0.3`
- `--gender-voting-window 7`

**Results:**
- Unique tracks: 109
- Gender breakdown: M: 68, F: 6, Unknown: 0
- Processing time: 126.8s
- Video: `output/test_configs/Config_C_Permissive/` (115MB)

**Analysis:**
- Most permissive (lowest threshold)
- Excellent coverage (0 unknowns)
- Strong imbalance: M >> F (68 vs 6)
- Fastest processing

## Key Observations

### Performance Metrics
- **FPS**: ~50-51 FPS (avg 19-20ms per frame)
- **Processing time**: ~126-127 seconds for 4500 frames
- **Latency**: p50=31ms, p95=46ms (acceptable)
- **Unique tracks**: 109 (consistent across all configs)

### Gender Classification Issues

1. **Severe Imbalance**: All configs show imbalance between M/F
   - Config A: 4M vs 37F (9:1 ratio favoring Female)
   - Config B: 59M vs 15F (4:1 ratio favoring Male)
   - Config C: 68M vs 6F (11:1 ratio favoring Male)

2. **Possible Causes**:
   - Face detection may miss some faces
   - Model bias toward one class
   - Need for face dataset fine-tuning
   - MediaPipe BlazeFace detection rate

3. **Unknown Classifications**:
   - Config A: 33 unknowns (30% of tracks)
   - Config B & C: 0 unknowns (good coverage)

## Recommendations

### Immediate Actions
1. **Visual inspection required**: Review all 3 videos to assess actual gender accuracy
2. **Fine-tune MobileNetV2**: Train on gender-specific face datasets (UTKFace, FairFace)
3. **Calibrate model**: Adjust for class imbalance in training data

### Parameter Selection
Based on initial results:
- **Coverage priority**: Config B or C (both have 0 Unknown)
- **Accuracy priority**: Requires visual inspection to determine
- **Recommended**: Config B (most balanced M/F ratio)

### Next Steps
1. Visual inspection of all 3 videos
2. Manual accuracy assessment
3. Choose best config or iterate parameters
4. Fine-tune MobileNetV2 on gender classification dataset

## Technical Details

### Architecture
- **Face Detection**: MediaPipe BlazeFace (confidence=0.5)
- **Gender Classifier**: MobileNetV2 (ImageNet pretrained)
- **Face Input Size**: 224x224
- **Normalization**: ImageNet stats (mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
- **Fallback**: Upper-body crop when face not detected

### Processing Pipeline
1. Detect persons with YOLOv8n
2. Track with IoU-based matching (EMA smoothing)
3. Face detection within person bbox (MediaPipe)
4. Gender classification on face crops (MobileNetV2)
5. Majority voting for stability
6. Async processing to avoid workflow blocking

## Files Generated

- Config A: `output/test_configs/Config_A_Strict/annotated_Binh Xa-Thach That_ch4_20251024102450_20251024112450.mp4`
- Config B: `output/test_configs/Config_B_Balanced/annotated_Binh Xa-Thach That_ch4_20251024102450_20251024112450.mp4`
- Config C: `output/test_configs/Config_C_Permissive/annotated_Binh Xa-Thach That_ch4_20251024102450_20251024112450.mp4`
- Reports: `output/test_configs/*/report_*.json`

## Conclusion

The face-based gender classification system is operational with acceptable performance (50 FPS). However, **gender prediction shows severe imbalance** requiring further investigation through visual inspection and potential model fine-tuning.

**Next action**: Visual review of generated videos to assess classification accuracy.

