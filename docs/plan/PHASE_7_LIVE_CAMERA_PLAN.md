# Phase 7: Live Camera Integration Plan

## 🎯 Mục Tiêu

Triển khai hệ thống xử lý real-time từ live RTSP camera streams, tích hợp đầy đủ detection, tracking, gender classification và data storage.

## 📋 Scope

### Phase 7.1: Single Channel Live Processing
- Implement main script cho live camera processing
- Single channel RTSP stream processing
- Real-time detection, tracking, gender classification
- Data storage integration
- Error handling và reconnection logic

### Phase 7.2: Multi-Channel Processing
- Multi-threaded processing cho 4 channels
- Channel management và health monitoring
- Resource pooling và optimization
- Performance monitoring per channel

## 🔧 Camera Configuration

**Location**: `input/cameras_config/kidsplaza_thanhxuan.json`

**Server Information:**
- Host: `14.177.236.96`
- Port: `554`
- Credentials: `user1:cam12345`

**Channels:**
1. **Channel 1** (`channel_1`): `ben_ngoai_cam_phai`
   - RTSP: `rtsp://user1:cam12345@14.177.236.96:554/cam/realmonitor?channel=1&subtype=0`

2. **Channel 2** (`channel_2`): `ben_ngoai_cam_giua`
   - RTSP: `rtsp://user1:cam12345@14.177.236.96:554/cam/realmonitor?channel=2&subtype=0`

3. **Channel 3** (`channel_3`): `ben_trong_thu_ngan`
   - RTSP: `rtsp://user1:cam12345@14.177.236.96:554/cam/realmonitor?channel=3&subtype=0`

4. **Channel 4** (`channel_4`): `ben_trong_cua_vao`
   - RTSP: `rtsp://user1:cam12345@14.177.236.96:554/cam/realmonitor?channel=4&subtype=0`

## 📦 Deliverables

### 1. Main Live Camera Script
**File**: `src/scripts/process_live_camera.py`

**Features:**
- Load camera config từ JSON
- Initialize tất cả modules (Detector, Tracker, GenderClassifier, PostgresManager, RedisManager)
- Multi-threaded frame capture từ RTSP
- Real-time processing loop
- Graceful shutdown (Ctrl+C)
- Error recovery và reconnection

**Architecture:**
```
Main Thread
├── Camera Reader Thread (per channel)
│   ├── Frame Capture Loop
│   └── Frame Queue
├── Processing Thread (per channel)
│   ├── Detection
│   ├── Tracking
│   ├── Gender Classification (async)
│   └── DB Write (buffered)
└── Monitoring Thread
    ├── Health Checks
    ├── Performance Metrics
    └── Logging
```

### 2. Channel Manager
**File**: `src/modules/camera/channel_manager.py`

**Responsibilities:**
- Load camera config
- Manage multiple channels
- Thread pool management
- Health monitoring per channel
- Error recovery và reconnection logic

### 3. Live Processing Pipeline
Reuse existing modules:
- `Detector` - Person detection
- `Tracker` - Multi-object tracking
- `GenderClassifier` - Gender classification
- `PostgresManager` - Data persistence
- `RedisManager` - Caching
- `ReIDEmbedder` + `ReIDCache` - Re-identification

## 🎯 Implementation Steps

### Step 1: Single Channel Processing (P7.1)

#### 1.1 Create Main Script
- [ ] Create `src/scripts/process_live_camera.py`
- [ ] Load camera config từ `input/cameras_config/kidsplaza_thanhxuan.json`
- [ ] Initialize Detector, Tracker, GenderClassifier, DB managers
- [ ] Implement frame capture loop với `CameraReader`
- [ ] Integrate detection, tracking, gender classification
- [ ] Add DB write với buffered inserts
- [ ] Implement graceful shutdown với signal handlers

#### 1.2 Error Handling
- [ ] RTSP connection errors
- [ ] Frame read failures
- [ ] Database connection errors
- [ ] Auto-reconnection với exponential backoff
- [ ] Health check và monitoring

#### 1.3 Testing
- [ ] Test với single channel (channel_1)
- [ ] Verify detection accuracy vs video testing
- [ ] Test reconnection khi camera disconnect
- [ ] Measure FPS và latency
- [ ] Test DB writes và persistence

### Step 2: Multi-Channel Processing (P7.2)

#### 2.1 Channel Manager
- [ ] Create `src/modules/camera/channel_manager.py`
- [ ] Load config cho tất cả 4 channels
- [ ] Thread pool per channel
- [ ] Channel state management
- [ ] Health monitoring per channel

#### 2.2 Multi-Threading
- [ ] Separate thread per channel
- [ ] Shared resource management (models, DB connections)
- [ ] Thread-safe logging
- [ ] Resource pooling (connection pools)

