# Phase 5B: Face-based Gender Classification với DeGirum MobileNetV2

## Reference
- Current: Upper-body crop (60% height) → MobileNetV3-Small → Accuracy: ~60-70%
- Upgrade: Face detection → DeGirum MobileNetV2 → Expected accuracy: 90-92%

## Tổng Quan

Tích hợp face detection + gender classification sử dụng DeGirum MobileNetV2 để cải thiện độ chính xác từ ~65% lên ~90-92%.

### Tech Stack Mới
- **Face Detection**: MediaPipe Face Detection hoặc BlazeFace (lightweight, real-time)
- **Gender Model**: DeGirum MobileNetV2 (UTKFace pretrained)
- **Accuracy**: 90-92% (vs 65% hiện tại)
- **Latency**: +5-8ms per detection với face crop
- **Integration**: Existing async worker pool

## Requirements

### Functional Requirements
1. ✅ Face detection trong person bounding box
2. ✅ Crop face region thay vì upper-body
3. ✅ Fallback to upper-body nếu không detect face
4. ✅ Gender classification với DeGirum MobileNetV2
5. ✅ Hiển thị trên overlay và bounding box labels
6. ✅ Ghi vào JSON report với confidence

### Non-Functional Requirements
- **Accuracy**: ≥90% (vs 65% hiện tại)
- **Face Detection Rate**: ≥70% tracks có face detected
- **Latency**: ≤15ms total (face detection + gender)
- **FPS Impact**: ΔFPS ≤5% (58 FPS → ≥55 FPS)
- **Fallback**: Upper-body crop nếu không detect face
- **Stability**: Flip rate ≤3% per minute per track

### Technical Constraints
- Compatible với async worker hiện có
- CLI: `--gender-enable-face-detection` (opt-in)
- Model: Download từ Hugging Face hoặc local cache
- No dependency conflicts (MediaPipe vs existing tools)

## User Stories

### US1: Face-based Gender Accuracy
**As a**: End user  
**I want**: Gender classification chính xác ≥90%  
**So that**: Dữ liệu demographics đáng tin cậy

**Acceptance Criteria**:
- Accuracy ≥90% verified trên sample videos
- Face detection rate ≥70% trong typical scenarios
- Fallback graceful khi không detect face
- Gender labels hiển thị trên bounding boxes

### US2: Performance không Degrade
**As a**: Developer  
**I want**: Face detection không làm FPS giảm >5%  
**So that**: Hệ thống vẫn realtime

**Acceptance Criteria**:
- ΔFPS ≤5% (58 FPS → ≥55 FPS)
- p95 total latency ≤20ms (face + gender)
- Async worker queue không overflow

### US3: Fallback Reliability
**As a**: System operator  
**I want**: Hệ thống hoạt động khi không detect face  
**So that**: Không mất dữ liệu

**Acceptance Criteria**:
- Fallback to upper-body crop nếu face detection fail
- Log warning khi fallback xảy ra
- Coverage ≥60% even với difficult angles

## Architecture

### Components (New)

```
src/modules/demographics/
├── face_detector.py          # MediaPipe BlazeFace detection
├── face_gender_classifier.py # DeGirum MobileNetV2 model
└── [existing files unchanged]
    ├── async_worker.py
    ├── metrics.py
    └── gender_classifier.py  # Keep as fallback
```

### Integration Flow

```
Person Detection (bbox) → Face Detection (within bbox)
                               ↓
                         Face Found?
                             /    \
                            Yes    No
                             ↓     ↓
                    Face Crop   Upper-body Crop (fallback)
                             ↓
                      DeGirum MobileNetV2
                             ↓
                        Gender + Confidence
                             ↓
                    Async Worker + Voting
                             ↓
                    Store in track metadata
```

### Data Structures

```python
@dataclass
class FaceDetectionResult:
    """Face detection result within person bbox."""
    face_detected: bool
    face_bbox: Optional[np.ndarray]  # (x1, y1, x2, y2) relative to person bbox
    confidence: float
    landmarks: Optional[np.ndarray]  # 5 keypoints

@dataclass
class GenderResult:
    """Gender classification result."""
    gender: str  # 'M', 'F', 'Unknown'
    confidence: float
    method: str  # 'face' or 'body'
    face_detected: bool
```

## Technical Approach

