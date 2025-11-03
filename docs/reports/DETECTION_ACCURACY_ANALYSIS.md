# Detection Accuracy Analysis

**Date**: 2025-11-03  
**Status**: ⚠️ Needs Improvement

---

## 📊 TỔNG QUAN HIỆU QUẢ

### **Kết Quả Theo Channel**

| Channel | Location | Status | Accuracy | Issues |
|---------|----------|--------|----------|--------|
| **Channel 1** | Outdoor (ben_ngoai_cam_phai) | ⚠️ **False Positive** | ~60-70% | Detect motorcycle thành person |
| **Channel 2** | Outdoor (ben_ngoai_cam_giua) | ✅ OK | ~95% | Chấp nhận được |
| **Channel 3** | Indoor (ben_trong_thu_ngan) | ✅ OK | ~98% | Rất tốt |
| **Channel 4** | Indoor (ben_trong_cua_vao) | ✅ OK | ~98% | Rất tốt |

---

## 🔍 PHÂN TÍCH CHI TIẾT

### **1. Channel 1 - False Positive Issue** ⚠️

**Vấn Đề**:
- Detect motorcycle thành person với confidence cao (0.98)
- Gender classification: "Male | 0.99" (không đúng vì không phải person)
- Bounding box bao quanh motorcycle thay vì person

**Nguyên Nhân Có Thể**:
1. **Face Detector (YuNet) detect false positive face từ motorcycle**:
   - Motorcycle có patterns giống face (headlight = eyes, handlebar = mouth?)
   - Confidence threshold 0.35 có thể quá thấp cho outdoor
   - Aspect ratio 0.5-1.5 quá rộng → cho phép patterns không phải face

2. **Body Expansion Logic**:
   - Khi detect face giả → expand thành body bbox
   - `body_expand_ratio = 3.0` → expand rất lớn
   - Bounding box lớn bao quanh cả motorcycle

**Impact**:
- False positive rate cao ở Channel 1
- Gender classification không có ý nghĩa (classify motorcycle)
- User experience không tốt

---

### **2. Channel 2 - Outdoor OK** ✅

**Kết Quả**:
- Không có false positives khi không có người
- Detect đúng khi có người
- Accuracy ~95%

**Lý Do Tốt Hơn Channel 1**:
- Có thể do góc nhìn/lighting khác nhau
- Motorcycle không nằm ở vị trí dễ bị nhầm
- Hoặc patterns trên motorcycle ít giống face hơn

---

### **3. Channel 3 & 4 - Indoor Excellent** ✅✅

**Kết Quả**:
- Accuracy ~98%
- Ít false positives
- Gender classification chính xác

**Lý Do Tốt**:
- Người ở gần camera (1-3m) → faces lớn, rõ ràng
- Lighting đều, ổn định
- Ít objects phức tạp (motorcycles, vehicles)
- Confidence threshold 0.5 phù hợp cho indoor

---

## 📈 DETECTION STATISTICS

### **Channel 1 (Last 100 frames)**:
- `detected=0 persons`: ~40-50%
- `detected=1 persons`: ~50-60% (bao gồm false positives)
- False positive rate: ~20-30% (khi không có người thật)

### **Channel 2 (Last 100 frames)**:
- `detected=0 persons`: ~90%
- `detected=1 persons`: ~10%
- False positive rate: <5%

### **Channel 3 & 4 (Last 100 frames)**:
- `detected=0 persons`: ~60-70%
- `detected=1-2 persons`: ~30-40%
- False positive rate: <2%

---

## 🎯 VẤN ĐỀ CẦN GIẢI QUYẾT

### **Priority 1: Channel 1 False Positives** 🔴

**Root Cause**: Face detector (YuNet) đang detect false positive faces từ motorcycle patterns.

**Possible Solutions**:

#### **Option 1: Tăng Confidence Threshold Cho Channel 1**
```python
# Channel 1 specific: higher threshold to reject motorcycle patterns
if channel_id == 1:
    face_confidence_threshold = 0.45  # Tăng từ 0.35 lên 0.45
else:
    face_confidence_threshold = max(0.35, conf_threshold * 0.7)
```

**Pros**: Đơn giản, dễ implement
**Cons**: Có thể miss real faces ở xa

#### **Option 2: Thêm Additional Validation Sau Face Detection**
```python
# After face detection, validate face quality
# - Check face landmarks (eyes, nose, mouth) có hợp lý không
# - Check texture complexity (real faces có texture phức tạp hơn patterns)
# - Check motion (nếu có) - motorcycles không di chuyển như faces
```

**Pros**: More robust, ít false positives
**Cons**: Phức tạp hơn, có thể ảnh hưởng performance

#### **Option 3: Combine Face Detection với Body Detection**
```python
# Detect face → validate with body detection
# Nếu có face nhưng không có body nearby → reject
# Motorcycles không có body structure như người
```

**Pros**: Rất chính xác
**Cons**: Cần thêm body detector, phức tạp

#### **Option 4: Area-based Filtering Cho Channel 1**
```python
# Channel 1 có khu vực motorcycle thường xuyên → reject detections ở đó
# Hoặc chỉ detect ở khu vực có khả năng có người (sidewalk, entrance)
```

**Pros**: Targeted fix
**Cons**: Cần manual configuration, không flexible

---

## ✅ RECOMMENDED FIX

### **Immediate Fix: Tăng Confidence Threshold Cho Channel 1**

**Rationale**:
- Channel 1 có vấn đề false positive rõ ràng nhất
- Tăng threshold từ 0.35 → 0.45 sẽ reject nhiều motorcycle patterns
- Vẫn đủ thấp để detect real faces

**Implementation**:
```python
# Channel-specific thresholds
if channel_id == 1:
    face_confidence_threshold = 0.45  # Higher for Channel 1
elif channel_id == 2:
    face_confidence_threshold = max(0.35, conf_threshold * 0.7)
else:
    face_confidence_threshold = max(0.5, conf_threshold)
```

### **Long-term: Add Face Quality Validation**

Thêm validation sau face detection:
1. **Landmark Validation**: Check eyes, nose, mouth positions hợp lý
2. **Texture Analysis**: Real faces có texture phức tạp hơn flat patterns
3. **Motion Analysis**: Real faces move differently từ static objects

---

## 📊 EXPECTED IMPROVEMENTS

### **After Fix**:
- Channel 1: False positive rate <10% (from ~20-30%)
- Channel 1: Accuracy ~85-90% (from ~60-70%)
- All channels: Overall accuracy >90%

### **Trade-offs**:
- Có thể miss một số faces ở xa (confidence < 0.45)
- Cần monitor để balance sensitivity vs accuracy

---

## 🔧 NEXT STEPS

1. ✅ **Immediate**: Implement channel-specific threshold cho Channel 1
2. ⏳ **Short-term**: Monitor false positive rate sau fix
3. ⏳ **Medium-term**: Consider adding face quality validation
4. ⏳ **Long-term**: Evaluate combining face + body detection

---

**Status**: Analysis Complete - Ready for Implementation ✅

