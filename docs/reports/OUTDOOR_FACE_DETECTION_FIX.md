# Outdoor Face Detection Fix - Improve Detection for Distant People

**Date**: 2025-11-03  
**Status**: ✅ Fixed

---

## 🔍 VẤN ĐỀ

### **Channel 1 & 2: Không Nhận Diện Được Person (Outdoor Cameras)**
- Channel 1: "ben_ngoai_cam_phai" (outdoor right camera)
- Channel 2: "ben_ngoai_cam_giua" (outdoor center camera)
- Người có trong hình nhưng không có bounding box
- Channel 3 & 4 (indoor) thì nhận diện đúng

### **Root Cause**
1. **Confidence threshold quá cao**: 0.5 → faces ở xa có confidence thấp hơn
2. **Min face size quá lớn**: 32x32 → faces ở xa thường nhỏ hơn
3. **Aspect ratio quá strict**: 0.7-1.3 → góc nhìn outdoor khác indoor
4. **Input size nhỏ**: 480x360 → không đủ resolution để detect faces nhỏ ở xa

**Differences Outdoor vs Indoor**:
- **Outdoor**: Người ở xa (3-5m), faces nhỏ hơn, lighting tự nhiên, góc nhìn rộng
- **Indoor**: Người ở gần (1-3m), faces lớn hơn, lighting đều, góc nhìn hẹp

---

## ✅ FIXES APPLIED

### **1. Adaptive Thresholds Based on Camera Type**

```python
# Detect outdoor vs indoor based on channel_id
is_outdoor = channel_id in [1, 2]  # Channel 1, 2: Outdoor
is_indoor = channel_id in [3, 4]    # Channel 3, 4: Indoor

if is_outdoor:
    face_confidence_threshold = max(0.35, conf_threshold * 0.7)  # 0.35 for outdoor
    input_size = (640, 480)  # Higher resolution for distant faces
else:
    face_confidence_threshold = max(0.5, conf_threshold)  # 0.5 for indoor
    input_size = (480, 360)  # Standard resolution for close faces
```

**Impact**:
- Outdoor: Lower threshold (0.35) → detect distant faces với confidence thấp hơn
- Indoor: Higher threshold (0.5) → reduce false positives
- Outdoor: Higher resolution (640x480) → better detect small faces

### **2. Reduced Minimum Face Size**

```python
# Before
min_face_size = 32  # Too large for distant faces

# After
min_face_size = 20  # Reduced to detect distant faces (2-5m distance)
```

**Impact**:
- Cho phép detect faces nhỏ hơn (20x20 pixels)
- Hợp lý cho CCTV cameras với khoảng cách 2-5m
- Vẫn đủ lớn để tránh false positives

### **3. Relaxed Aspect Ratio Validation**

```python
# Before
min_aspect = 0.7
max_aspect = 1.3

# After
min_aspect = 0.6  # Reduced from 0.7
max_aspect = 1.4  # Increased from 1.3
```

**Impact**:
- Cho phép faces với tỷ lệ rộng hơn (do góc nhìn khác nhau)
- Outdoor cameras có góc nhìn rộng hơn → aspect ratio khác indoor

### **4. Enhanced Logging**

```python
# Changed from logger.debug() to logger.info() for:
# - "Found X raw faces"
# - "After NMS: X faces"
# - "Rejected face: confidence/size/aspect ratio"
```

**Impact**:
- Có thể debug dễ dàng hơn
- Xem được số lượng raw faces detected
- Xem được lý do reject (confidence, size, aspect ratio)

---

## 📊 SETTINGS COMPARISON

### **Outdoor Cameras (Channel 1, 2)**:
| Parameter | Before | After | Reason |
|-----------|--------|-------|--------|
| Confidence | 0.5 | 0.35 | Detect distant faces |
| Input Size | 480x360 | 640x480 | Higher resolution |
| Min Face Size | 32x32 | 20x20 | Allow smaller faces |
| Aspect Ratio | 0.7-1.3 | 0.6-1.4 | Wider range |

### **Indoor Cameras (Channel 3, 4)**:
| Parameter | Before | After | Reason |
|-----------|--------|-------|--------|
| Confidence | 0.5 | 0.5 | Keep higher threshold |
| Input Size | 480x360 | 480x360 | Standard resolution |
| Min Face Size | 32x32 | 20x20 | Applied to all |
| Aspect Ratio | 0.7-1.3 | 0.6-1.4 | Applied to all |

---

## 🔧 IMPACT

### **Before**:
- ❌ Channel 1, 2: Không detect được persons (outdoor)
- ❌ Confidence 0.5 quá cao cho distant faces
- ❌ Min face size 32x32 quá lớn
- ❌ Không có logging để debug

### **After**:
- ✅ Channel 1, 2: Có thể detect persons (outdoor)
- ✅ Lower confidence (0.35) cho outdoor cameras
- ✅ Smaller min face size (20x20)
- ✅ Better logging để debug

---

## 📝 FILES MODIFIED

1. **`src/scripts/process_live_camera.py`**:
   - Added adaptive thresholds based on `channel_id`
   - Outdoor: lower confidence (0.35), higher resolution (640x480)
   - Indoor: higher confidence (0.5), standard resolution (480x360)

2. **`src/modules/detection/face_detector_opencv.py`**:
   - Reduced `min_face_size` from 32 to 20
   - Relaxed aspect ratio: 0.6-1.4 (from 0.7-1.3)
   - Enhanced logging: debug → info for visibility

---

## ✅ VERIFICATION

### **Expected Behavior**:
- ✅ Channel 1, 2: Detect được persons ở outdoor
- ✅ Logs hiển thị "Found X raw faces" để debug
- ✅ Tỷ lệ detection cao hơn cho outdoor cameras

### **Monitoring**:
- Check logs for "Found X raw faces" để xem YuNet có detect không
- Check "Rejected face" logs để xem lý do reject
- Adjust thresholds nếu cần (có thể giảm thêm confidence cho outdoor)

---

**Status**: Ready for testing ✅