### 1. Face Detection
- **Technology**: MediaPipe BlazeFace (lightweight, 8-10ms per detection)
- **Alternative**: RetinaFace (more accurate but slower)
- **Optimization**: Batch processing for multiple persons
- **Crop Size**: 112x112 (typical face detection input)

### 2. Gender Model
- **Model**: DeGirum MobileNetV2 (pretrained UTKFace)
- **Source**: Download from Hugging Face `degirum/gender-classification-mobilenetv2`
- **Input**: 224x224 RGB face crop
- **Output**: 2 classes (M/F) với confidence scores
- **Latency**: ~3-5ms on M4 with MPS

### 3. Fallback Strategy
- **Primary**: Face detection → face crop → gender
- **Fallback**: No face → upper-body crop → existing MobileNetV3
- **Decision**: Confidence threshold (face: 0.7, gender: 0.5)

### 4. Async Integration
- Reuse existing `AsyncGenderWorker`
- Priority: Face-based tasks > body-based tasks
- Queue: Max 4 per frame, timeout 20ms per task

## Implementation Phases

### Phase 1: Face Detection Integration (PR1)
**Scope**: Add face detector module và integration logic

**Tasks**:
- [ ] Install MediaPipe: `pip install mediapipe`
- [ ] Create `face_detector.py` với BlazeFace model
- [ ] Add face detection trong video processing pipeline
- [ ] Unit tests cho face detection accuracy
- [ ] Integration tests với sample videos

**Acceptance**:
- Face detection rate ≥70% on test video
- Latency ≤10ms per person
- No FPS degradation

### Phase 2: DeGirum Model Integration (PR2)
**Scope**: Download và integrate DeGirum MobileNetV2

**Tasks**:
- [ ] Download model từ Hugging Face
- [ ] Create `face_gender_classifier.py` wrapper
- [ ] Add CLI flag `--gender-enable-face-detection`
- [ ] Fallback logic: face → body crop
- [ ] Update metrics: track `method` (face vs body)

**Acceptance**:
- Model loads successfully
- Gender prediction latency ≤8ms
- Accuracy verified trên samples
- Fallback hoạt động khi no face

### Phase 3: Testing & Benchmarking (PR3)
**Scope**: Comprehensive testing và performance validation

**Tasks**:
- [ ] Benchmark accuracy: face-based vs body-based
- [ ] Performance metrics: FPS, latency, queue
- [ ] Test edge cases: side view, occlusion, small faces
- [ ] Integration with existing overlay/labels
- [ ] Document best practices

**Acceptance**:
- Accuracy ≥90% verified
- ΔFPS ≤5% compared to baseline
- All edge cases handled gracefully
- Video outputs correct

## Testing Strategy

### Unit Tests
```python
def test_face_detector_detects_face():
    """Test face detection returns correct bbox."""
    
def test_face_gender_accuracy():
    """Test DeGirum model accuracy ≥90%."""
    
def test_fallback_to_upper_body():
    """Test fallback khi không detect face."""
```

### Integration Tests
- Face detection trong person bbox
- Gender prediction từ face crop
- Overlay và labels hiển thị đúng
- JSON report có gender data

### Benchmark Tests
- Face-based vs body-based accuracy comparison
- Performance impact (FPS, latency)
- Queue behavior và backpressure handling

## CLI Flags

```bash
# Enable face-based gender classification
--gender-enable
--gender-enable-face-detection  # NEW: use face detection
--gender-model-type timm_mobile  # Use DeGirum MobileNetV2
--gender-min-confidence 0.5
--gender-voting-window 7
```

## Success Metrics

- **Accuracy**: ≥90% verified trên test videos
- **Coverage**: ≥70% tracks có gender (vs ~60% hiện tại)
- **Latency**: p95 ≤20ms (face + gender)
- **FPS Impact**: ≤5% degradation
- **User Satisfaction**: Improved gender label correctness

## Timeline

- **PR1**: Face detection integration (2-3 days)
- **PR2**: DeGirum model integration (2-3 days)
- **PR3**: Testing & benchmarking (1-2 days)
- **Total**: 5-8 days

## Dependencies

```txt
mediapipe>=0.10.0
torch>=2.0.0
transformers>=4.30.0  # For Hugging Face download
```

## Notes

- Face detection optional: opt-in via CLI flag
- Fallback strategy ensures backward compatibility
- Existing body-based method remains available
- DeGirum model có lightweight footprint (~5MB)

