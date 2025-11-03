# Phân Tích Tối Ưu CPU/GPU và Multi-threading

**Date**: 2025-11-02

## Tổng Quan Hiện Tại

### ✅ ĐÃ CÓ Multi-threading

#### 1. **Frame Reading Thread** ✅
```python
# Line 271: Frame reader thread
self._frame_reader_thread: Optional[threading.Thread] = None

# Line 284-323: Worker thread để đọc frames
def _frame_reader_worker(self, camera_reader):
    while not self._shutdown_requested:
        frame = camera_reader.read_frame()
        self._frame_queue.put_nowait(frame)
```

**Status**: ✅ Hoạt động tốt
- Producer-consumer pattern
- Queue maxsize=2 (giảm lag)
- Non-blocking frame reading

#### 2. **Async Detection Processing** ✅
```python
# Line 267: ThreadPoolExecutor cho detection
self._detection_executor = ThreadPoolExecutor(max_workers=1, ...)

# Line 1041-1091: Async detection function
def _detect_frame_async(self, frame, frame_num):
    # Run face detection in worker thread
    detections = self.face_detector_full.detect_persons_from_faces(frame)
```

**Status**: ✅ Hoạt động nhưng **chỉ 1 worker**

#### 3. **Async Database Writes** ✅
```python
# Line 268: ThreadPoolExecutor cho DB writes
self._db_executor = ThreadPoolExecutor(max_workers=1, ...) if db_enable else None

# Line 1093-1109: Async DB storage
def _store_detections_async(self, detections, ...):
    # Store in background thread
```

**Status**: ✅ Hoạt động tốt

---

## ❌ CHƯA TỐI ƯU GPU

### 1. **OpenCV DNN Không Sử Dụng GPU Backend**

**Current Implementation**:
```python
# face_detector_opencv.py:90-94
self.face_detector = cv2.FaceDetectorYN.create(
    model_path,
    "",
    self.input_size,
    self.min_detection_confidence
)
# ❌ KHÔNG set GPU backend!
```

**Vấn đề**:
- OpenCV DNN mặc định dùng CPU
- Chưa enable CUDA/OpenCL/Metal backend
- Không tận dụng GPU cho inference

**Có thể cải thiện**:
```python
# Có thể set GPU backend nếu có:
net = cv2.dnn.readNetFromONNX(model_path)
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)  # For NVIDIA
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
# Hoặc
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_OPENCL)  # For AMD/Intel
```

### 2. **Apple Silicon MPS Không Được Dùng**

**Current**: Đã disable YOLOv8 detector (dùng face detection)
- YOLOv8 có MPS support nhưng không được dùng
- Face detection (OpenCV DNN) không có MPS support

**Mất mát**: 
- Apple Silicon GPU (Metal) không được tận dụng
- Chỉ dùng CPU cores

---

## ⚠️ CHƯA TỐI ƯU PARALLEL PROCESSING

### 1. **Detection Executor Chỉ 1 Worker**

```python
# Line 267
self._detection_executor = ThreadPoolExecutor(max_workers=1, ...)
```

**Vấn đề**:
- Chỉ có 1 thread cho detection
- Không thể process nhiều frames song song
- Với 4 channels, mỗi channel chỉ có 1 worker

**Có thể cải thiện**:
- Tăng `max_workers=2` hoặc 3 (tùy CPU cores)
- Cho phép xử lý nhiều detection tasks song song

### 2. **Re-ID Embedding Không Parallel**

**Current**: Re-ID embedding chạy tuần tự trong main thread

```python
# integrator.py - chạy tuần tự
for det in detections_with_tracks:
    crop = processor.crop_person(frame, bbox)
    emb = embedder.embed(crop)  # ❌ Chạy tuần tự
```

**Có thể cải thiện**:
- Parallelize embedding cho nhiều detections cùng lúc
- Sử dụng ThreadPoolExecutor hoặc batch processing

### 3. **NMS Chạy Trên Main Thread**

Face detection NMS chạy trong main detection thread:
```python
# face_detector_opencv.py:326
def _nms_faces(self, faces, iou_threshold=0.3):
    # Chạy trên CPU, trong main thread
    indices = cv2.dnn.NMSBoxes(...)
```

**Status**: OK (NMS nhanh, không cần parallelize)

---

## 📊 Đánh Giá Hiện Tại

