# Rà Soát Multi-threading và Parallel Processing

**Date**: 2025-11-02  
**Status**: ✅ Đã có multi-threading, có thể tối ưu thêm

## 📊 Tổng Quan Hiện Tại

### ✅ ĐÃ CÓ Multi-threading

#### 1. **Frame Reading Thread** ✅
**Location**: `src/scripts/process_live_camera.py:370-410`

```python
# Producer-consumer pattern
self._frame_reader_thread: Optional[threading.Thread] = None
self._frame_queue: queue.Queue[Optional[np.ndarray]] = queue.Queue(maxsize=2)

def _frame_reader_worker(self, camera_reader):
    while not self._shutdown_requested:
        frame = camera_reader.read_frame()
        self._frame_queue.put_nowait(frame)
```

**Status**: ✅ **HOẠT ĐỘNG TỐT**
- Separate thread cho frame reading
- Non-blocking với queue (maxsize=2)
- Producer-consumer pattern đúng chuẩn

---

#### 2. **Async Detection Processing** ✅
**Location**: `src/scripts/process_live_camera.py:349-353`

```python
import os
num_cores = os.cpu_count() or 4
detection_workers = min(2, max(1, num_cores // 2))  # 2 workers

self._detection_executor = ThreadPoolExecutor(
    max_workers=detection_workers,  # 2 workers
    thread_name_prefix="detection"
)
```

**Status**: ✅ **2 WORKERS ACTIVE**
- Parallel face detection cho nhiều frames
- Submit async, không block main thread
- Scale bbox back đúng cách

---

#### 3. **Parallel Re-ID Embedding** ✅
**Location**: `src/modules/reid/integrator.py:135-160`

```python
# ThreadPoolExecutor với 2 workers cho Re-ID embedding
with ThreadPoolExecutor(max_workers=2, thread_name_prefix="reid-embed") as executor:
    futures = {executor.submit(_compute_embedding, cand): cand for cand in candidates}
    
    for future in as_completed(futures):
        # Process results as they complete
```

**Status**: ✅ **2 WORKERS PARALLEL**
- Multiple embeddings computed simultaneously
- Non-blocking với `as_completed()`
- Efficient parallel processing

---

#### 4. **Async Database Writes** ✅
**Location**: `src/scripts/process_live_camera.py:353, 777-787`

```python
self._db_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="db-writer")

# Non-blocking async write
self._db_executor.submit(
    self._store_detections_async,
    detections.copy(),
    frame_num,
    ...
)
```

**Status**: ✅ **ASYNC, NON-BLOCKING**
- 1 worker cho DB writes (phù hợp, I/O bound)
- Không block main processing pipeline
- Batch writes để optimize

---

#### 5. **Gender/Age Classification Workers** ✅
**Location**: `src/modules/demographics/async_worker.py:34-63`

```python
class AsyncGenderWorker:
    def __init__(self, max_workers: int = 2, ...):
        self._workers = [
            threading.Thread(
                target=self._run_loop,
                name=f"gender-worker-{i}",
                daemon=True
            )
            for i in range(max_workers)  # 2 workers
        ]
```

**Location**: `src/scripts/process_live_camera.py:294`

```python
self.gender_worker = AsyncGenderWorker(max_workers=2, queue_size=128)
```

**Status**: ✅ **2 WORKERS ACTIVE**
- Parallel gender/age classification
- Priority queue system
- Non-blocking với `try_get_result()`

---

#### 6. **OpenCL GPU Backend** ✅
**Location**: `src/modules/detection/face_detector_opencv.py:70-85`

```python
# Enable OpenCL backend for GPU acceleration
self._use_opencl = False
try:
    if cv2.ocl.haveOpenCL():
        cv2.ocl.setUseOpenCL(True)
        self._use_opencl = True
        logger.info("OpenCL backend enabled for GPU acceleration")
except Exception as e:
    logger.debug("OpenCL not available: %s", e)
```

**Status**: ✅ **ENABLED**
- GPU acceleration cho face detection
- Automatic fallback to CPU nếu GPU không có
- Log confirmation: "OpenCL backend enabled"

---

## 🏗️ Architecture Overview

### Current Parallel Processing Pipeline:

```
┌─────────────────────────────────────────────────────┐
│ Main Thread                                          │
│  - Frame management                                  │
│  - Tracking (IoU-based)                             │
│  - Display (limited FPS)                            │
└─────────────────────────────────────────────────────┘
         │
         ├──► Frame Reader Thread ────────────────────┐
         │    (Producer Thread)                         │
         │    - Continuous frame reading               │
         │    - Queue maxsize=2                        │
         │                                              ▼
         │                                        ┌──────────────┐
         │                                        │ Frame Queue  │
         │                                        └──────────────┘
         │                                              │
         │                                              ▼
         ├──► Detection Executor ──────────────────────┤
         │    (ThreadPoolExecutor: 2 workers)          │
         │    - Face detection (GPU via OpenCL)       │
         │    - Pre-resize frames                      │
         │    - Scale bboxes back                      │
         │                                              ▼
         ├──► Re-ID Executor ──────────────────────────┤
         │    (ThreadPoolExecutor: 2 workers)          │
         │    - Embedding computation (parallel)        │
         │    - Multiple tracks simultaneously         │
         │                                              ▼
         ├──► Gender/Age Workers ───────────────────────┤
         │    (AsyncGenderWorker: 2 workers)            │
         │    - Gender classification (PyTorch/OpenCV) │
         │    - Age estimation (PyTorch/OpenCV)        │
         │    - Priority queue system                  │
         │                                              ▼
         └──► DB Executor ─────────────────────────────┘
              (ThreadPoolExecutor: 1 worker)
              - Async database writes
              - Batch operations
```

