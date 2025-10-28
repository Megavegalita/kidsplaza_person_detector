# Development Plan: Person Detection System

## 📋 Tổng Quan

Kế hoạch phát triển chi tiết cho hệ thống phát hiện người tại Kidsplaza Thanh Xuan, sử dụng AI/ML trên nền tảng Mac M4 Pro với Metal Performance Shaders (MPS).

---

## 1. Requirements Definition

### 1.1 Mục Tiêu Dự Án

Phát triển hệ thống phát hiện và phân tích người từ camera RTSP với các chức năng:
- Phát hiện người trong video stream real-time
- Theo dõi đối tượng qua nhiều frame
- Ước tính tuổi và giới tính
- Lưu trữ và phân tích dữ liệu

### 1.2 User Stories

#### US-001: Setup Development Environment
**As a** developer  
**I want to** setup local development environment on Mac M4 Pro  
**So that** I can develop and test the person detection system

**Acceptance Criteria:**
- [ ] Python virtual environment created
- [ ] All dependencies installed (PyTorch with MPS support, OpenCV, Ultralytics)
- [ ] Environment configured with Metal backend
- [ ] Can verify GPU acceleration is working

#### US-002: Camera Configuration Management
**As a** system administrator  
**I want to** manage camera configurations  
**So that** the system can connect to multiple RTSP streams

**Acceptance Criteria:**
- [ ] Camera config loaded from JSON files
- [ ] Support multiple channels per camera server
- [ ] RTSP URL construction and validation
- [ ] Health check for all channels

#### US-003: Real-time Person Detection
**As a** system  
**I want to** detect people in video streams  
**So that** I can track and analyze visitor behavior

**Acceptance Criteria:**
- [ ] Load YOLOv8n model optimized for MPS
- [ ] Process video frames in real-time
- [ ] Detect persons with confidence threshold
- [ ] Draw bounding boxes and labels on frame
- [ ] Performance: target 5+ FPS initially, optimize to 10+ FPS (Mac M4 Pro)

#### US-004: Multi-Object Tracking
**As a** system  
**I want to** track detected persons across frames  
**So that** I can analyze movement patterns

**Acceptance Criteria:**
- [ ] Implement ByteTrack algorithm
- [ ] Assign unique IDs to detected persons
- [ ] Maintain tracking across multiple frames
- [ ] Handle occlusions and re-identifications
- [ ] Track data stored for analysis

#### US-005: Age and Gender Estimation
**As a** system  
**I want to** estimate age and gender of detected persons  
**So that** I can gather demographic insights

**Acceptance Criteria:**
- [ ] Load age/gender estimation model
- [ ] Extract face region from detected person
- [ ] Estimate age and gender with confidence scores
- [ ] Convert and optimize model to Core ML format
- [ ] Accuracy > 80% for age estimation

#### US-006: Data Storage and Retrieval
**As a** system  
**I want to** store detection results in database  
**So that** I can analyze historical data

**Acceptance Criteria:**
- [ ] PostgreSQL connection management
- [ ] Create tables for detections, tracks, demographics
- [ ] Insert detection data with timestamps
- [ ] Query historical data
- [ ] Redis caching for recent detections

#### US-007: Model Optimization
**As a** developer  
**I want to** optimize models for Core ML  
**So that** I can achieve better inference performance

**Acceptance Criteria:**
- [ ] Convert PyTorch models to Core ML format
- [ ] Apply FP16 quantization
- [ ] Integrate NMS into Core ML pipeline
- [ ] Benchmark inference speed
- [ ] Model size reduction >50%

### 1.3 Technical Requirements

#### Environment
- macOS with Apple Silicon (M4 Pro)
- Python 3.8+ (currently using Python 3.11)
- Metal Performance Shaders support

#### Dependencies
- PyTorch (nightly/pre-release for latest MPS)
- OpenCV (opencv-python)
- Ultralytics (YOLOv8 - focusing on YOLOv8n for MPS compatibility)
- ByteTrack (object tracking)
- coremltools (model conversion)
- PostgreSQL (psycopg2)
- Redis (redis)

#### Models
- Person Detection: **YOLOv8n** (nano - smallest, fastest, best MPS support)
- Object Tracking: ByteTrack (with SORT fallback)
- Age/Gender Estimation: TBD (to be researched early)

---

## 2. Architecture Planning