| Component | Status | Workers | GPU Support | Có thể cải thiện |
|-----------|--------|--------|-------------|------------------|
| **Frame Reading** | ✅ | 1 thread | N/A | OK |
| **Face Detection** | ⚠️ | 1 worker | ❌ No GPU | ⭐ Enable GPU backend |
| **Tracking** | ✅ | Main thread | N/A | OK |
| **Re-ID Embedding** | ⚠️ | Sequential | ❌ No GPU | ⭐ Parallelize |
| **DB Writes** | ✅ | 1 worker | N/A | OK |
| **Display** | ✅ | Main thread | N/A | OK |

---

## 🎯 Khuyến Nghị Cải Thiện

### Priority 1: Enable GPU Backend cho OpenCV DNN ⭐⭐⭐

```python
# Trong face_detector_opencv.py
def __init__(self, ...):
    # ...
    # Try to enable GPU backend
    self.face_detector = cv2.FaceDetectorYN.create(...)
    
    # Try CUDA first (NVIDIA)
    try:
        if cv2.cuda.getCudaEnabledDeviceCount() > 0:
            # OpenCV DNN with CUDA
            net = cv2.dnn.readNetFromONNX(model_path)
            net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
            net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
            logger.info("Using CUDA backend for face detection")
    except:
        pass
    
    # Try OpenCL (AMD/Intel)
    try:
        if cv2.ocl.haveOpenCL():
            cv2.ocl.setUseOpenCL(True)
            logger.info("Using OpenCL backend for face detection")
    except:
        pass
```

### Priority 2: Tăng Detection Workers ⭐⭐

```python
# Line 267 - tăng từ 1 → 2 hoặc 3
import os
num_cores = os.cpu_count() or 4
detection_workers = min(2, num_cores // 2)  # 1-2 workers

self._detection_executor = ThreadPoolExecutor(
    max_workers=detection_workers,
    thread_name_prefix="detection"
)
```

### Priority 3: Parallelize Re-ID Embedding ⭐

```python
# Trong integrator.py
from concurrent.futures import ThreadPoolExecutor

def integrate_reid_for_tracks(..., embedder, ...):
    # Batch embeddings
    executor = ThreadPoolExecutor(max_workers=2)
    futures = []
    
    for det in detections_with_tracks:
        future = executor.submit(_embed_detection, det, embedder, frame)
        futures.append(future)
    
    # Collect results
    for future in futures:
        emb = future.result()
        # Process embedding
```

### Priority 4: Batch Processing cho Face Detection ⭐

```python
# Process multiple frames at once
def detect_batch(self, frames: List[np.ndarray]) -> List[List[Dict]]:
    # Batch detect nhiều frames cùng lúc
    # Sử dụng GPU nếu có
```

---

## 💻 Hardware Utilization Hiện Tại

### CPU Usage
- ✅ Frame reading: Parallel thread
- ✅ Detection: 1 worker thread
- ✅ DB writes: 1 worker thread
- ⚠️ Main thread: Tracking, Re-ID, Display

### GPU Usage
- ❌ **Face Detection**: CPU only (OpenCV DNN không enable GPU)
- ❌ **Re-ID Embedding**: CPU only
- ❌ **Apple Silicon MPS**: Không được dùng (đã bỏ YOLOv8)

---

## 📈 Tác Động Cải Thiện

### Nếu Enable GPU Backend:
- **Face Detection**: 2-5x nhanh hơn (tùy GPU)
- **Tổng FPS**: Có thể đạt 30+ FPS per channel

### Nếu Tăng Detection Workers:
- **Multiple Channels**: Xử lý tốt hơn khi có nhiều người
- **Latency**: Giảm khi có backlog

### Nếu Parallelize Re-ID:
- **Re-ID Processing**: Nhanh hơn 2-3x khi có nhiều detections

---

## Kết Luận

### ✅ Đã Có:
- Multi-threading cơ bản (frame reading, async detection, async DB)
- Producer-consumer pattern
- Non-blocking operations

### ❌ Chưa Có:
- GPU acceleration cho OpenCV DNN
- Multiple detection workers
- Parallel Re-ID embedding
- Batch processing

### 🎯 Ưu Tiên Cải Thiện:
1. **Enable GPU backend** cho OpenCV DNN (highest impact)
2. **Tăng detection workers** (medium impact)
3. **Parallelize Re-ID** (low impact, nhưng có thể giúp khi nhiều người)


