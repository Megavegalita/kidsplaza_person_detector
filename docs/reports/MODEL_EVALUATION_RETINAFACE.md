# Model Evaluation - RetinaFace Integration

**Date**: 2025-11-03  
**Status**: 🔄 Evaluation in Progress

---

## 🔍 CURRENT ISSUE

### **Problem**: YuNet Too Restrictive After Fixes
- Landmark validation quá strict → reject cả real faces
- Channel 1: threshold 0.60 + landmark validation → không detect được
- Channel 3, 4: "Found raw faces" nhưng không có detections → có thể bị reject

### **Root Cause**:
1. **Landmark validation quá strict**: Tolerances (20%, 25%, 30%) quá nhỏ cho góc nhìn khác nhau
2. **Threshold quá cao**: 0.60 có thể miss real faces với confidence thấp hơn
3. **YuNet limitations**: Model không đủ tốt cho surveillance scenarios

---

## 🎯 SOLUTION: EVALUATE RETINAFACE

### **Why RetinaFace?**

**Advantages over YuNet**:
- ✅ **Higher accuracy**: ~95-98% vs YuNet ~85-95%
- ✅ **Better false positive handling**: Ít detect motorcycles hơn
- ✅ **Better angle handling**: Detect faces ở nhiều góc độ hơn
- ✅ **Landmark support**: Built-in face landmarks (better than YuNet)
- ✅ **Surveillance optimized**: Designed for CCTV/security use cases

**Trade-offs**:
- ⚠️ Slightly slower: ~10-15ms vs YuNet ~5-8ms (still acceptable for 24 FPS)
- ⚠️ Requires external library: `pip install retinaface`

---

## 📦 RETINAFACE INTEGRATION PLAN

### **Option 1: RetinaFace Library (Easiest)** ⭐ RECOMMENDED

**Installation**:
```bash
pip install retinaface
```

**Integration**:
```python
from retinaface import RetinaFace

# Detect faces
results = RetinaFace.detect_faces(frame)
# Returns dict: {
#   "face_1": {
#       "facial_area": [x, y, w, h],
#       "landmarks": {
#           "right_eye": [x, y],
#           "left_eye": [x, y],
#           "nose": [x, y],
#           "mouth_right": [x, y],
#           "mouth_left": [x, y]
#       },
#       "score": confidence
#   }
# }
```

**Pros**:
- ✅ Simple integration
- ✅ Good accuracy
- ✅ Built-in landmarks

**Cons**:
- ⚠️ External dependency
- ⚠️ May need GPU for best performance

---

### **Option 2: RetinaFace ONNX (OpenCV DNN)** ⭐⭐ ALTERNATIVE

**Download Model**:
- ONNX model from: https://github.com/deepinsight/insightface
- Or: https://github.com/wanghongfei/Retinaface_Onnx

**Integration**:
```python
import cv2

net = cv2.dnn.readNetFromONNX("retinaface.onnx")
# Similar to YuNet integration
```

**Pros**:
- ✅ No external library (uses OpenCV DNN)
- ✅ Consistent với current architecture

**Cons**:
- ⚠️ Need to find/download ONNX model
- ⚠️ May need preprocessing adjustments

---

## 🔧 IMMEDIATE FIX: SMART LANDMARK VALIDATION

### **Applied**: Only Validate Suspicious Confidence Range

```python
# Only apply landmark validation for faces with confidence 0.60-0.80
# Real faces usually have confidence > 0.80
# Motorcycles often have confidence 0.60-0.75
if 0.60 <= confidence < 0.80:
    landmark_valid = self._validate_face_landmarks(...)
```

**Rationale**:
- High confidence (>0.80) → likely real face → skip validation
- Low confidence (<0.60) → already rejected by threshold
- Medium confidence (0.60-0.80) → suspicious → validate landmarks

**Expected Impact**:
- ✅ Real faces (confidence > 0.80) pass without validation
- ✅ Motorcycles (confidence 0.60-0.75) get validated and rejected
- ✅ Less strict → fewer false negatives

---

## 📊 COMPARISON: RETINAFACE vs YUNET

| Feature | YuNet (Current) | RetinaFace |
|---------|-----------------|------------|
| **Accuracy** | ~85-95% | ~95-98% |
| **Speed** | 5-8ms | 10-15ms |
| **False Positives** | High (motorcycles) | Low |
| **Angle Handling** | Limited | Better |
| **Landmarks** | Basic (5 points) | Better quality |
| **Surveillance** | Good | Excellent |
| **Dependencies** | OpenCV only | External library |

---

## 🎯 RECOMMENDATION

### **Immediate** (Applied):
1. ✅ Smart landmark validation (only validate suspicious confidence range)
2. ✅ Relaxed tolerances (20% → 30%, 25% → 35%, 30% → 40%)

### **Short-term** (Evaluate):
1. **Test RetinaFace**:
   - Install: `pip install retinaface`
   - Create RetinaFace detector module
   - Benchmark accuracy vs YuNet
   - Test false positive rate

2. **If RetinaFace performs well**:
   - Replace YuNet with RetinaFace
   - Adjust thresholds (lower due to better accuracy)
   - Remove strict landmark validation (RetinaFace has better accuracy)

### **Long-term**:
- Fine-tune RetinaFace on surveillance data
- Ensemble methods (combine YuNet + RetinaFace)
- Custom model training

---

## 📝 IMPLEMENTATION STATUS

### **Current Fixes Applied**:
- ✅ Smart landmark validation (confidence-based)
- ✅ Relaxed tolerances
- ✅ Better logging

### **Next Steps**:
1. Monitor detection rates with smart validation
2. Evaluate RetinaFace integration
3. Compare accuracy improvements

---

**Status**: Smart validation applied ✅ | RetinaFace evaluation pending 🔄

