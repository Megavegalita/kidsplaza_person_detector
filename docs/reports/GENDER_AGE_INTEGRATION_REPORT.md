# Gender và Age Prediction Integration Report

## 📋 Tổng Quan

Đã tích hợp thành công **Gender Classification** và **Age Estimation** vào luồng xử lý camera live, sử dụng **PyTorch** (không cần MediaPipe/TensorFlow).

## ✅ Giải Pháp

### 1. **Gender Classification**
- **Module**: `FaceGenderClassifier` (PyTorch MobileNetV2)
- **Tương thích**: Hoàn toàn tương thích với OpenCV DNN face detection
- **Không cần**: MediaPipe, TensorFlow
- **Input**: Face crop từ `face_bbox` trong OpenCV detections

### 2. **Age Estimation**
- **Module**: `AgeEstimator` (PyTorch CNN)
- **Tương thích**: Hoàn toàn tương thích với OpenCV DNN
- **Input**: Face crop từ OpenCV detections
- **Output**: Age (0-100 years) + confidence

### 3. **Tích Hợp với OpenCV Face Detection**
- Sử dụng `face_bbox` có sẵn trong detections từ `FaceDetectorOpenCV`
- Không cần detect face lại (tiết kiệm thời gian)
- Fallback: upper-body crop nếu không có face_bbox

## 🔧 Thay Đổi Code

### 1. Database Model
```python
# src/modules/database/models.py
@dataclass
class PersonDetection:
    # ... existing fields ...
    age: Optional[int]
    age_confidence: Optional[float]
```

### 2. Process Live Camera
- **Enabled**: PyTorch-based gender và age classification
- **Initialization**: 
  - `FaceGenderClassifier` (MobileNetV2)
  - `AgeEstimator` (CNN)
  - `AsyncGenderWorker` (2 workers)
- **Face Crop Extraction**: Sử dụng `face_bbox` từ OpenCV detections

### 3. Async Worker
- **Updated**: Return format: `(gender, conf, age, age_conf, timestamp)`
- **Processing**: Parallel gender + age trong cùng một task

### 4. Storage
- **Age data**: Lưu vào `PersonDetection` cùng với gender
- **Tracking**: `_track_id_to_age` và `_track_id_to_age_conf` dictionaries

## 📊 Luồng Xử Lý

```
OpenCV Face Detection (YuNet)
    ↓
Person Detections (có face_bbox)
    ↓
Extract Face Crop từ face_bbox
    ↓
Async Worker (2 workers)
    ├─→ Gender Classification (MobileNetV2)
    └─→ Age Estimation (CNN)
    ↓
Store Results:
    ├─→ track_id_to_gender
    ├─→ track_id_to_age
    └─→ Database (PersonDetection)
```

## 🚀 Cách Sử Dụng

### Enable Gender/Age Classification

```bash
python src/scripts/process_live_camera.py \
    --config input/cameras_config/kidsplaza_thanhxuan.json \
    --channel-id 1 \
    --preset gender_main_v1 \
    --gender-enable  # Bật gender/age classification
```

### Config Parameters

- `--gender-enable`: Enable gender/age classification (default: False)
- `--gender-every-k`: Classify mỗi K frames (default: 10)
- `--gender-max-per-frame`: Max classifications per frame (default: 2)

## ⚙️ Technical Details

### Face Crop Extraction

1. **Primary**: Sử dụng `face_bbox` từ OpenCV detection
   ```python
   face_bbox = detection.get("face_bbox")  # [x1, y1, x2, y2]
   crop = frame[face_y1:face_y2, face_x1:face_x2]
   ```

2. **Fallback**: Upper-body crop nếu không có face_bbox
   ```python
   upper_yi2 = yi1 + int(h_box * 0.6)
   crop = frame[yi1:upper_yi2, xi1:xi2]
   ```

### Async Processing

- **Workers**: 2 threads để parallelize
- **Queue Size**: 128 tasks
- **Timeout**: 50ms per task
- **Result Format**: `(gender, conf, age, age_conf, timestamp)`

### Age Model

- **Architecture**: Simple CNN (3x224x224 input)
- **Output**: Regression (0-100 years)
- **Note**: Hiện tại dùng random initialization (cần pretrained weights cho accuracy)

## 📝 Notes

1. **Age Model**: Cần pretrained weights để có kết quả chính xác. Hiện tại model chưa được train, sẽ trả về random values.

2. **Performance**: Gender/Age classification chạy async, không block main pipeline.

3. **Compatibility**: Hoàn toàn tương thích với OpenCV DNN, không cần MediaPipe/TensorFlow.

4. **Future Improvements**:
   - Download pretrained age estimation model
   - Fine-tune trên dataset phù hợp
   - Optimize model size cho real-time

## ✅ Testing Checklist

- [x] Gender classification enabled với PyTorch
- [x] Age estimation integrated
- [x] Face crop extraction từ OpenCV detections
- [x] Database storage updated
- [x] Async worker updated
- [x] No linter errors
- [ ] Test với live camera (pending)
- [ ] Verify accuracy (pending - cần pretrained model)

## 🎯 Kết Luận

Đã tích hợp thành công gender và age prediction vào luồng hiện tại:
- ✅ **Không cần MediaPipe/TensorFlow**
- ✅ **Tương thích 100% với OpenCV DNN**
- ✅ **Async processing để không block pipeline**
- ✅ **Sử dụng face crops từ OpenCV detections**

Hệ thống sẵn sàng để test với live camera!



