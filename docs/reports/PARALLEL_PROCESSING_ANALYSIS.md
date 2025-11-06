# Parallel Processing Analysis - False Positives & False Negatives

**Date**: 2025-11-03  
**Status**: ✅ No Detector Confusion - Issues Are Detection Accuracy Related

---

## 🔍 KẾT QUẢ PHÂN TÍCH

### **✅ KHÔNG CÓ NHẦM LẪN DETECTOR GIỮA CÁC CHANNELS**

#### **1. Architecture - Separate Instances** ✅

**Mỗi Channel Chạy Trong Process Riêng**:
```
Channel 1 → Process PID 5764 → LiveCameraProcessor instance 1
Channel 2 → Process PID 5773 → LiveCameraProcessor instance 2  
Channel 3 → Process PID 5767 → LiveCameraProcessor instance 3
Channel 4 → Process PID 5769 → LiveCameraProcessor instance 4
```

**Mỗi Processor Có Detector Instance Riêng**:
```python
# src/scripts/process_live_camera.py:163
self.face_detector_full = FaceDetectorOpenCV(
    min_detection_confidence=face_confidence_threshold,  # Per-channel threshold
    ...
)
```

**Evidence**:
- ✅ Lock files: `/tmp/kidsplaza_live_camera_ch{1,2,3,4}.lock` - mỗi channel riêng
- ✅ Separate PIDs - không share memory
- ✅ Instance variables (`self.face_detector_full`) - không global state

#### **2. Threading Isolation** ✅

**Mỗi Channel Có Thread Pool Riêng**:
```python
# src/scripts/process_live_camera.py:338
self._detection_executor = ThreadPoolExecutor(
    max_workers=detection_workers,  # 2 workers per channel
    thread_name_prefix="detection"  # Per-channel naming
)
```

**Parallel Processing Flow**:
```
Channel 1:
├── Frame Reader Thread (threading.Thread)
├── Detection Executor (ThreadPoolExecutor, 2 workers)
├── Gender Worker (AsyncGenderWorker, 2 workers)
└── DB Executor (ThreadPoolExecutor, 1 worker)

Channel 2: (Separate, isolated)
├── Frame Reader Thread
├── Detection Executor (separate pool)
├── Gender Worker (separate pool)
└── DB Executor (separate pool)
```

**Thread Safety**:
- ✅ `queue.Queue` - thread-safe
- ✅ No shared global state
- ✅ Instance methods operate on `self` (isolated)

#### **3. Async Detection Flow** ✅

**Per-Channel Detection**:
```python
# src/scripts/process_live_camera.py:558
self._detection_future = self._detection_executor.submit(
    self._detect_frame_async,  # Uses self.face_detector_full
    small_frame,
    current_frame_num,
    ...
)
```

**Không Có Cross-Channel Contamination**:
- ✅ `self.face_detector_full.detect_persons_from_faces(frame)` - instance method
- ✅ `frame` passed as parameter (no shared state)
- ✅ Results returned via Future (isolated)

---

## 🎯 NGUYÊN NHÂN THỰC SỰ

### **1. Channel 1 - False Positive (Motorcycle)** ⚠️

**Vấn Đề**: Detect motorcycle thành person với confidence cao

**Nguyên Nhân**: 
- **YuNet detector thực sự detect "face" từ motorcycle patterns**
  - Logs: "Found 1 raw faces from YuNet detector" liên tục
  - Confidence >= 0.45 (threshold cho Channel 1)
  - Pass qua tất cả validations (size, aspect ratio)

**Không Phải Do Parallel Processing**:
- ✅ Detector instance riêng cho Channel 1
- ✅ Threshold riêng (0.45)
- ✅ YuNet model thực sự detect false positive face

**Root Cause**:
- Motorcycle có patterns giống face (headlight, handlebar, reflections)
- YuNet (face detector) có thể bị confuse bởi patterns này
- Threshold 0.45 vẫn chưa đủ cao để reject

**Evidence từ Logs**:
```
2025-11-03 10:58:21,211 - INFO - Found 1 raw faces from YuNet detector
2025-11-03 10:58:21,211 - INFO - After NMS: 1 faces (removed 0 duplicates)
2025-11-03 10:58:21,366 - INFO - Face detection attempt: frame=3760, detected=1 persons
```