### 2.1 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Camera RTSP Streams                       │
│               (4 channels from Kidsplaza)                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Video Capture Module                       │
│                  (OpenCV VideoCapture)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Person Detection Module                         │
│           (YOLOv9 on MPS Backend)                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Object Tracking Module                          │
│                    (ByteTrack)                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│          Age & Gender Estimation Module                      │
│              (CNN-based models)                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               Data Storage Module                            │
│          (PostgreSQL + Redis Cache)                         │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow

1. **Video Input**: RTSP streams from 4 camera channels
2. **Frame Capture**: OpenCV captures frames from each stream
3. **Detection**: YOLO detects persons in each frame
4. **Tracking**: ByteTrack assigns IDs and tracks across frames
5. **Demographics**: Age/gender estimation for tracked persons
6. **Storage**: Results saved to PostgreSQL with Redis caching
7. **Analytics**: Historical data for reporting and analysis

### 2.3 Data Models

#### PersonDetection
```python
@dataclass
class PersonDetection:
    """Person detection result."""
    timestamp: datetime
    camera_id: int
    channel_id: int
    detection_id: str
    track_id: int
    confidence: float
    bbox: Tuple[int, int, int, int]  # (x, y, width, height)
    age: Optional[int]
    age_confidence: Optional[float]
    gender: Optional[str]
    gender_confidence: Optional[float]
    frame_number: int
```

#### PersonTrack
```python
@dataclass
class PersonTrack:
    """Person track information."""
    track_id: int
    camera_id: int
    start_time: datetime
    end_time: Optional[datetime]
    detection_count: int
    avg_confidence: float
    trajectory: List[Tuple[float, float]]  # Path coordinates
```

### 2.4 API Design

#### Database Schema

```sql
-- Detections table
CREATE TABLE detections (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    camera_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    detection_id VARCHAR(50) NOT NULL,
    track_id INTEGER,
    confidence FLOAT NOT NULL,
    bbox_x INTEGER NOT NULL,
    bbox_y INTEGER NOT NULL,
    bbox_width INTEGER NOT NULL,
    bbox_height INTEGER NOT NULL,
    age INTEGER,
    age_confidence FLOAT,
    gender VARCHAR(10),
    gender_confidence FLOAT,
    frame_number INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tracks table
CREATE TABLE tracks (
    id SERIAL PRIMARY KEY,
    track_id INTEGER NOT NULL,
    camera_id INTEGER NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    detection_count INTEGER NOT NULL,
    avg_confidence FLOAT NOT NULL,
    trajectory JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_detections_timestamp ON detections(timestamp);
CREATE INDEX idx_detections_track_id ON detections(track_id);
CREATE INDEX idx_tracks_camera_id ON tracks(camera_id);
```

### 2.5 Module Structure

```
src/
├── modules/
│   ├── __init__.py
│   ├── camera/
│   │   ├── __init__.py
│   │   ├── camera_reader.py      # RTSP capture
│   │   ├── camera_config.py      # Config management
│   │   └── health_checker.py     # Health verification
│   ├── detection/
│   │   ├── __init__.py
│   │   ├── detector.py           # YOLO detection
│   │   ├── model_loader.py       # Model loading
│   │   └── image_processor.py    # Frame preprocessing
│   ├── tracking/
│   │   ├── __init__.py
│   │   ├── tracker.py            # ByteTrack implementation
│   │   └── track_manager.py      # Track management
│   ├── demographics/
│   │   ├── __init__.py
│   │   ├── age_estimator.py      # Age estimation
│   │   ├── gender_estimator.py   # Gender estimation
│   │   └── face_extractor.py     # Face region extraction
│   ├── database/
│   │   ├── __init__.py
│   │   ├── postgres_manager.py   # PostgreSQL operations
│   │   ├── redis_manager.py      # Redis cache
│   │   └── models.py             # Data models
│   └── utils/
│       ├── __init__.py
│       ├── logger.py             # Logging setup
│       └── validators.py         # Input validation
└── scripts/
    ├── __init__.py
    ├── process_video_file.py     # Offline video processing and testing
    ├── main_detector.py          # Main detection loop (live camera)
    ├── export_model.py          # Model export to Core ML
    ├── verify_camera_health.py   # Existing
    └── verify_database_health.py # Existing
```

---

## 3. Implementation Plan

### Phase 1: Environment Setup (Week 1)

