# Gender Classification - Hiện Trạng & Giải Pháp

**Date**: 2025-11-02  
**Status**: 📊 Đánh giá hoàn tất - Sẵn sàng cải thiện

---

## 📊 HIỆN TRẠNG

### 1. **Models Hiện Có**

| Model | Type | Input | Training | Status | Accuracy Estimate |
|-------|------|-------|----------|--------|-------------------|
| **AgeGenderOpenCV** | OpenCV DNN (Caffe) | Face crop | Adience dataset | ✅ Đang dùng | ~85-90% (gender) |
| **FaceGenderClassifier** | PyTorch MobileNetV2 | Face crop | ImageNet + UTKFace | ✅ Fallback | ~80-85% (face-only) |
| **GenderClassifier** | PyTorch (timm MobileNetV3) | Body crop | ImageNet | ⚠️ Không dùng | ~75-80% (body-only) |
| **ResNet50GenderClassifier** | PyTorch ResNet50 | Face crop | ImageNet | ⚠️ Không dùng | ~85-90% (chậm hơn) |
| **KerasTFGenderClassifier** | TensorFlow Keras | Body crop | Custom trained | ⚠️ Không dùng | ~70-75% (cũ) |

### 2. **Code Flow Hiện Tại**

```
Detection → Tracking → Gender/Age Classification
                        ↓
            ┌─────────────────────────┐
            │ AgeGenderOpenCV (Ưu tiên)│
            │  - Age estimation       │
            │  - Gender classification│
            └─────────────────────────┘
                        ↓ (nếu fail)
            ┌─────────────────────────┐
            │ FaceGenderClassifier    │
            │  - Gender only          │
            │  - AgeEstimatorPyTorch  │
            └─────────────────────────┘
                        ↓
            Voting mechanism (gender + age)
                        ↓
            Storage + Display
```

### 3. **Vấn Đề Hiện Tại**

#### ❌ **Vấn đề 1: Age Estimation không chính xác**
- AgeGenderOpenCV: Models từ Adience nhưng có thể không tối ưu cho Asian faces
- AgeEstimatorPyTorch: Fallback models (ResNet18/Hugging Face) chưa được train đúng
- **Impact**: Age predictions không đáng tin cậy, user muốn tắt

#### ⚠️ **Vấn đề 2: Gender Accuracy chưa tối ưu**
- **Current**: OpenCV DNN gender (~85-90% trên Adience)
- **Issues**:
  - Face crops có thể nhỏ/không rõ → giảm accuracy
  - Voting mechanism có thể chưa đủ mạnh
  - Confidence thresholds có thể chưa tối ưu (hiện tại 0.60 cho display)
  - Không có fine-tuning cho dataset cụ thể (Kidsplaza Asian faces)

#### 📊 **Vấn đề 3: Code complexity**
- Logic age/gender bị trộn lẫn
- Voting mechanism xử lý cả age và gender
- Storage và display logic phức tạp
- Khó maintain và optimize riêng gender

---

## 🎯 GIẢI PHÁP

### **Phase 1: Tắt Age Estimation** ✅ (Ưu tiên)

**Mục tiêu**: Loại bỏ hoàn toàn age estimation để tập trung vào gender

**Thay đổi**:
1. ✅ Disable age initialization
2. ✅ Remove age storage logic
3. ✅ Remove age display logic
4. ✅ Simplify voting mechanism (chỉ gender)
5. ✅ Clean up age-related code

**Files cần sửa**:
- `src/scripts/process_live_camera.py`: 
  - Dòng 242-290: Remove age estimator initialization
  - Dòng 844-966: Simplify voting (remove age)
  - Dòng 1032-1096: Remove age estimation calls
  - Dòng 671-678: Remove age display
  - Dòng 320-322: Remove age tracking dicts

### **Phase 2: Cải Thiện Gender Classification** 🚀

#### **Option A: Tối ưu OpenCV DNN (Recommended - Fast)**
- **Pros**: 
  - Đã có models, không cần train
  - Fast inference (OpenCL GPU support)
  - Good baseline accuracy (~85-90%)
- **Cons**: 
  - Không thể fine-tune (pretrained Caffe models)
  - Có thể chưa tối ưu cho Asian faces

**Cải thiện**:
1. ✅ Better face crop preprocessing:
   - Increase face crop padding
   - Better face detection confidence threshold
   - Validate face crop size (minimum 64x64)
