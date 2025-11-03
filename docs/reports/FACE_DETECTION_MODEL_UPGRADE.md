# Face Detection Model Upgrade Analysis

**Date**: 2025-11-03  
**Status**: 🔄 Evaluating Alternatives

---

## 🔍 CURRENT MODEL ANALYSIS

### **YuNet (OpenCV FaceDetectorYN)**

**Current Implementation**:
- Model: `face_detection_yunet_2023mar.onnx`
- Provider: OpenCV DNN
- Input Size: 320x320 (default), 640x480 (outdoor), 480x360 (indoor)
- Confidence Threshold: 0.35-0.55 (channel-dependent)

**Issues**:
- ❌ False positives từ motorcycle patterns (Channel 1)
- ❌ Không detect được faces quay lưng/không rõ (Channel 4)
- ⚠️ Accuracy ~85-95% (cần cải thiện)

**Pros**:
- ✅ Fast inference (~5-8ms)
- ✅ Built-in OpenCV support
- ✅ No external dependencies
- ✅ GPU acceleration via OpenCL

**Cons**:
- ❌ Limited accuracy for challenging scenarios
- ❌ Sensitive to false positives (patterns, objects)
- ❌ May miss faces at difficult angles

---

## 🎯 ALTERNATIVE MODELS

### **1. RetinaFace** ⭐⭐⭐⭐⭐ RECOMMENDED

**Overview**:
- State-of-the-art face detection model
- Higher accuracy than YuNet
- Better handling of difficult angles and lighting

**Pros**:
- ✅ Higher accuracy (~95-98%)
- ✅ Better at detecting faces at various angles
- ✅ Lower false positive rate
- ✅ Good performance on surveillance cameras
- ✅ Supports face landmarks (can validate face quality)

**Cons**:
- ⚠️ Slightly slower than YuNet (~10-15ms)
- ⚠️ Requires external library (retinaface-python hoặc dlib)
- ⚠️ Larger model size

**Implementation**:
```python
# Option 1: retinaface library
from retinaface import RetinaFace
faces = RetinaFace.detect_faces(img_path)

# Option 2: OpenCV DNN (if ONNX model available)
net = cv2.dnn.readNetFromONNX("retinaface.onnx")
```

**Accuracy**: ~95-98% (vs YuNet ~85-95%)

---

### **2. YOLOv8-Face** ⭐⭐⭐⭐ GOOD ALTERNATIVE

**Overview**:
- YOLOv8 specialized for face detection
- Fast inference with good accuracy
- Can detect multiple faces efficiently

**Pros**:
- ✅ Fast inference (~8-12ms)
- ✅ Good accuracy (~92-96%)
- ✅ Handles multiple faces well
- ✅ Good at detecting small faces

**Cons**:
- ⚠️ Requires YOLOv8-face model file
- ⚠️ May need fine-tuning for surveillance

**Implementation**:
```python
from ultralytics import YOLO
model = YOLO("yolov8n-face.pt")  # Face detection model
results = model(frame)
```

---

### **3. MTCNN** ⭐⭐⭐ LEGACY

**Overview**:
- Classic multi-task CNN for face detection
- Accurate but slower

**Pros**:
- ✅ Good accuracy (~90-95%)
- ✅ Detects face landmarks (validation)

**Cons**:
- ❌ Slow inference (~50-100ms)
- ❌ Not suitable for real-time CCTV

**Recommendation**: ❌ **Not recommended** (too slow)

---

### **4. MediaPipe BlazeFace** ⭐⭐⭐⭐ FAST OPTION

**Overview**:
- Google's lightweight face detector
- Optimized for mobile/edge devices

**Pros**:
- ✅ Very fast (~3-5ms)
- ✅ Good accuracy for frontal faces (~90-95%)
- ✅ Already integrated (but currently disabled)

**Cons**:
- ❌ Limited accuracy for side profiles
- ❌ TensorFlow dependency (conflict issues)
- ❌ Less accurate than RetinaFace/YuNet for difficult cases

**Note**: Đã có trong codebase nhưng disabled do TensorFlow conflicts

---

## 📊 COMPARISON TABLE

| Model | Accuracy | Speed | False Positives | Recommendation |
|-------|----------|-------|-----------------|----------------|
| **YuNet** (current) | ~85-95% | 5-8ms | High (motorcycles) | ⚠️ Current, issues |
| **RetinaFace** | ~95-98% | 10-15ms | Low | ⭐⭐⭐⭐⭐ **Best** |
| **YOLOv8-Face** | ~92-96% | 8-12ms | Medium | ⭐⭐⭐⭐ Good |
| **MTCNN** | ~90-95% | 50-100ms | Low | ❌ Too slow |
| **BlazeFace** | ~90-95% | 3-5ms | Medium | ⚠️ Already available |

---

## 🎯 RECOMMENDED UPGRADE PATH

### **Option 1: RetinaFace (Best Accuracy)** ⭐⭐⭐⭐⭐

**Why**:
- Highest accuracy (~95-98%)
- Best false positive handling
- Good for surveillance cameras

**Implementation**:
1. Install: `pip install retinaface`
2. Replace YuNet với RetinaFace
3. Adjust thresholds (lower needed due to better accuracy)

**Trade-offs**:
- Slightly slower (~10-15ms vs 5-8ms) - still acceptable
- External dependency (manageable)

---

### **Option 2: YOLOv8-Face (Fast + Accurate)** ⭐⭐⭐⭐

**Why**:
- Fast (~8-12ms)
- Good accuracy (~92-96%)
- Better than YuNet, faster than RetinaFace

**Implementation**:
1. Download YOLOv8-face model
2. Integrate via ultralytics
3. Replace YuNet

**Trade-offs**:
- Need to find/download model
- ultralytics dependency

---

### **Option 3: Improve YuNet với Better Validation** ⭐⭐⭐

**Why**:
- No model change needed
- Fast implementation
- Can reduce false positives with validation

**Implementation**:
1. Add landmark validation (check eye/nose/mouth positions)
2. Texture analysis (reject flat patterns)
3. Motion analysis (optional)
4. Increase thresholds

**Trade-offs**:
- Limited improvement potential
- Still may miss difficult faces

---

## 🔧 IMMEDIATE FIXES APPLIED

### **1. Channel 1 Threshold Increase**
```python
# Before: 0.45
# After: 0.55
face_confidence_threshold = max(0.55, conf_threshold * 1.1)
```

**Impact**: Reduce motorcycle false positives

### **2. Channel 4 Detection Frequency**
```python
# Before: detect_every_n = 4
# After: detect_every_n = 2 (Channel 4 only)
```

**Impact**: Better coverage, less likely to miss faces

---

## 📝 NEXT STEPS

### **Short-term** (Applied):
- ✅ Channel 1: Threshold 0.55
- ✅ Channel 4: Detect every 2 frames

### **Medium-term** (Recommend):
1. **Evaluate RetinaFace**:
   - Test accuracy improvement
   - Measure performance impact
   - Compare false positive rates

2. **If RetinaFace works well**:
   - Migrate from YuNet to RetinaFace
   - Adjust thresholds
   - Monitor improvements

### **Long-term**:
- Fine-tune model on surveillance data
- Add face quality validation
- Consider ensemble methods

---

**Status**: Immediate fixes applied ✅ | Model upgrade evaluation in progress 🔄