#### 1.1 Setup Development Environment
- [ ] Verify Python 3.11 installation
- [ ] Create virtual environment
- [ ] Install PyTorch with MPS support
- [ ] Install OpenCV, Ultralytics, ByteTrack
- [ ] Install database libraries (psycopg2, redis)
- [ ] Verify Metal GPU acceleration
- [ ] Test basic YOLO model loading

#### 1.2 Project Structure Setup
- [ ] Create module directories
- [ ] Setup `__init__.py` files
- [ ] Initialize git submodules if needed
- [ ] Configure logging infrastructure
- [ ] Setup configuration management

#### 1.3 Database Setup
- [ ] Create PostgreSQL database
- [ ] Design and create tables
- [ ] Setup indexes
- [ ] Configure Redis cache
- [ ] Test database connections

### Phase 1.5: Model Research and Early Testing (Week 1-2)

#### 1.5.1 Research Demographics Models
- [ ] Research available age/gender estimation models
- [ ] Test models on sample data
- [ ] Evaluate accuracy and performance
- [ ] Download and validate chosen models
- [ ] Document model choices and rationale

#### 1.5.2 Benchmark YOLOv8n Performance
- [ ] Load YOLOv8n model
- [ ] Test with sample images
- [ ] Measure inference speed on CPU
- [ ] Test MPS acceleration if available
- [ ] Document baseline performance
- [ ] Set realistic performance targets

### Phase 2: Camera Integration (Week 1-3)

#### 2.1 Camera Module
- [ ] Implement `camera_reader.py`
  - [ ] RTSP URL parsing
  - [ ] VideoCapture wrapper
  - [ ] Frame reading and validation
  - [ ] Error handling and retry logic
- [ ] Implement `camera_config.py`
  - [ ] Load JSON configuration
  - [ ] Validate config format
  - [ ] RTSP URL construction
- [ ] Implement `health_checker.py`
  - [ ] Connection testing
  - [ ] Resolution validation
  - [ ] Health status reporting

#### 2.2 Testing
- [ ] Unit tests for camera module
- [ ] Integration test with real RTSP stream
- [ ] Test with all 4 channels
- [ ] Performance benchmarking

### Phase 3: Person Detection (Week 3-5)

#### 3.1 Detection Module
- [ ] Implement `model_loader.py`
  - [ ] Load YOLOv8n model (start with v8n for best MPS support)
  - [ ] Configure for MPS device with CPU fallback
  - [ ] Handle model not found errors
  - [ ] Benchmark MPS vs CPU performance
- [ ] Implement `detector.py`
  - [ ] Frame preprocessing (resize, normalize)
  - [ ] Run inference on MPS
  - [ ] Parse YOLO output
  - [ ] Filter detections by confidence
  - [ ] Format bounding boxes
- [ ] Implement `image_processor.py`
  - [ ] Frame resizing logic
  - [ ] Normalization
  - [ ] Data type conversions

#### 3.2 Testing
- [ ] Test with sample images
- [ ] Test with video frames
- [ ] Measure inference speed
- [ ] Validate detection accuracy
- [ ] Test MPS GPU utilization

### Phase 4: Object Tracking (Week 5-7)

#### 4.1 Tracking Module
- [ ] Install ByteTrack dependencies
- [ ] Implement `tracker.py`
  - [ ] Initialize ByteTrack
  - [ ] Update tracks with detections
  - [ ] Handle track associations
  - [ ] Manage track lifecycle
- [ ] Implement `track_manager.py`
  - [ ] Track state management
  - [ ] Track ID assignment
  - [ ] Track data storage

#### 4.2 Testing
- [ ] Test tracking on sample video
- [ ] Test track persistence
- [ ] Test with multiple persons
- [ ] Test occlusion handling
- [ ] Measure tracking performance

### Phase 5: Demographics Estimation (Week 8-10)

#### 5.1 Demographics Module
- [ ] Research and select age/gender models
- [ ] Implement `face_extractor.py`
  - [ ] Extract face region from person bbox
  - [ ] Face alignment and preprocessing
- [ ] Implement `age_estimator.py`
  - [ ] Load age estimation model
  - [ ] Run age prediction
  - [ ] Return confidence scores
- [ ] Implement `gender_estimator.py`
  - [ ] Load gender estimation model
  - [ ] Run gender prediction
  - [ ] Return confidence scores

#### 5.2 Model Conversion
- [ ] Convert models to Core ML format
- [ ] Apply FP16 quantization
- [ ] Test Core ML inference
- [ ] Benchmark performance improvements