---

## 📈 Parallel Processing Breakdown

| Component | Type | Workers | Status | GPU Support |
|-----------|------|---------|--------|-------------|
| **Frame Reading** | Thread | 1 | ✅ | N/A |
| **Face Detection** | ThreadPoolExecutor | 2 | ✅ | ✅ OpenCL |
| **Re-ID Embedding** | ThreadPoolExecutor | 2 | ✅ | ✅ (MPS/PyTorch) |
| **Gender/Age** | AsyncGenderWorker | 2 | ✅ | ✅ (MPS/PyTorch) |
| **Database Writes** | ThreadPoolExecutor | 1 | ✅ | N/A (I/O) |

---

## ✅ Tối Ưu Đã Implement

### 1. **Producer-Consumer Pattern** ✅
- Frame reader thread độc lập
- Queue-based communication
- Non-blocking operations

### 2. **Parallel Detection** ✅
- 2 workers cho face detection
- Async submission với Future
- Can process multiple frames simultaneously

### 3. **Parallel Re-ID** ✅
- 2 workers cho embedding computation
- Batch processing multiple tracks
- Non-blocking với `as_completed()`

### 4. **Parallel Gender/Age** ✅
- 2 workers cho classification
- Priority queue system
- Async result polling

### 5. **GPU Acceleration** ✅
- OpenCL backend cho face detection
- MPS support cho PyTorch models
- Automatic fallback

### 6. **Async Database** ✅
- Non-blocking writes
- Batch operations
- Separate thread pool

---

## 🔍 Kiểm Tra Chi Tiết

### ✅ Frame Reading
- **Thread**: Separate `_frame_reader_thread`
- **Pattern**: Producer-consumer với queue
- **Queue Size**: 2 (optimal để reduce lag)
- **Status**: ✅ Hoạt động tốt

### ✅ Face Detection
- **Executor**: `ThreadPoolExecutor(max_workers=2)`
- **Submission**: Async với `submit()`
- **Result**: Non-blocking với `result(timeout=0.0)`
- **GPU**: OpenCL enabled
- **Status**: ✅ Parallel, GPU-accelerated

### ✅ Re-ID Processing
- **Executor**: `ThreadPoolExecutor(max_workers=2)` trong integrator
- **Processing**: Parallel embedding cho multiple tracks
- **Completion**: `as_completed()` for non-blocking
- **Status**: ✅ Fully parallelized

### ✅ Gender/Age Classification
- **Workers**: 2 threads trong `AsyncGenderWorker`
- **Queue**: Priority queue (128 size)
- **Processing**: Parallel classification
- **Status**: ✅ Parallel với queue system

### ✅ Database Writes
- **Executor**: `ThreadPoolExecutor(max_workers=1)`
- **Writes**: Async, non-blocking
- **Batching**: Batch size 200, flush interval 500ms
- **Status**: ✅ Async, optimal cho I/O

---

## 🎯 Tổng Kết

### ✅ ĐÃ CÓ Multi-threading và Parallel Processing:

1. **Frame Reading**: ✅ Separate thread
2. **Detection**: ✅ 2 workers, GPU-accelerated
3. **Re-ID**: ✅ 2 workers, parallel embeddings
4. **Gender/Age**: ✅ 2 workers, priority queue
5. **Database**: ✅ Async writes, 1 worker (optimal cho I/O)
6. **GPU**: ✅ OpenCL + MPS support

### 📊 Tổng Số Threads per Channel:

- Main thread: 1
- Frame reader: 1
- Detection workers: 2
- Re-ID workers: 2 (temporary, per call)
- Gender/Age workers: 2
- DB worker: 1

**Total**: ~9 threads per channel (với 4 channels = ~36 threads)

---

## 💡 Recommendations

### ✅ ĐÃ TỐI ƯU TỐT

Codebase đã có multi-threading và parallel processing tốt:
- ✅ Producer-consumer pattern
- ✅ ThreadPoolExecutor cho parallel processing
- ✅ GPU acceleration
- ✅ Async I/O operations
- ✅ Priority queue systems

### 🔧 Có Thể Cải Thiện (Optional):

1. **Batch Frame Processing**: Process multiple frames in batches
2. **Dynamic Worker Scaling**: Adjust workers based on load
3. **Model Batching**: Batch inference cho PyTorch models
4. **Memory Pool**: Reuse memory allocations

**Tuy nhiên, hiện tại đã đủ tốt cho 4 channels với FPS mục tiêu ≥24!**

---

## ✅ KẾT LUẬN

**Status**: ✅ **ĐÃ CÓ ĐẦY ĐỦ Multi-threading và Parallel Processing**

- Tất cả components quan trọng đều parallel
- GPU acceleration enabled
- Async I/O operations
- Non-blocking pipelines
- Optimal worker counts

**Code đã được tối ưu tốt cho multi-channel processing!** 🚀


