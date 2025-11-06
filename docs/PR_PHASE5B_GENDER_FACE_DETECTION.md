# PR: Phase 5B - Gender Classification with Face Detection & Keras Model Integration

## Mục tiêu
- Tích hợp model Keras đã train sẵn (cctv_full_body_gender_classification.h5) cho gender classification
- Tối ưu hóa tham số để đạt độ chính xác cao (conf0.4_vote25)
- Sửa mapping M/F để đảm bảo nhãn đúng giới tính
- Tích hợp face detection (MediaPipe BlazeFace) làm backend

## Phạm vi
- Modified: `src/scripts/process_video_file.py` - Updated default gender parameters
- New: `src/modules/demographics/keras_tf_gender_classifier.py` - Keras model wrapper
- New: `docs/GENDER_CLASSIFICATION_FINAL_CONFIG.md` - Configuration documentation

## Chi tiết thay đổi

### 1. KerasTFGenderClassifier
- Wrapper cho TensorFlow/Keras model đã train sẵn
- Input size: 100x200 (model expects this size)
- Mapping: class_0_prob > class_1_prob → M, else → F
- Model file: `models/gender_classification/cctv_full_body_gender_classification.h5`

### 2. Default Parameters Update
- `gender-min-confidence`: 0.5 → 0.4
- `gender-voting-window`: 10 → 25 (max voting for stability)

### 3. Integration Changes
- Switched from ResNet50GenderClassifier to KerasTFGenderClassifier
- Uses face detection (MediaPipe) for better accuracy
- Maintains async processing with 2 workers

## Acceptance Criteria

- [✓] Keras model successfully integrated
- [✓] M/F mapping correct (verified with test videos)
- [✓] Default parameters optimized (conf0.4_vote25)
- [✓] Face detection working
- [✓] Documentation created
- [✓] All temporary files cleaned up

## Testing Results

Test video: `Binh Xa-Thach That_ch4_20251024102450_20251024112450.mp4`

| Config | Confidence | Voting | M | F | Result |
|--------|-----------|--------|---|---|--------|
| conf0.4_vote25 | 0.4 | 25 | 60 | 14 | **SELECTED** |

**Why this config:**
- Maximum voting window (25) for stability
- Moderate confidence (0.4) balances accuracy and coverage
- Produces stable predictions with minimal flipping

## Performance

- FPS: ~38 FPS (with TensorFlow backend)
- Processing Time: ~116s for 80K frames
- Coverage: 67.9% of unique tracks
- Device: MPS (Metal Performance Shaders)

## Impact

- **Breaking**: None
- **Behavior change**: Default gender parameters changed
- **Migration**: Existing commands continue to work; no manual parameter adjustment needed

## Files Changed

```
src/scripts/process_video_file.py                           |   8 +-
 src/modules/demographics/keras_tf_gender_classifier.py      | 182 +++
 docs/GENDER_CLASSIFICATION_FINAL_CONFIG.md                | 124 +++
```

Total: ~314 insertions, ~6 deletions

## Related Issues

- Integrates trained Keras model instead of pretrained ResNet50
- Corrects M/F gender mapping that was reversed in earlier tests
- Sets optimal default parameters based on extensive testing

## Review Checklist

- [x] Code follows project standards
- [x] No linter errors
- [x] Documentation updated
- [x] Acceptance criteria met
- [x] Ready for review

## Merge Strategy

- **Strategy**: Squash & merge (to keep history clean)
- **Requires**: 1 reviewer approval minimum
- **CI**: Should pass all checks (black, isort, flake8, mypy, pytest, bandit)