#### 5.3 Testing
- [ ] Test age/gender estimation accuracy
- [ ] Test with diverse demographics
- [ ] Validate confidence scores
- [ ] Test inference performance

### Phase 6: Data Storage (Week 10-11)

#### 6.1 Database Module
- [ ] Implement `models.py`
  - [ ] Define Pydantic/dataclass models
  - [ ] Data validation
- [ ] Implement `postgres_manager.py`
  - [ ] Connection pooling
  - [ ] Batch insert operations
  - [ ] Query methods
  - [ ] Error handling and retries
- [ ] Implement `redis_manager.py`
  - [ ] Cache recent detections
  - [ ] Cache tracking data
  - [ ] Cache invalidation strategy

#### 6.2 Testing
- [ ] Test database insertion performance
- [ ] Test query performance
- [ ] Test Redis caching
- [ ] Test with concurrent writes
- [ ] Validate data integrity

### Phase 3.5: Offline Video Testing (Week 5)

#### 3.5.1 Offline Testing Infrastructure
- [ ] Implement `video_file_processor.py` script
  - [ ] Read video files from `input/video/` directory
  - [ ] Process video with detection pipeline
  - [ ] Save annotated output videos
  - [ ] Generate detection reports
- [ ] Create test video dataset
  - [ ] Use existing video: `Binh Xa-Thach That_ch4_20251024102450_20251024112450.mp4`
  - [ ] Extract sample clips with persons
  - [ ] Prepare diverse scenarios (multiple persons, occlusions)
- [ ] Implement video output writer
  - [ ] Draw bounding boxes and labels
  - [ ] Add tracking IDs to frames
  - [ ] Add demographics annotations
  - [ ] Output to `output/videos/` directory

#### 3.5.2 Testing Workflow
- [ ] Test detection on video file
- [ ] Test tracking consistency across frames
- [ ] Test demographics estimation
- [ ] Validate accuracy metrics
- [ ] Performance benchmarking on video
- [ ] Generate test reports and visualizations
- [ ] Fix any issues before proceeding to live camera

### Phase 4: Object Tracking - Video Testing (Week 6-8)

#### 4.1 Tracking Module
- [ ] Install ByteTrack dependencies
- [ ] Implement `tracker.py`
  - [ ] Initialize ByteTrack
  - [ ] Update tracks with detections
  - [ ] Handle track associations
  - [ ] Manage track lifecycle
- [ ] Implement `track_manager.py`
  - [ ] Track state management
  - [ ] Track ID assignment
  - [ ] Track data storage

#### 4.2 Testing on Video Files
- [ ] Test tracking on sample video
- [ ] Test track persistence
- [ ] Test with multiple persons
- [ ] Test occlusion handling
- [ ] Measure tracking performance
- [ ] Generate tracking visualizations

### Phase 5: Demographics Estimation - Video Testing (Week 9-11)

#### 5.1 Demographics Module
- [ ] Research and select age/gender models
- [ ] Implement `face_extractor.py`
  - [ ] Extract face region from person bbox
  - [ ] Face alignment and preprocessing
- [ ] Implement `age_estimator.py`
  - [ ] Load age estimation model
  - [ ] Run age prediction
  - [ ] Return confidence scores
- [ ] Implement `gender_estimator.py`
  - [ ] Load gender estimation model
  - [ ] Run gender prediction
  - [ ] Return confidence scores

#### 5.2 Model Conversion
- [ ] Convert models to Core ML format
- [ ] Apply FP16 quantization
- [ ] Test Core ML inference
- [ ] Benchmark performance improvements

#### 5.3 Testing on Video Files
- [ ] Test age/gender estimation accuracy on video
- [ ] Test with diverse demographics in video
- [ ] Validate confidence scores
- [ ] Test inference performance
- [ ] Generate annotated output with demographics

### Phase 6: Data Storage - Video Testing (Week 11-12)

#### 6.1 Database Module
- [ ] Implement `models.py`
  - [ ] Define Pydantic/dataclass models
  - [ ] Data validation
- [ ] Implement `postgres_manager.py`
  - [ ] Connection pooling
  - [ ] Batch insert operations
  - [ ] Query methods
  - [ ] Error handling and retries
- [ ] Implement `redis_manager.py`
  - [ ] Cache recent detections
  - [ ] Cache tracking data
  - [ ] Cache invalidation strategy

