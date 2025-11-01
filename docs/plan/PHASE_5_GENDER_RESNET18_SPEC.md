# Phase 5: Gender Classification (Face-based ResNet-18) với Async Integration

## Reference
- [Đề xuất Stack Re-ID & Phân loại Giới tính](https://docs.google.com/document/d/1OqQ-7W-jSMCALZICdgKIi9sedr_5d1w1aNFuoyzRc_0/edit?tab=t.0)

## Tổng Quan

Tích hợp gender classification dựa trên khuôn mặt sử dụng ResNet-18 với cơ chế async để không làm gián đoạn workflow xử lý chính.

### Tech Stack (theo tài liệu)
- **Gender Model**: ResNet-18 (PyTorch)
- **Accuracy**: >97% dựa trên khuôn mặt
- **Balance**: Cân bằng tốt tốc độ và hiệu suất
- **Integration**: Async worker pool để non-blocking

## Requirements

### Functional Requirements
1. ✅ Gender classification dựa trên khuôn mặt
2. ✅ Async processing không block pipeline chính
3. ✅ Hiển thị overlay với gender counts (M/F/U)
4. ✅ Ghi gender data vào JSON report
5. ✅ Metrics và logging đầy đủ

### Non-Functional Requirements
- **Latency**: <10-15ms per crop trên M4 với MPS
- **FPS Impact**: ΔFPS ≤5% so với baseline (58 FPS → tối thiểu 55 FPS)
- **Stability**: Flip rate ≤3% per minute per track
- **Coverage**: ≥70% tracks có gender sau 3 phút
- **Queue**: Không overflow >5% thời gian chạy

### Technical Constraints
- Device: Mac M4 với MPS acceleration
- Compatible với existing tracker/reid pipeline
- No breaking changes to current workflow
- Configurable qua CLI flags

## User Stories

### US1: Hiển thị Gender trên Video
**As a**: System operator  
**I want**: Xem gender counts (M/F/U) trên overlay video  
**So that**: Theo dõi demographics realtime

**Acceptance Criteria**:
- Overlay hiển thị "Gender M/F/U: 10/15/5"
- Cập nhật nhãn trong <500ms sau track confirmation
- Không nhấp nháy (flip rate ≤3% per minute)

### US2: Non-blocking Performance
**As a**: Developer  
**I want**: Gender classification không làm FPS giảm >5%  
**So that**: Hệ thống vẫn realtime

**Acceptance Criteria**:
- ΔFPS ≤5% baseline (58 FPS → ≥55 FPS)
- p95 latency gender task ≤40ms
- Queue không đầy >5% thời gian chạy

### US3: Data Export
**As a**: Data analyst  
**I want**: Gender data trong JSON report  
**So that**: Phân tích demographics offline

**Acceptance Criteria**:
- JSON có `gender` per detection
- Summary có `gender_counts_total`, `coverage%`
- Logs định kỳ mỗi 10s

### US4: Configurable
**As a**: SRE  
**I want**: Enable/disable gender và chọn model type  
**So that**: Tùy chỉnh theo nhu cầu

**Acceptance Criteria**:
- CLI flags: `--gender-enable`, `--gender-every-k`, `--gender-model-type`
- Model types: `resnet18_face`, `mobilenetv3`, `efficientnet`
- Thresholds configurable: `--gender-attach-th`, `--gender-keep-th`

## Architecture

### Components

```
src/modules/demographics/
├── face_detector.py       # Lightweight face detection (BlazeFace/RetinaFace)
├── face_cropper.py        # Face cropping với fallback to upper-body
├── gender_classifier.py   # ResNet-18 + voting/hysteresis logic
├── async_worker.py        # Async worker pool + queue management
└── metrics.py             # Metrics collector
```

### Data Flow

```
Tracker → Gender Async Worker
                 ↓
         Priority Queue (new-confirmed > ambiguous > refresh)
                 ↓
         Batch Processing (max N crops/frame)
                 ↓
         Face Detection → Face Cropping
                 ↓
         ResNet-18 Classification
                 ↓
         Voting + Hysteresis
                 ↓
         Update GenderCache
                 ↓
Overlay Reads Cache (non-blocking)
```

### Async Worker Design

**Queue Management**:
- Priority queue: new-confirmed tracks > ambiguous > periodic refresh
- Max queue size: 100 tasks
- Backpressure: Drop low-priority khi queue đầy
- Timeout: Cancel tasks >100ms old (bbox changed)

**Batch Processing**:
- Group crops per frame
- Max batch size: 5 crops
- Time budget: 50ms per batch
- Early return nếu timeout

**Metrics**:
- `gender_calls/frame`, `gender_ms/call` (p50, p95)
- `coverage%` (labeled/total), `flip_rate`, `queue_len`
- Distribution: M/F/U counts

## Integration Points

### CLI Arguments
```bash
--gender-enable              # Enable gender classification
--gender-every-k N          # Classify every K frames (default: 30)
--gender-model-type TYPE   # resnet18_face | mobilenetv3 | efficientnet
--gender-attach-th FLOAT   # Attach threshold (default: 0.75)
--gender-keep-th FLOAT     # Keep threshold (default: 0.65)
--gender-vote-window N    # Voting window size (default: 5)
--gender-max-per-frame N   # Max crops per frame (default: 5)
```

### JSON Report Structure
```json
{
  "summary": {
    "unique_tracks_total": 30,
    "gender_counts_total": {
      "M": 10,
      "F": 15,
      "Unknown": 5
    },
    "gender_coverage_pct": 83.3
  },
  "frame_results": [
    {
      "frame_number": 1,
      "gender_counts": {"M": 5, "F": 8, "Unknown": 2},
      "detections": [
        {
          "track_id": 1,
          "gender": "M",
          "gender_confidence": 0.87
        }
      ]
    }
  ]
}
```

### Metrics Logging
```
INFO - Gender metrics at 10s: calls=45, avg_ms=8.2, p95_ms=12.5, coverage=78%, M=5, F=10, U=3
INFO - Queue: len=2/100, dropped=0, enqueued=47, completed=45
```

## Testing Strategy

### Unit Tests
- Voting logic với các window sizes
- Hysteresis thresholds
- Queue prioritization
- Timeout/cancel logic
- Bbox parsing/clamping

### Integration Tests
- Full pipeline 3 phút video
- Đo ΔFPS, coverage%, flip_rate, latency
- A/B config comparison
- Queue overflow scenarios

### Acceptance Tests
- Config A: every_k=30, vote=5, 0.75/0.65
- Config B: every_k=20, vote=7, 0.70/0.60
- Compare: ΔFPS, coverage, flip_rate
- Recommend optimal config

## PR Breakdown

### PR1: Async Worker + Queue Framework
**Scope**: Core async infrastructure, priority queue, metrics collector  
**Target**: <300 LOC  
**Files**: `async_worker.py`, `metrics.py`

### PR2: Face Detection/Cropping
**Scope**: Face detector + cropper với fallback  
**Target**: <250 LOC  
**Files**: `face_detector.py`, `face_cropper.py`

### PR3: Gender Classifier (ResNet-18)
**Scope**: ResNet-18 model + voting/hysteresis  
**Target**: <400 LOC  
**Files**: `gender_classifier.py` (refactor existing)

### PR4: Pipeline Integration
**Scope**: CLI integration, overlay, JSON reports  
**Target**: <300 LOC  
**Files**: `process_video_file.py` (integration)

### PR5: Testing & Benchmarks
**Scope**: Unit tests + integration benchmarks  
**Target**: Complete test coverage ≥80%  
**Files**: `tests/unit/test_gender*.py`, `tests/integration/`

## Checklist

- [x] Requirements documented
- [x] User stories written
- [x] Architecture planned
- [x] Feature branch created
- [ ] PR1: Async worker implemented
- [ ] PR2: Face detection implemented
- [ ] PR3: ResNet-18 classifier implemented
- [ ] PR4: Integration complete
- [ ] PR5: Tests complete
- [ ] All PRs merged to main_func
- [ ] Documentation updated

## Timeline

- Week 1: PR1 + PR2 (Async worker + face detection)
- Week 2: PR3 + PR4 (Classifier + integration)
- Week 3: PR5 (Testing + benchmarks + A/B comparison)
- Week 4: Documentation + acceptance review