**Fix Needed**:
- Tăng threshold Channel 1: 0.45 → 0.50 hoặc 0.55
- Hoặc thêm validation: landmark quality check, texture analysis

---

### **2. Channel 4 - False Negative (Person Không Được Detect)** ⚠️

**Vấn Đề**: Có người trong frame nhưng không có bounding box

**Nguyên Nhân Có Thể**:

#### **Option 1: YuNet Không Detect Được Face** (Most Likely)
- Person quay lưng hoặc góc nhìn không rõ mặt
- Face quá nhỏ hoặc bị che khuất
- Lighting conditions không tốt

**Evidence từ Logs**:
```
2025-11-03 10:56:05,045 - INFO - Face detection attempt: frame=380, detected=0 persons
# Không có "Found raw faces" → YuNet không detect được
```

#### **Option 2: Face Bị Reject Bởi Validation**
- Confidence < 0.5 (indoor threshold)
- Size < 20x20 pixels
- Aspect ratio ngoài 0.5-1.5

**Evidence**: Logs không show "Rejected face" messages → có thể YuNet không detect được ngay từ đầu

#### **Option 3: Detection Frame Skipping**
- `detect_every_n = 4` → chỉ detect mỗi 4 frames
- Frame có person có thể bị skip
- Tracker có thể maintain track nhưng không có detection mới → không hiển thị

**Không Phải Do Parallel Processing**:
- ✅ Detector instance riêng cho Channel 4
- ✅ Threshold riêng (0.5 cho indoor)
- ✅ Tracker instance riêng
- ✅ Không có cross-contamination

**Fix Needed**:
- Kiểm tra xem person có quay mặt không
- Giảm `detect_every_n` từ 4 → 2 để detect thường xuyên hơn
- Hoặc giảm threshold indoor từ 0.5 → 0.45

---

## 📊 PARALLEL PROCESSING VERIFICATION

### **✅ No Shared State**

**Detector Instances**:
```python
# Channel 1
processor_1 = LiveCameraProcessor(channel_id=1, ...)
processor_1.face_detector_full = FaceDetectorOpenCV(confidence=0.45, ...)

# Channel 4  
processor_4 = LiveCameraProcessor(channel_id=4, ...)
processor_4.face_detector_full = FaceDetectorOpenCV(confidence=0.50, ...)
```

**Thread Pools**:
```python
# Channel 1
processor_1._detection_executor = ThreadPoolExecutor(max_workers=2, ...)

# Channel 4
processor_4._detection_executor = ThreadPoolExecutor(max_workers=2, ...)
```

**No Race Conditions**:
- ✅ Instance methods (`self.face_detector_full.detect_persons_from_faces()`)
- ✅ Thread-safe queues
- ✅ No global variables shared

---

## ✅ KẾT LUẬN

### **1. Parallel Processing Hoạt Động Đúng** ✅
- Không có nhầm lẫn detector giữa channels
- Mỗi channel isolated hoàn toàn
- Thread-safe implementation

### **2. Vấn Đề Là Detection Accuracy** ⚠️

**Channel 1 (False Positive)**:
- YuNet detector thực sự detect false positive từ motorcycle
- Cần tăng threshold hoặc thêm validation

**Channel 4 (False Negative)**:
- YuNet không detect được face (có thể do góc nhìn)
- Hoặc bị reject bởi validation
- Cần kiểm tra frame có person quay mặt không

### **3. Không Cần Fix Parallel Processing**
- Architecture đã đúng
- Isolation đã đảm bảo
- Vấn đề ở model accuracy và threshold tuning

---

## 🔧 RECOMMENDED FIXES

### **Immediate**:
1. **Channel 1**: Tăng threshold 0.45 → 0.50 hoặc 0.55
2. **Channel 4**: Kiểm tra frame để xem person có quay mặt không
3. **Channel 4**: Giảm `detect_every_n` từ 4 → 2

### **Medium-term**:
1. Thêm face quality validation (landmark check)
2. Texture analysis để reject non-face patterns
3. Motion analysis (optional)

---

**Status**: Analysis Complete - No Parallel Processing Issues Found ✅