#### 6.2 Testing with Video Data
- [ ] Test database insertion performance with video processing
- [ ] Test query performance
- [ ] Test Redis caching
- [ ] Test with concurrent operations
- [ ] Validate data integrity from video

### Phase 7: Live Camera Integration (Week 12-14)

#### 7.1 Main Detector Script for Live Streams
- [ ] Implement `main_detector.py`
  - [ ] Initialize all modules
  - [ ] Multi-threaded frame capture from RTSP
  - [ ] Detection loop
  - [ ] Tracking updates
  - [ ] Demographics estimation
  - [ ] Data storage
  - [ ] Graceful shutdown
- [ ] Add configuration management
- [ ] Add logging and monitoring
- [ ] Add performance metrics

#### 7.2 Integration Testing with Live Camera
- [ ] Test with single camera channel first
- [ ] Verify detection accuracy vs video testing
- [ ] Test all 4 channels simultaneously
- [ ] Measure overall system performance
- [ ] Test error recovery (connection drops)
- [ ] Test resource management
- [ ] Compare results with offline video testing

### Phase 8: Model Optimization (Week 14-15)

#### 8.1 Model Export
- [ ] Implement `export_model.py`
  - [ ] Export YOLO to Core ML
  - [ ] Apply optimizations (FP16, NMS)
  - [ ] Export age/gender models
- [ ] Benchmark before/after optimization
- [ ] Validate output accuracy

#### 8.2 Performance Tuning
- [ ] Profile code for bottlenecks
- [ ] Optimize frame processing pipeline
- [ ] Optimize database operations
- [ ] Tune threading/async operations

### Phase 9: Testing & Documentation (Week 15-16)

#### 9.1 Comprehensive Testing
- [ ] Unit tests for all modules
- [ ] Integration tests
- [ ] E2E tests
- [ ] Load tests
- [ ] Error handling tests
- [ ] Coverage report (target >80%)

#### 9.2 Documentation
- [ ] Update README with usage
- [ ] API documentation
- [ ] Architecture diagrams
- [ ] Deployment guide
- [ ] Troubleshooting guide

---

## 4. Testing Strategy

### 4.1 Testing Workflow Overview

**Testing Approach: Offline First, Then Live**
1. **Phase 1-3**: Unit tests and basic integration
2. **Phase 3.5**: Offline video file testing (validation and benchmarking)
3. **Phase 4-6**: Continue testing on video files
4. **Phase 7**: Live camera integration (final testing)
5. **Phase 8-9**: Optimization and comprehensive testing

### 4.2 Unit Tests

**Location**: `tests/unit/`

- `test_camera_reader.py` - Camera reading functionality
- `test_detector.py` - Detection logic
- `test_tracker.py` - Tracking algorithms
- `test_demographics.py` - Age/gender estimation
- `test_database.py` - Database operations

### 4.3 Integration Tests - Video File Based

**Location**: `tests/integration/`

- `test_video_detection.py` - Detection on video files
- `test_video_tracking.py` - Tracking on video files
- `test_video_full_pipeline.py` - End-to-end pipeline on video
- `test_database_integration.py` - Database operations with video data
- `test_video_output.py` - Annotated video generation

### 4.4 Video File Testing

**Script**: `src/scripts/process_video_file.py`
**Test Data**: `input/video/Binh Xa-Thach That_ch4_20251024102450_20251024112450.mp4`
**Output**: `output/videos/`, `output/reports/`

**Test Cases**:
- [ ] Process video file end-to-end
- [ ] Generate annotated output video
- [ ] Validate detection accuracy metrics
- [ ] Test tracking consistency
- [ ] Test demographics estimation accuracy
- [ ] Generate performance report
- [ ] Compare results with ground truth (if available)

### 4.5 Live Camera Integration Tests

**Location**: `tests/e2e/`

- `test_live_camera_pipeline.py` - Full pipeline with live camera
- `test_multi_channel.py` - Multiple channels simultaneously
- `test_camera_error_recovery.py` - Handle connection drops
- `test_performance_comparison.py` - Compare live vs video results

### 4.6 Performance Tests

**Video File Testing**:
- Inference speed on video (target: >5 FPS, optimize to >10 FPS)
- Detection accuracy on video (target: >85%, stretch goal: >90%)
- Tracking consistency (target: >80%, stretch goal: >90%)
- Demographics accuracy (target: >70%, stretch goal: >80%)
- Memory usage monitoring during video processing
- CPU/GPU utilization tracking

