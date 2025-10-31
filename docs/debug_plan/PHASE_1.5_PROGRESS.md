# Phase 1.5: Model Research & Benchmarking - Progress Report

## 📊 Benchmark Results - YOLOv8n

### Test Environment
- **Device**: Mac M4 Pro
- **Python**: 3.11
- **PyTorch**: 2.10.0.dev
- **Model**: YOLOv8n (nano)

### Results

| Device | Avg Time (ms) | FPS | Min (ms) | Max (ms) | Speedup |
|--------|---------------|-----|----------|----------|---------|
| **CPU** | 18.91 | 52.89 | 18.41 | 19.49 | 1.00x |
| **MPS** | 18.69 | 53.51 | 18.16 | 20.01 | 1.01x |

### Key Findings

✅ **MPS Acceleration**: Working and slightly faster than CPU  
✅ **High Performance**: ~53 FPS on single inference  
⚠️ **Note**: Real-world FPS will be lower due to:
- Video frame processing overhead
- Tracking algorithm
- Demographics estimation
- Database operations
- Multi-threading overhead

### Performance Expectations

Based on benchmark, realistic targets for production:

**Single Frame Processing**:
- Inference only: ~50 FPS
- With preprocessing: ~40 FPS
- With full pipeline: ~10-15 FPS (estimated)

**Multi-Channel Processing**:
- 1 camera channel: ~10 FPS
- 2 camera channels: ~5 FPS each
- 4 camera channels: ~2-3 FPS each

### Recommendation

✅ **Use MPS device** for all inference operations
✅ **Target**: 5+ FPS per channel (achievable)
✅ **Optimization goal**: 10+ FPS per channel

---

## 🔍 Demographics Models Research

### Options Considered

#### Option 1: FairFace
- **Purpose**: Age and gender estimation
- **Framework**: PyTorch
- **Accuracy**: ~80-85% age, ~90% gender
- **Pros**: Good accuracy, well-documented
- **Cons**: May need fine-tuning for Asian demographics

#### Option 2: Oarriaga/face_recognition
- **Purpose**: Face detection and recognition
- **Framework**: dlib
- **Accuracy**: Very good detection
- **Pros**: Easy to use, good detection
- **Cons**: No built-in age/gender

#### Option 3: Age-Gender Net
- **Purpose**: Age and gender estimation
- **Framework**: TensorFlow/PyTorch
- **Accuracy**: ~70-80%
- **Pros**: Lightweight
- **Cons**: Lower accuracy

#### Option 4: Custom Model from scratch
- **Purpose**: Fully customized
- **Framework**: PyTorch
- **Accuracy**: Depends on dataset
- **Pros**: Can be tailored to specific needs
- **Cons**: Requires training data and time

### Recommendation

**Initial Choice**: FairFace or similar PyTorch model
**Fallback**: Simpler model if accuracy isn't critical

**Next Steps**:
1. Download and test FairFace
2. Test on sample data
3. Benchmark performance
4. Evaluate accuracy on diverse demographics

---

## 🎯 Performance Targets Set

Based on benchmark results and feasibility analysis:

### Detection Module
- **Inference Speed**: Target 5+ FPS per channel initially
- **Optimization Goal**: 10+ FPS per channel
- **Accuracy**: Target 85%, stretch goal 90%

### Tracking Module
- **Consistency**: Target 80%, stretch goal 90%
- **Performance Impact**: Minimal (on top of detection)

### Demographics Module
- **Accuracy**: Target 70%, stretch goal 80%
- **Performance Impact**: Low-medium (only on detected persons)

### Overall System
- **Single Channel**: 5-10 FPS
- **Four Channels**: 2-5 FPS per channel
- **Memory Usage**: < 4GB
- **Latency**: < 200ms per frame

---

## 📝 Next Actions

1. ✅ Benchmark completed
2. ⏳ Research demographics models (in progress)
3. ⏳ Test age/gender models on sample data
4. ⏳ Document model choices
5. ⏳ Set final performance targets

**Status**: Phase 1.5 - 40% Complete

