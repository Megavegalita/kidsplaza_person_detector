# Phase: ArcFace Integration for Face Re-ID

## Overview

Tích hợp ArcFace face recognition model thay thế lightweight projection matrix hiện tại trong Face Re-ID embedder để cải thiện độ chính xác Re-ID matching.

## Requirements

### Functional Requirements
1. ✅ ArcFace model integration vào FaceReIDEmbedder
2. ✅ Automatic model download và caching
3. ✅ Backward compatibility với existing code
4. ✅ Error handling và fallback mechanisms
5. ✅ Performance optimization (model loading, inference speed)

### Non-Functional Requirements
- **Accuracy**: Unique tracks ≤ 35 (better than current 44)
- **Latency**: Inference ≤ 20ms per face (vs current ~5ms)
- **Model Size**: ≤ 300MB (downloadable)
- **Compatibility**: Python 3.11+, macOS/Linux

### Technical Constraints
- Library: `insightface` (official ArcFace implementation)
- Model: `arcface_r100_v1` (512-dim embeddings)
- Device: Support CPU and MPS (Apple Silicon)
- Fallback: Graceful degradation if model unavailable

## User Stories

### US1: Accurate Face Re-ID
**As a**: System developer  
**I want**: ArcFace model cho face Re-ID  
**So that**: Face Re-ID accuracy tăng lên và có thể match hoặc beat body Re-ID

**Acceptance Criteria**:
- ArcFace model được download và load thành công
- Embeddings có 512 dimensions
- Unique tracks ≤ 35 (vs 44 hiện tại)
- Latency ≤ 20ms per face

### US2: Seamless Integration
**As a**: System developer  
**I want**: ArcFace integration không phá vỡ existing code  
**So that**: Hệ thống vẫn hoạt động nếu ArcFace không available

**Acceptance Criteria**:
- Automatic fallback to lightweight embedder
- No breaking changes to API
- Backward compatible

## Technical Approach

### 1. ArcFace Model

**Library:** `insightface`
**Model:** `arcface_r100_v1`
- Embedding dimension: 512
- Input size: 112x112 (aligned face)
- Pretrained on: MS1M, VGGFace2

**Installation:**
```bash
pip install insightface onnxruntime onnxruntime-gpu  # Optional GPU
```

### 2. Architecture

```
FaceReIDEmbedder (Base Class)
├── LightweightEmbedder (Current - fallback)
└── ArcFaceEmbedder (New - primary)
    ├── Model loading (lazy, cached)
    ├── Face alignment (if needed)
    └── Embedding extraction (512-dim)
```

### 3. Integration Strategy

- **Option 1**: Replace `_forward_model` with ArcFace
- **Option 2**: Conditional logic (ArcFace if available, else lightweight)
- **Chosen**: Option 2 (safer, backward compatible)

### 4. Face Alignment

ArcFace works best with aligned faces. May need:
- Face landmarks detection
- Alignment using landmarks
- Crop aligned face to 112x112

But for speed, we can skip alignment initially and test performance.

## Implementation Phases

### Phase 1: Dependencies & Setup (PR1)
**Scope**: Add insightface dependency và setup

**Tasks**:
- [ ] Add `insightface` to requirements.txt
- [ ] Create ArcFace embedder module
- [ ] Test model download và loading
- [ ] Unit tests for model loading

**Acceptance**:
- Model downloads successfully
- Can load và generate embeddings
- Unit tests pass

### Phase 2: Integration (PR2)
**Scope**: Integrate ArcFace into FaceReIDEmbedder

**Tasks**:
- [ ] Update FaceReIDEmbedder to use ArcFace
- [ ] Add fallback to lightweight embedder
- [ ] Update cache to handle 512-dim embeddings
- [ ] Integration tests

**Acceptance**:
- ArcFace used when available
- Falls back gracefully
- No breaking changes

### Phase 3: Benchmark & Optimization (PR3)
**Scope**: Test và optimize parameters

**Tasks**:
- [ ] Benchmark ArcFace vs lightweight
- [ ] Optimize similarity thresholds
- [ ] Performance profiling
- [ ] Final report

**Acceptance**:
- Unique tracks ≤ 35
- Latency acceptable
- Better than current 44 tracks

## Data Models

```python
@dataclass
class ArcFaceConfig:
    model_name: str = 'arcface_r100_v1'
    embedding_dim: int = 512
    input_size: Tuple[int, int] = (112, 112)
    use_gpu: bool = False  # MPS/GPU support
```

## Testing Strategy

### Unit Tests
- Model loading
- Embedding generation
- Error handling
- Fallback mechanism

### Integration Tests
- Video processing với ArcFace
- Performance metrics
- Comparison với lightweight embedder

### Benchmark Tests
- Unique tracks count
- Processing time
- Memory usage

## Success Metrics

- **Unique Tracks**: ≤ 35 (target: 30-33 to match body Re-ID)
- **Latency**: ≤ 20ms per face embedding
- **Model Load Time**: ≤ 5 seconds
- **Memory**: ≤ 500MB additional

## Dependencies

```txt
insightface>=0.7.3
onnxruntime>=1.16.0  # Required by insightface
```

## References

- InsightFace: https://github.com/deepinsight/insightface
- ArcFace Paper: https://arxiv.org/abs/1801.07698
- Model Zoo: https://github.com/deepinsight/insightface/wiki/Model-Zoo

---

*Created: 2025-10-29*