**Live Camera Testing**:
- Real-time processing speed
- Latency measurement
- Resource usage comparison
- Concurrent channel handling

### 4.7 Testing Checklist (Before Live Integration)

- [ ] All unit tests pass (>80% coverage)
- [ ] Video file testing completed successfully
- [ ] Performance metrics meet targets
- [ ] Detection accuracy validated on video
- [ ] Tracking consistency verified
- [ ] Demographics estimation validated
- [ ] Database operations tested with video data
- [ ] Error handling tested on various scenarios
- [ ] Output videos generated and reviewed
- [ ] Test reports generated and analyzed

---

## 5. Configuration Management

### 5.1 Configuration Files

**`config/detection.json`**
```json
{
  "model": {
    "type": "yolov8n",
    "path": "models/yolov8n.pt",
    "confidence_threshold": 0.5,
    "device": "mps"
  },
  "tracking": {
    "track_thresh": 0.5,
    "high_thresh": 0.6,
    "match_thresh": 0.8,
    "frame_rate": 30
  },
  "demographics": {
    "age_model_path": "models/age_model.mlpackage",
    "gender_model_path": "models/gender_model.mlpackage",
    "min_face_size": 32
  },
  "processing": {
    "frame_skip": 1,
    "batch_size": 1,
    "workers": 2
  }
}
```

**`config/storage.json`**
```json
{
  "postgresql": {
    "host": "localhost",
    "port": 5432,
    "database": "gender_analysis",
    "pool_size": 10,
    "insert_batch_size": 100
  },
  "redis": {
    "host": "localhost",
    "port": 6379,
    "ttl": 3600,
    "cache_detections": true
  }
}
```

### 5.2 Environment Variables

```bash
# .env
CAMERA_CONFIG_PATH=input/cameras_config/
LOG_LEVEL=INFO
LOG_FILE=logs/detector.log
MAX_RETRIES=3
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
REDIS_URL=redis://localhost:6379
```

---

## 6. Risk Assessment

### 6.1 Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|------------|------------|
| MPS support issues | High | Medium | Test early, use fallback to CPU if needed |
| Model accuracy issues | High | Low | Use proven models (YOLOv8), fine-tune if needed |
| Performance bottlenecks | Medium | Medium | Profile early, optimize incrementally |
| RTSP connection issues | High | High | Implement robust retry logic, health checks |
| Database overload | Medium | Medium | Batch inserts, connection pooling, indexing |

### 6.2 Timeline Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Model conversion challenges | High | Allocate extra time, research Core ML docs |
| Integration complexity | Medium | Incremental integration, thorough testing |
| Dependency issues | Medium | Pin versions, test compatibility early |

---

## 7. Success Criteria

### 7.1 Functional Requirements
- ✅ Detect persons in real-time from 4 camera channels
- ✅ Track persons across frames with unique IDs
- ✅ Estimate age and gender (target: >70% accuracy for demographics)
- ✅ Store detection data in PostgreSQL
- ✅ Cache recent data in Redis
- ✅ Video file testing completed and validated

### 7.2 Performance Requirements
**Initial Targets** (Phase 3-7):
- Target: 5+ FPS per camera channel (initial)
- Optimize to: 10+ FPS per camera channel (final)
- Total latency < 200ms per frame (acceptable)
- Memory usage < 4GB
- Database insertion < 50ms (batch operations)

**Success Criteria**:
- ✅ Core functionality works (detection + tracking)
- ✅ Can process video files smoothly
- ✅ Can handle 4 camera channels (even if slower)
- ✅ Database operations functional

### 7.3 Quality Requirements
- ✅ Code coverage >80%
- ✅ All linter checks pass (Black, Flake8, Pylint)
- ✅ Type checking passes (MyPy) - no errors
- ✅ Documentation complete (docstrings, README)
- ✅ Error handling comprehensive
- ✅ Video file testing completed successfully
- ✅ All tests pass before live camera integration

---

## 8. Developer Checklist Compliance

### Code Quality Standards
- [ ] Follow PEP 8 style guide (max line length: 100 chars)
- [ ] Use type hints for all functions and return types
- [ ] Add Google-style docstrings to all public APIs
- [ ] No bare `except:` clauses - catch specific exceptions
- [ ] Implement proper error handling and logging
- [ ] Use context managers for resource cleanup

