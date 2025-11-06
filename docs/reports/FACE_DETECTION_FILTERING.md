# Face Detection Filtering - Reduce False Positives

**Date**: 2025-11-03  
**Status**: ✅ Fixed

---

## 🔍 VẤN ĐỀ

### **Camera 1: False Positives**
- Không có người nhưng vẫn nhận diện và vẽ khung "person"
- Bounding box lớn bao quanh cả motorbike và không có người thật

### **Root Cause**
1. **Face detection confidence quá thấp**: 0.3 → nhiều false positives (shadows, objects, patterns)
2. **Không có validation face size**: Những face quá nhỏ (< 32x32) thường là false positive
3. **Không có validation aspect ratio**: Face không hợp lý (quá dẹp/dài) thường là false positive

---

## ✅ FIXES APPLIED

### **1. Tăng Face Detection Confidence Threshold**
```python
# Before
min_detection_confidence=conf_threshold  # Could be 0.3

# After
face_confidence_threshold = max(0.5, conf_threshold)  # At least 0.5
```

**Impact**:
- Loại bỏ những detections với confidence < 0.5
- Chỉ giữ lại những faces có confidence cao (more reliable)

### **2. Thêm Face Size Validation**
```python
# Minimum face size: 32x32 pixels
min_face_size = 32
if face_w_actual < min_face_size or face_h_actual < min_face_size:
    continue  # Reject too small faces (likely false positives)
```

**Impact**:
- Loại bỏ những faces quá nhỏ (thường là noise, patterns, shadows)
- Chỉ giữ lại những faces có kích thước hợp lý

### **3. Thêm Aspect Ratio Validation**
```python
# Face should be roughly square (0.7-1.3)
face_aspect_ratio = face_w_actual / face_h_actual
if face_aspect_ratio < 0.7 or face_aspect_ratio > 1.3:
    continue  # Reject invalid aspect ratios
```

**Impact**:
- Loại bỏ những detections có tỷ lệ không hợp lý (quá dẹp hoặc quá dài)
- Chỉ giữ lại những faces có tỷ lệ realistic (gần vuông)

---

## 📊 EXPECTED IMPROVEMENTS

### **Before**:
- ❌ Confidence threshold: 0.3 (quá thấp)
- ❌ No size validation
- ❌ No aspect ratio validation
- ❌ Many false positives (shadows, objects, patterns)

### **After**:
- ✅ Confidence threshold: ≥ 0.5 (higher quality)
- ✅ Size validation: ≥ 32x32 pixels
- ✅ Aspect ratio validation: 0.7-1.3
- ✅ Fewer false positives

---

## 🔧 CODE CHANGES

### **Files Modified**:
1. **`src/modules/detection/face_detector_opencv.py`**:
   - Added face size validation (min 32x32)
   - Added aspect ratio validation (0.7-1.3)

2. **`src/scripts/process_live_camera.py`**:
   - Increased face confidence threshold: `max(0.5, conf_threshold)`
   - Added logging for threshold

### **Validation Logic**:
```python
# 1. Confidence check (already existed)
if confidence < self.min_detection_confidence:
    continue

# 2. Size validation (NEW)
if face_w_actual < 32 or face_h_actual < 32:
    continue

# 3. Aspect ratio validation (NEW)
if face_aspect_ratio < 0.7 or face_aspect_ratio > 1.3:
    continue

# Only valid faces proceed to person detection
```

---

## ✅ VERIFICATION

### **Expected Behavior**:
- ✅ Camera 1: No false positives when no person present
- ✅ Only detect persons when real faces are found
- ✅ Better accuracy với higher confidence threshold

### **Monitoring**:
- Check logs for "Rejected face: too small" và "Rejected face: invalid aspect ratio"
- Monitor false positive rate trên cameras
- Adjust thresholds nếu cần (có thể tăng lên 0.6 nếu vẫn có false positives)

---

**Status**: Ready for testing ✅

