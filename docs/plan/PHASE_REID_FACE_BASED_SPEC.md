# Phase Re-ID: Face-based Re-Identification

## Overview

Thêm khả năng Re-ID sử dụng face embeddings để so sánh với body-based Re-ID hiện tại. Face-based Re-ID thường chính xác hơn trong việc phân biệt người, đặc biệt khi có điều kiện ánh sáng và góc nhìn tốt.

## Requirements

### Functional Requirements
1. ✅ Face-based Re-ID embedder module
2. ✅ Option để chọn giữa face-based và body-based Re-ID
3. ✅ Fallback từ face sang body nếu không detect được face
4. ✅ Benchmark và so sánh accuracy giữa face vs body Re-ID
5. ✅ Tích hợp vào tracker matching logic

### Non-Functional Requirements
- **Accuracy**: Face-based Re-ID nên có unique tracks ít hơn body-based
- **Face Detection Rate**: ≥70% tracks có face detected
- **Latency**: Face detection + embedding ≤15ms per person
- **Compatibility**: Tương thích với code hiện có

### Technical Constraints
- Sử dụng face detector hiện có (MediaPipe BlazeFace)
- Reuse ReIDEmbedder architecture
- CLI option: `--reid-use-face` (opt-in)
- Fallback logic khi không detect face

## User Stories

### US1: Face-based Re-ID Option
**As a**: Developer  
**I want**: Option để sử dụng face-based Re-ID thay vì body-based  
**So that**: Có thể cải thiện độ chính xác Re-ID matching

**Acceptance Criteria**:
- CLI option `--reid-use-face` available
- System falls back to body-based nếu không detect face
- No regression khi option disabled

### US2: Accuracy Comparison
**As a**: Developer  
**I want**: Benchmark so sánh face vs body Re-ID  
**So that**: Biết khi nào nên dùng phương pháp nào

**Acceptance Criteria**:
- Benchmark script tạo được
- So sánh unique tracks count
- Report rõ ràng về trade-offs

## Technical Approach

### 1. Face-based Re-ID Embedder
- **Architecture**: Similar to ReIDEmbedder but uses face crops
- **Input**: Face crop từ MediaPipe (112x112 typical)
- **Output**: L2-normalized embedding vector (128-dim)
- **Model**: Có thể dùng lightweight CNN hoặc projection matrix

### 2. Integration Strategy
- **Option 1**: Separate embedder instances (face vs body)
- **Option 2**: Single embedder với mode parameter
- **Chosen**: Option 1 (cleaner separation, easier to benchmark)

### 3. Fallback Logic
```
1. Try face detection
2. If face detected → use face Re-ID
3. If no face → use body Re-ID
4. If no Re-ID embedding → skip Re-ID matching (use IoU only)
```

### 4. Tracker Integration
- Tracker accepts both face and body embedders
- Matching logic tries face first, then body
- Cache stores embeddings với type indicator (face/body)

## Implementation Phases

### Phase 1: Face Re-ID Module (PR1)
**Scope**: Create face-based Re-ID embedder

**Tasks**:
- [ ] Create `src/modules/reid/face_embedder.py`
- [ ] Implement face crop preprocessing
- [ ] Implement embedding generation
- [ ] Unit tests

**Acceptance**:
- Face embedder generates valid embeddings
- Latency ≤15ms per face
- Unit tests pass

### Phase 2: Integration (PR2)
**Scope**: Integrate face Re-ID vào tracker và video processor

**Tasks**:
- [ ] Update Tracker to accept face embedder
- [ ] Add fallback logic (face → body)
- [ ] CLI option `--reid-use-face`
- [ ] Integration tests

**Acceptance**:
- Face Re-ID works in video processing
- Fallback logic correct
- No regression với body Re-ID

### Phase 3: Benchmark & Comparison (PR3)
**Scope**: Compare face vs body Re-ID accuracy

**Tasks**:
- [ ] Create benchmark script
- [ ] Run comparison tests
- [ ] Document results

**Acceptance**:
- Benchmark completes successfully
- Results documented clearly
- Recommendations provided

## Data Models

```python
@dataclass
class ReIDEmbedding:
    """Re-ID embedding with metadata."""
    embedding: np.ndarray
    type: str  # 'face' or 'body'
    timestamp: float
    confidence: float  # Face detection confidence (if type='face')
```

## Testing Strategy

### Unit Tests
- Face embedder generates consistent embeddings
- Fallback logic works correctly
- Error handling for missing face

### Integration Tests
- End-to-end video processing với face Re-ID
- Comparison với body Re-ID
- Performance metrics

### Benchmark Tests
- Unique tracks count comparison
- Processing time comparison
- Accuracy metrics

## Success Metrics

- **Unique Tracks**: Face Re-ID ≤ body Re-ID (fewer is better)
- **Face Detection Rate**: ≥70%
- **Latency Impact**: ≤10% overhead
- **No Regression**: Body Re-ID still works when face disabled

## Dependencies

- MediaPipe (already installed for face detection)
- Existing ReIDEmbedder as reference
- FaceDetector module (already exists)

## References

- Current Re-ID: `src/modules/reid/embedder.py`
- Face Detection: `src/modules/demographics/face_detector.py`
- Tracker: `src/modules/tracking/tracker.py`