### Development Workflow
- [ ] Run `black src/` and `isort src/` before commit
- [ ] Run `flake8 src/` and `pylint src/` to check for issues
- [ ] Run `mypy src/` for type checking
- [ ] Write unit tests for each new module (>80% coverage)
- [ ] Run `pytest tests/` before committing
- [ ] Use pre-commit hooks

### Testing Requirements
- [ ] Write unit tests for all functions
- [ ] Write integration tests for video file processing
- [ ] Test error handling and edge cases
- [ ] Mock external dependencies
- [ ] Generate test reports and visualizations
- [ ] Validate accuracy metrics on video files before live testing

### Documentation Requirements
- [ ] Module docstrings (purpose and functionality)
- [ ] Class docstrings (responsibilities)
- [ ] Function docstrings (Args, Returns, Raises)
- [ ] Complex logic comments (explain WHY)
- [ ] Update README when adding features
- [ ] Document API changes

### Security & Best Practices
- [ ] No hardcoded secrets - use environment variables
- [ ] Input validation for all user inputs
- [ ] SQL injection prevention (parameterized queries)
- [ ] Path traversal prevention
- [ ] Validate file sizes and formats

## 9. Summary & Execution Flow

### Critical Success Path
```
Phase 1: Environment Setup (Week 1)
    ↓
Phase 1.5: Model Research & Benchmarking (Week 1-2) ⭐ NEW
    ↓
Phase 2: Camera Integration (Week 1-3)
    ↓
Phase 3: Person Detection (Week 3-5)
    ↓
Phase 3.5: ✅ VIDEO FILE TESTING (Week 5) OFFLINE
    ↓
Phase 4-6: Full Pipeline on Video Files (Week 6-12)
    ↓
✅ Validation Complete on Video
    ↓
Phase 7: Live Camera Integration (Week 12-14)
    ↓
Phase 8-9: Optimization & Final Testing (Week 14-16)
```

**Updated Timeline: 16 weeks (with buffer)**

### Key Principle: Test on Video First
**KHÔNG tiến hành live camera testing cho đến khi:**
- ✅ Video file testing hoàn thành 100%
- ✅ Tất cả metrics đạt minimum targets (>5 FPS, >85% detection)
- ✅ Không có critical bugs
- ✅ Performance benchmarks acceptable
- ✅ Test reports được review và approve
- ✅ Code coverage >80%
- ✅ All linter and type checks pass

---

## 10. Immediate Actions

### Phase 1: Setup
1. [ ] Review and approve this plan
2. [ ] Setup development environment
3. [ ] Create GitHub issues for each phase
4. [ ] Setup CI/CD pipeline

### Phase 2-3: Core Development
1. [ ] Begin Phase 1-2 implementation
2. [ ] Implement camera module
3. [ ] Implement detection module
4. [ ] Write unit tests for each module

### Phase 3.5: Critical - Video File Testing
1. [ ] Implement `process_video_file.py` script
2. [ ] Test detection on video file
3. [ ] Test tracking on video file
4. [ ] Generate test reports and visualizations
5. [ ] **Validate all metrics before proceeding to live camera**

### Phase 4-6: Continue on Video Files
1. [ ] Complete offline testing
2. [ ] Implement demographics estimation
3. [ ] Test database operations with video data
4. [ ] Generate annotated output videos

### Phase 7: Live Camera (Only After Video Testing Passes)
1. [ ] Implement `main_detector.py` for live streams
2. [ ] Test with single camera channel
3. [ ] Test with all 4 channels
4. [ ] Compare results with video testing

---

## 11. Resources

### Documentation
- [PyTorch MPS](https://pytorch.org/docs/stable/notes/mps.html)
- [Ultralytics YOLO](https://docs.ultralytics.com/)
- [ByteTrack](https://github.com/ifzhang/ByteTrack)
- [Core ML Tools](https://coremltools.readme.io/)
- [OpenCV Python](https://docs.opencv.org/)

### Models
- YOLOv8: https://github.com/ultralytics/ultralytics
- YOLOv9: https://github.com/WongKinYiu/yolov9
- Age/Gender models: To be researched and selected

---

**Document Version**: 2.0 (Revised with realistic targets)  
**Created**: 2024  
**Last Updated**: 2024 (Feasibility-driven adjustments)  
**Status**: Ready for Implementation  
**Branch**: main_func

