# Model Evaluation Summary - YuNet Issues & Alternatives

**Date**: 2025-11-03  
**Status**: 🔄 YuNet Adjusted | RetinaFace Evaluation Recommended

---

## 🔍 VẤN ĐỀ SAU FIX

### **Sau Khi Apply Landmark Validation**:
- ❌ Tất cả channels: `detected=0 persons` liên tục
- ❌ "Found raw faces" nhưng không có detections
- ❌ Real faces bị reject bởi:
  1. **Too small**: Faces < 20x20 sau khi scale về original size
  2. **Landmark validation quá strict**: Reject cả real faces
  3. **Threshold quá cao**: Channel 1 = 0.60 → miss real faces

---

## ✅ FIXES ĐÃ ÁP DỤNG

### **1. Channel-Aware Min Face Size**
```python
# Before: Fixed 20x20 for all
min_face_size = 20

# After: Channel-specific
if channel_id in [3, 4]:  # Indoor
    min_face_size = 16  # Faces close but may shrink after scaling
else:  # Outdoor
    min_face_size = 12  # Faces far, accept smaller after scaling
```

**Rationale**:
- Sau khi scale về original frame size, faces có thể nhỏ hơn
- Indoor: faces gần nhưng scale → nhỏ
- Outdoor: faces xa, scale → rất nhỏ

### **2. Smart Landmark Validation**
```python
# Channel 1: Always validate (motorcycle false positives)
# Other channels: Only validate confidence 0.60-0.80 (suspicious range)
if channel_id == 1:
    landmark_valid = validate(...)  # Always
elif 0.60 <= confidence < 0.80:
    landmark_valid = validate(...)  # Suspicious only
else:
    landmark_valid = True  # High confidence → trust model
```

**Rationale**:
- Real faces thường có confidence > 0.80
- Motorcycles thường có confidence 0.60-0.75
- Chỉ validate suspicious range, không reject high confidence faces

### **3. Reduced Thresholds**
```python
# Channel 1: 0.60 → 0.50 (lowered, rely on landmark validation)
face_confidence_threshold = max(0.50, conf_threshold * 1.0)
```

---

## 📊 YUNET LIMITATIONS

### **Issues Identified**:
1. **False Positives**: Detect motorcycles với confidence cao (0.60-0.75)
2. **Face Size After Scaling**: Faces trở nên quá nhỏ sau scaling
3. **Limited Accuracy**: ~85-95% (cần cải thiện)
4. **Landmark Quality**: Landmarks không đủ tốt để validate trong mọi trường hợp

### **Trade-offs**:
- ✅ Fast (5-8ms)
- ✅ No external dependencies
- ❌ Accuracy limited
- ❌ False positives từ patterns

---

## 🎯 ALTERNATIVE: RETINAFACE

### **Why RetinaFace is Better**:

**Accuracy**:
- YuNet: ~85-95%
- RetinaFace: ~95-98% ⭐

**False Positive Rate**:
- YuNet: High (motorcycles)
- RetinaFace: Low ⭐

**Angle Handling**:
- YuNet: Limited
- RetinaFace: Better ⭐

**Surveillance Performance**:
- YuNet: Good
- RetinaFace: Excellent ⭐

### **Implementation**:

**Option 1: RetinaFace Library** (Easiest)
```bash
pip install retinaface
```

```python
from retinaface import RetinaFace

results = RetinaFace.detect_faces(frame)
# Returns dict with landmarks and confidence
```

**Option 2: RetinaFace ONNX** (OpenCV DNN)
- Download ONNX model
- Use với OpenCV DNN (similar to YuNet)
- Consistent với current architecture

---

## 📝 RECOMMENDATION

### **Immediate** (Applied):
- ✅ Channel-aware min_face_size (12-16 pixels)
- ✅ Smart landmark validation (Channel 1 only, or suspicious confidence)
- ✅ Reduced thresholds (0.50 for Channel 1)

### **Short-term** (Recommended):
1. **Test RetinaFace**:
   - Install: `pip install retinaface`
   - Benchmark accuracy improvement
   - Compare false positive rates
   - Test performance impact

2. **If RetinaFace performs well**:
   - Replace YuNet with RetinaFace
   - Adjust thresholds (lower due to better accuracy)
   - Remove strict landmark validation

### **Long-term**:
- Fine-tune model on surveillance data
- Ensemble methods (combine models)
- Custom training on CCTV footage

---

## 🔧 CURRENT STATUS

### **YuNet với Fixes**:
- ✅ Channel-aware validation
- ✅ Smart landmark checking
- ✅ Adaptive thresholds
- ⚠️ Still limited by YuNet accuracy

### **RetinaFace Potential**:
- ⭐ Higher accuracy (~95-98%)
- ⭐ Better false positive handling
- ⭐ Better surveillance performance
- ⚠️ Requires external library

---

**Status**: YuNet fixes applied ✅ | RetinaFace evaluation recommended 🔄

**Next Step**: Test RetinaFace integration for accuracy improvement