2. ✅ Tune confidence thresholds:
   - Current: 0.60 for display
   - Suggest: 0.65-0.70 for better accuracy
   - Separate thresholds for M/F nếu cần
3. ✅ Improve voting mechanism:
   - Increase voting window (10 → 15-20 frames)
   - Weight by confidence scores
   - Temporal smoothing (EMA)
4. ✅ Face crop quality:
   - Use best face detection (highest confidence)
   - Multiple face crops per person (average predictions)

#### **Option B: Fine-tune PyTorch Model (Best Accuracy)**
- **Pros**:
  - Có thể fine-tune trên dataset cụ thể
  - Better accuracy cho Asian faces (~90-95%)
  - Flexible architecture
- **Cons**:
  - Cần dataset và training
  - Slower inference (có thể optimize)
  - More complex deployment

**Implementation**:
1. Sử dụng ResNet50 hoặc EfficientNet
2. Fine-tune trên UTKFace + custom Asian dataset
3. Transfer learning từ ImageNet pretrained
4. Optimize inference (quantization, ONNX export)

#### **Option C: Ensemble (Best of Both)**
- Combine OpenCV DNN + PyTorch models
- Weighted voting based on confidence
- Fallback mechanism

---

## 📋 KẾ HOẠCH CHI TIẾT

### **Step 1: Disable Age (Immediate)** ✅
- [x] Remove age estimator initialization
- [x] Remove age from voting logic
- [x] Remove age from storage
- [x] Remove age from display
- [x] Clean up age-related variables

### **Step 2: Optimize Gender - OpenCV DNN (Quick Wins)** 🎯
- [ ] Improve face crop quality:
  - Increase padding (current: 20%, suggest: 30-40%)
  - Minimum size validation (64x64)
  - Use best face (highest confidence)
- [ ] Tune confidence thresholds:
  - Display: 0.60 → 0.65-0.70
  - Storage: 0.50 → 0.55
  - Separate M/F thresholds if needed
- [ ] Enhance voting:
  - Window: 10 → 15-20 frames
  - Confidence-weighted voting
  - Temporal smoothing (EMA α=0.7)
- [ ] Better preprocessing:
  - Face alignment (optional)
  - Histogram equalization (optional)
  - Better interpolation for small crops

### **Step 3: Advanced Improvements (Future)** 🔮
- [ ] Fine-tune PyTorch model trên Asian faces
- [ ] Ensemble multiple models
- [ ] Multi-face crops per person (average)
- [ ] Active learning for continuous improvement

---

## 🔍 METRICS ĐỂ ĐÁNH GIÁ

### **Current Metrics**
- Gender accuracy: ~85-90% (estimate)
- Display threshold: 0.60
- Voting window: 10 frames
- Face crop min: 48x48

### **Target Metrics**
- Gender accuracy: **>90%** cho Asian faces
- Display threshold: 0.65-0.70 (reduce false positives)
- Voting window: 15-20 frames (better stability)
- Face crop min: 64x64 (better quality)

---

## 💡 RECOMMENDATIONS

### **Immediate (Phase 1)**:
1. ✅ **Tắt age estimation** để simplify code
2. 🎯 **Tối ưu OpenCV DNN gender** (Option A) - Quick wins:
   - Better face crops
   - Tune thresholds
   - Improve voting

### **Short-term (Phase 2)**:
3. 📊 **Benchmark current accuracy** trên real data
4. 🔧 **Fine-tune nếu cần** (Option B) - nếu accuracy < 90%

### **Long-term (Phase 3)**:
5. 🚀 **Ensemble models** (Option C) - best accuracy
6. 📈 **Continuous improvement** với active learning

---

## 📝 FILES CẦN SỬA

### **Phase 1: Disable Age**
1. `src/scripts/process_live_camera.py` - Main processing script
2. `src/modules/detection/image_processor.py` - Display logic (nếu có age)
3. Tests và docs

### **Phase 2: Gender Improvements**
1. `src/modules/demographics/age_gender_opencv.py` - Gender classification
2. `src/scripts/process_live_camera.py` - Voting và thresholds
3. `src/modules/detection/face_detector_opencv.py` - Face crop quality

---

## ✅ NEXT STEPS

1. **Bây giờ**: Tắt age estimation (Phase 1)
2. **Tiếp theo**: Tối ưu gender với OpenCV DNN (Phase 2, Option A)
3. **Sau đó**: Benchmark và fine-tune nếu cần (Phase 2, Option B)

---

**Status**: Ready for implementation ✅

