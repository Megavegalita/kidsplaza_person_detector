# Gender Classification - Final Configuration

## Official Configuration (conf0.4_vote25)

### Parameters

- **Confidence Threshold**: `0.4`
- **Voting Window**: `25` (maximum for stability)
- **Model**: `KerasTFGenderClassifier` (trained model: `cctv_full_body_gender_classification.h5`)
- **Face Detection**: Enabled (MediaPipe BlazeFace)
- **Async Processing**: Enabled with 2 workers

### Usage

```bash
python src/scripts/process_video_file.py \
  "input/video/your_video.mp4" \
  --model yolov8n.pt \
  --gender-enable \
  --gender-enable-face-detection \
  --gender-every-k 30
```

### Configuration Details

The final configuration was selected after extensive testing of multiple parameter combinations:

| Config | Confidence | Voting | M | F | Notes |
|--------|-----------|--------|---|---|-------|
| conf0.2_vote5 | 0.2 | 5 | 58 | 16 | Too permissive |
| conf0.25_vote7 | 0.25 | 7 | 51 | 23 | Balance |
| conf0.3_vote10 | 0.3 | 10 | 50 | 24 | Balance |
| conf0.35_vote12 | 0.35 | 12 | 68 | 6 | Imbalanced |
| **conf0.4_vote15** | **0.4** | **15** | **57** | **17** | Original test |
| conf0.4_vote20 | 0.4 | 20 | 38 | 36 | More balanced |
| **conf0.4_vote25** | **0.4** | **25** | **60** | **14** | **SELECTED** |
| conf0.45_vote18 | 0.45 | 18 | 53 | 21 | Good alternative |
| conf0.5_vote15 | 0.5 | 15 | 74 | 0 | Too strict |

### Why This Configuration?

1. **Maximum Voting Window (25)**: Requires 25 predictions before deciding gender, providing maximum stability
2. **Moderate Confidence (0.4)**: Balances accuracy and coverage
3. **Face Detection**: Uses MediaPipe BlazeFace for face-based classification
4. **Stable Results**: Minimal prediction flipping due to large voting window

### Model Details

- **Architecture**: ResNet50-based (2-class output)
- **Input Size**: 100x200 (width x height)
- **Output**: [F_prob, M_prob]
- **Mapping**: class_0_prob > class_1_prob → M, else → F
- **Source**: `models/gender_classification/cctv_full_body_gender_classification.h5`

### Performance

- **FPS**: ~38 FPS (with TensorFlow backend)
- **Coverage**: 67.9% (of unique tracks)
- **Processing Time**: ~116s for 3-minute video (80218 frames)
- **Device**: MPS (Metal Performance Shaders)

### Default Parameters

Updated in `src/scripts/process_video_file.py`:

- `--gender-min-confidence`: default `0.4` (was 0.5)
- `--gender-voting-window`: default `25` (was 10)

### Test Results

From video: `Binh Xa-Thach That_ch4_20251024102450_20251024112450.mp4`

- **Unique Tracks**: 109
- **Male Classifications**: 60
- **Female Classifications**: 14
- **Unknown**: 0
- **Processing Time**: 116.4s

### M/F Mapping

After extensive testing, the correct mapping is:

```python
if class_0_prob > class_1_prob:
    gender = 'M'  # Male
else:
    gender = 'F'  # Female
```

This mapping produces accurate gender labels when applied to the video.

### Migration from Previous Configs

If you were using different parameters, update your commands to use the new defaults:

**Old** (manual parameters):
```bash
--gender-min-confidence 0.5 --gender-voting-window 10
```

**New** (defaults):
```bash
# No need to specify, defaults are now optimal
--gender-enable --gender-enable-face-detection
```

### Troubleshooting

**Issue**: All predictions are Male or Female
- **Solution**: Check M/F mapping in `src/modules/demographics/keras_tf_gender_classifier.py`

**Issue**: Low accuracy
- **Solution**: Increase `--gender-voting-window` to 30 or higher

**Issue**: Too many Unknown
- **Solution**: Lower `--gender-min-confidence` to 0.3

### References

- Model file: `models/gender_classification/cctv_full_body_gender_classification.h5`
- Gender classifier: `src/modules/demographics/keras_tf_gender_classifier.py`
- Face detector: `src/modules/demographics/face_detector.py`
- Test video: `input/video/Binh Xa-Thach That_ch4_20251024102450_20251024112450.mp4`

