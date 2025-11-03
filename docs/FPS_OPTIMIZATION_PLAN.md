# FPS Optimization Plan - Multi-threading & Parallel Processing

## Current Status
- **Current FPS**: 13.08
- **Target FPS**: ≥24
- **Gap**: Need to increase ~84%

## Bottleneck Analysis

### Current Processing Pipeline (Synchronous)
```
Frame Read → Face Detection → Filtering → Tracking → Re-ID → Display → DB Write
     ↓            ↓              ↓          ↓         ↓        ↓         ↓
   ~5ms        ~30ms          ~2ms       ~5ms     ~20ms    ~3ms     ~10ms
Total: ~75ms per frame = ~13 FPS
```

### Identified Bottlenecks
1. **Face Detection** (~30ms): Largest bottleneck - CPU-bound
2. **Re-ID Processing** (~20ms): Embedding generation and matching
3. **Database Writes** (~10ms): I/O bound, blocking
4. **Tracking** (~5ms): Can be optimized with frame skipping

## Parallelization Strategy

### Strategy 1: Producer-Consumer Pattern ⭐ RECOMMENDED
**Architecture**:
```
Main Thread (Frame Reader)
    ↓
Queue 1: Raw Frames
    ↓
Worker Thread 1: Face Detection
    ↓
Queue 2: Detections
    ↓
Worker Thread 2: Tracking + Re-ID (if needed)
    ↓
Queue 3: Tracked Results
    ↓
Main Thread: Display + DB Write (async)
```

**Benefits**:
- Face detection can run in parallel with frame reading
- Overlapping processing time
- Expected speedup: 2-3x (13 → 25-30 FPS)

### Strategy 2: Pipeline Parallelism
**Stages**:
1. **Stage 1**: Frame Read + Resize (preprocessing)
2. **Stage 2**: Face Detection (parallel batches)
3. **Stage 3**: Tracking + Re-ID
4. **Stage 4**: Display + DB

**Benefits**:
- Process multiple frames simultaneously
- Better CPU utilization
- Expected speedup: 1.5-2x

### Strategy 3: Async I/O for Database
**Implementation**:
- Use async database writes
- Batch multiple writes together
- Non-blocking I/O operations

**Benefits**:
- Remove blocking I/O overhead (~10ms saved)
- Expected speedup: 1.2-1.3x

## Implementation Plan

### Phase 1: Frame Reading + Detection Parallelization (Priority 1)
**Goal**: Overlap frame reading with face detection

```python
import queue
import threading
from concurrent.futures import ThreadPoolExecutor

class LiveCameraProcessor:
    def __init__(self):
        # Detection thread pool
        self.detection_executor = ThreadPoolExecutor(max_workers=2)
        self.frame_queue = queue.Queue(maxsize=3)  # Buffer 3 frames
        self.detection_queue = queue.Queue(maxsize=2)
        
    def _frame_reader_thread(self):
        """Continuously read frames and put in queue"""
        while not self._shutdown_requested:
            frame = camera_reader.read_frame()
            if frame is not None:
                try:
                    self.frame_queue.put(frame, timeout=0.1)
                except queue.Full:
                    # Drop oldest frame if queue full
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put(frame, timeout=0.1)
                    except queue.Empty:
                        pass
```

**Expected Speedup**: 2x (detection runs while reading next frame)

### Phase 2: Async Database Writes (Priority 2)
**Implementation**:
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncDBWriter:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.write_executor = ThreadPoolExecutor(max_workers=1)
        self.write_queue = queue.Queue()
        
    def write_async(self, detections):
        """Non-blocking write"""
        self.write_executor.submit(
            self.db_manager.insert_detections, detections
        )
```

**Expected Speedup**: 1.2x (remove 10ms blocking)

### Phase 3: Batch Face Detection (Priority 3)
**If multiple faces per frame are common**:
- Process multiple detections in parallel
- Use batch inference if model supports

**Expected Speedup**: 1.3x (if applicable)

## Combined Expected Results

### Conservative Estimate:
- Phase 1 (Parallel Detection): 2x → **26 FPS** ✅ (meets target)
- Phase 2 (Async DB): 1.2x → **31 FPS**
- Phase 3 (Batch): 1.1x → **34 FPS**

### Realistic Target:
- **Minimum**: 24 FPS (target met)
- **Expected**: 28-30 FPS
- **Optimal**: 32-35 FPS

## Implementation Details

### Thread Safety Considerations
1. **Frame Queue**: Thread-safe (queue.Queue)
2. **Detection Results**: Synchronized access with locks
3. **Tracker State**: Must be single-threaded (use main thread)
4. **Display**: Must be main thread (OpenCV requirement)

### Resource Management
- Limit thread pool sizes to avoid CPU oversubscription
- Use bounded queues to prevent memory issues
- Graceful shutdown of all threads

### Trade-offs
- **Latency**: Slightly increased due to buffering (1-2 frames)
- **Memory**: Slightly higher due to frame queue buffers
- **Complexity**: More complex code, harder to debug

## Testing Plan
1. Baseline: Current single-threaded (13 FPS)
2. Test Phase 1: Parallel detection (expected ~26 FPS)
3. Test Phase 2: Add async DB (expected ~31 FPS)
4. Test Phase 3: Add batch processing (expected ~34 FPS)
5. Verify accuracy maintained (no false positives)
6. Verify tracking continuity (no dropped tracks)

---

*Generated: 2025-11-02*
*For: Phase 7 Live Camera Integration - FPS Optimization*



