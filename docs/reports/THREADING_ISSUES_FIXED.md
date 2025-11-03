# Threading và Parallel Processing Issues - Fixed

**Date**: 2025-11-03  
**Status**: ✅ Fixed

---

## 🔍 VẤN ĐỀ PHÁT HIỆN

### 1. **AsyncWorker Type Mismatch** ❌
**Symptom**: 
```
WARNING - Gender/Age task failed: not enough values to unpack (expected 4, got 2)
```

**Root Cause**:
- `AsyncGenderWorker` vẫn expect 4 values: `(gender, conf, age, age_conf)`
- Nhưng code đã return chỉ 2 values: `(gender, conf)` (age disabled)
- Type mismatch giữa `Callable[[], Tuple[str, float, int, float]]` và actual return `Tuple[str, float]`

**Fix**: ✅
- Updated `_QueuedTask.func` type: `Tuple[str, float]` (gender, confidence only)
- Updated `_results` dict: `Tuple[str, float, float]` (gender, conf, timestamp)
- Updated unpacking: `gender, conf = queued.func()` (no age)

---

### 2. **Camera 2: False Track Persistence** ❌
**Symptom**: 
- Camera 2: "detected=0 persons" nhưng vẫn có "Tracks: 1"
- Track tồn tại quá lâu sau khi không có detections

**Root Cause**:
- `tracker_max_age=50` quá cao (50 frames = ~2 seconds)
- Old tracks không được remove nhanh khi không có detections
- Track `track_id=1` vẫn tồn tại sau nhiều frames không có detections

**Fix**: ✅
- Reduced `tracker_max_age`: 50 → 30 frames (~1.2 seconds)
- Tracks sẽ được remove nhanh hơn khi không có detections

---

### 3. **Gender Classification Not Called** ⚠️
**Symptom**: 
- Gender classification không được gọi ở một số channels
- Logs không thấy "Gender result stored"

**Root Cause**:
- Condition check: `self.face_gender_classifier is not None`
- Nhưng khi dùng OpenCV DNN, `self.face_gender_classifier = None` (disabled)
- Nên condition fail, không gọi gender classification

**Fix**: ✅
- Updated condition: `(self.face_gender_classifier is not None or self.gender_opencv is not None)`
- Gender classification sẽ được gọi với cả PyTorch và OpenCV models

---

## 📊 THREADING ANALYSIS

### ✅ **No Shared State Issues**
- Mỗi channel có instance riêng của `LiveCameraProcessor`
- Mỗi processor có:
  - Own `Tracker` instance
  - Own `GenderOpenCV`/`FaceGenderClassifier` instance
  - Own `AsyncGenderWorker` với thread pool riêng
  - Own queues (`_frame_queue`, `_detection_queue`)

### ✅ **Proper Threading Isolation**
- Frame reader thread: Per channel, isolated
- Detection executor: Per channel, ThreadPoolExecutor với 2 workers
- Gender worker: Per channel, AsyncGenderWorker với 2 workers
- DB executor: Per channel, 1 worker

### ✅ **No Race Conditions**
- Thread-safe queues (`queue.Queue`)
- Thread-safe results dict với locks (`_results_lock`)
- No shared global state

---

## 🔧 FIXES APPLIED

### **1. AsyncWorker Type Fix**
```python
# Before
func: Callable[[], Tuple[str, float, int, float]]  # 4 values
_results: Dict[str, Tuple[str, float, int, float, float]]

# After  
func: Callable[[], Tuple[str, float]]  # 2 values (age disabled)
_results: Dict[str, Tuple[str, float, float]]  # gender, conf, timestamp
```

### **2. Tracker max_age Fix**
```python
# Before
tracker_max_age: int = 50  # Too high

# After
tracker_max_age: int = 30  # Faster cleanup of stale tracks
```

### **3. Gender Classification Condition Fix**
```python
# Before
if (
    self.gender_enable
    and self.face_gender_classifier is not None  # Only checks PyTorch
    and self.gender_worker is not None
):

# After
if (
    self.gender_enable
    and (self.face_gender_classifier is not None or self.gender_opencv is not None)  # Both
    and self.gender_worker is not None
):
```

---

## ✅ VERIFICATION

### **Files Modified**:
1. ✅ `src/modules/demographics/async_worker.py` - Type fixes
2. ✅ `src/scripts/process_live_camera.py` - max_age và condition fixes

### **Expected Results**:
- ✅ No more "expected 4, got 2" warnings
- ✅ Camera 2 tracks removed nhanh hơn khi không có detections
- ✅ Gender classification được gọi với OpenCV DNN models

---

**Status**: Ready for testing ✅