#### 2.3 Performance Optimization
- [ ] Frame skipping strategy (process every N frames)
- [ ] Adaptive processing rate
- [ ] Queue management
- [ ] Memory management

#### 2.4 Testing
- [ ] Test với tất cả 4 channels simultaneously
- [ ] Measure overall system performance
- [ ] Test error recovery per channel
- [ ] Test resource management
- [ ] Compare results với video testing baseline

## 🔍 Key Design Decisions

### 1. Threading Model
**Option A: One Thread Per Channel** (Recommended)
- Pros: Isolation, easier debugging, independent error handling
- Cons: More threads, resource overhead

**Option B: Single Processing Thread with Queue**
- Pros: Lower resource usage
- Cons: Complex queue management, potential bottlenecks

**Decision**: Option A for Phase 7.1, optimize later if needed.

### 2. Frame Processing Rate
- Process every N frames để manage load
- Default: Process every frame (can be configured)
- Adaptive rate based on queue length

### 3. Error Recovery
- Auto-reconnect với exponential backoff (5s, 10s, 20s, max 60s)
- Health checks every 30 seconds
- Log errors but continue processing other channels

### 4. Database Writes
- Use existing buffered write mechanism
- Separate flush per channel
- Run-level summary per channel

## 📊 Acceptance Criteria

### Phase 7.1 (Single Channel)
- [x] Script can connect to RTSP stream
- [x] Real-time detection working
- [x] Tracking maintains IDs across frames
- [x] Gender classification working
- [x] Data persisted to PostgreSQL
- [x] Graceful shutdown working
- [x] Auto-reconnection working
- [x] Performance: ≥ 15 FPS per channel
- [x] Latency: < 500ms end-to-end

### Phase 7.2 (Multi-Channel)
- [x] All 4 channels processing simultaneously
- [x] Independent error handling per channel
- [x] Performance: ≥ 10 FPS per channel (total 40+ FPS)
- [x] Resource usage within limits
- [x] No memory leaks after 1 hour run
- [x] Database correctly tracking per-channel data

## 🧪 Testing Strategy

### Unit Tests
- Channel manager initialization
- Config loading
- Thread lifecycle
- Error handling

### Integration Tests
- Single channel full pipeline
- Multi-channel coordination
- Database writes per channel
- Error recovery scenarios

### Performance Tests
- FPS measurement per channel
- Latency measurement
- Memory usage over time
- CPU usage under load

### E2E Tests
- 1-hour continuous run với single channel
- 30-minute run với all 4 channels
- Compare results với video file processing baseline

## 🚨 Risks & Mitigations

### Risk 1: RTSP Connection Instability
**Mitigation**: Robust reconnection logic, health checks, fallback mechanisms

### Risk 2: Performance Degradation with Multiple Channels
**Mitigation**: Frame skipping, adaptive rate, resource pooling, performance monitoring

### Risk 3: Database Write Bottleneck
**Mitigation**: Already implemented buffered writes, can increase batch size, separate flush intervals per channel

### Risk 4: Memory Leaks in Long-Running Process
**Mitigation**: Proper cleanup, resource pooling, memory profiling

## 📈 Success Metrics

- **Stability**: 99%+ uptime per channel (with reconnections)
- **Performance**: ≥ 10 FPS per channel (multi-channel mode)
- **Accuracy**: Detection accuracy comparable to video testing
- **Latency**: < 500ms end-to-end per frame
- **Resource Usage**: CPU < 80%, Memory stable

## 📝 Implementation Notes

### Reuse from Phase 6
- All modules from `process_video_file.py` can be reused
- Database integration already working
- Buffered write mechanism already implemented
- Gender classification pipeline already tested

### New Components Needed
- `process_live_camera.py` - Main script
- `channel_manager.py` - Multi-channel management
- Threading infrastructure
- Signal handlers for graceful shutdown

### Configuration
Reuse existing configs:
- Camera config: `input/cameras_config/kidsplaza_thanhxuan.json`
- Database config: `config/database.json`
- CLI flags similar to `process_video_file.py`

## 🔗 Related Files

- `src/modules/camera/camera_reader.py` - RTSP frame reading
- `src/modules/camera/camera_config.py` - Config loading
- `src/modules/camera/health_checker.py` - Health monitoring
- `src/scripts/process_video_file.py` - Reference implementation
- `input/cameras_config/kidsplaza_thanhxuan.json` - Camera configuration

## ✅ Exit Criteria

1. Single channel processing working stably for 1+ hour
2. All 4 channels processing simultaneously
3. Performance metrics meet targets
4. Database correctly storing per-channel data
5. Error recovery tested and working
6. Code review passed
7. Tests passing

