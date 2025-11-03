# Face Detection Alternatives - Comparison & Recommendation

## Problem Statement
MediaPipe face detection conflicts with TensorFlow due to protobuf version mismatch:
- MediaPipe 0.10.14 requires `protobuf < 5`
- TensorFlow 2.17+ requires `protobuf >= 5.28`
- MediaPipe auto-imports TensorFlow, causing initialization failure

## Solution Options

### Option 1: OpenCV DNN Face Detector ⭐ RECOMMENDED
**Library**: OpenCV DNN (built-in)
**Model**: OpenCV Face Detector (Yunet) or MTCNN/DDFace ONNX

**Pros**:
- ✅ **Fastest**: 5-8ms per frame (even faster than MediaPipe)
- ✅ **No dependencies**: Uses OpenCV DNN (already in requirements)
- ✅ **No conflicts**: Zero dependency issues with TensorFlow
- ✅ **Lightweight**: Small model size (~1-2MB)
- ✅ **Well-optimized**: Native C++ implementation
- ✅ **Good accuracy**: 85-90% detection rate

**Cons**:
- ⚠️ Slightly less accurate than MediaPipe BlazeFace on edge cases
- ⚠️ Model download required (one-time setup)

**Performance**:
- FPS: 60+ FPS on CPU, 120+ FPS on GPU
- Latency: 5-8ms per detection
- Model size: ~1.5MB

**Implementation**:
```python
import cv2

# Initialize face detector
face_detector = cv2.FaceDetectorYN.create(
    model="face_detection_yunet_2023mar.onnx",
    config="",
    input_size=(320, 320),  # or (640, 480) for higher accuracy
    score_threshold=0.6,
    nms_threshold=0.3,
    top_k=5000
)

# Detect faces
faces = face_detector.detect(frame)
```

---

### Option 2: TensorFlow Lite Face Detection
**Library**: TensorFlow Lite
**Model**: TensorFlow Lite face detection model

**Pros**:
- ✅ **Native TensorFlow**: Perfect compatibility
- ✅ **Optimized**: TensorFlow Lite optimized for edge devices
- ✅ **Good accuracy**: Similar to MediaPipe
- ✅ **Mobile-ready**: Designed for real-time on mobile/edge

**Cons**:
- ⚠️ Requires TensorFlow Lite runtime
- ⚠️ Slightly slower than OpenCV DNN (~10-15ms)
- ⚠️ Model conversion step needed

**Performance**:
- FPS: 40-50 FPS on CPU, 80-100 FPS on GPU
- Latency: 10-15ms per detection
- Model size: ~2-3MB

**Implementation**:
```python
import tensorflow as tf

# Load TFLite model
interpreter = tf.lite.Interpreter(model_path="face_detection.tflite")
interpreter.allocate_tensors()

# Run inference
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
interpreter.set_tensor(input_details[0]['index'], input_image)
interpreter.invoke()
detections = interpreter.get_tensor(output_details[0]['index'])
```

---

### Option 3: ONNX Runtime Face Detection
**Library**: ONNX Runtime (already in requirements.txt)
**Model**: Ultra-Light-Fast-Generic-Face-Detector or RetinaFace ONNX

**Pros**:
- ✅ **Cross-platform**: Works with any backend (TensorFlow, PyTorch, etc.)
- ✅ **Fast**: 8-12ms per detection
- ✅ **No conflicts**: ONNX Runtime is independent
- ✅ **Already available**: onnxruntime in requirements.txt

**Cons**:
- ⚠️ Requires ONNX model conversion
- ⚠️ Slightly more complex setup

**Performance**:
- FPS: 50-60 FPS on CPU, 100+ FPS on GPU
- Latency: 8-12ms per detection
- Model size: ~2-4MB

**Implementation**:
```python
import onnxruntime as ort

# Create inference session
session = ort.InferenceSession("face_detection.onnx")

# Run inference
outputs = session.run(None, {"input": preprocessed_image})
```

---

### Option 4: MTCNN (Not Recommended for Real-time)
**Library**: facenet-pytorch or tensorflow-mtcnn

**Pros**:
- ✅ High accuracy (95%+)
- ✅ Face landmarks included

**Cons**:
- ❌ **Too slow**: 50-100ms per detection (not real-time)
- ❌ Multiple stages (P-Net, R-Net, O-Net)
- ❌ Not suitable for live camera streams

**Performance**:
- FPS: 10-20 FPS only
- Latency: 50-100ms per detection

---

## Recommendation: OpenCV DNN Face Detector

### Why OpenCV DNN is Best for Live Camera?

1. **Performance**: Fastest option (5-8ms), crucial for real-time
2. **Zero conflicts**: No dependency issues
3. **Simple integration**: Uses existing OpenCV installation
4. **Good accuracy**: 85-90% detection rate (sufficient for person detection)
5. **Production-ready**: Battle-tested, widely used

### Implementation Plan

1. **Download model** (one-time):
   ```bash
   wget https://github.com/opencv/opencv_zoo/raw/master/models/face_detection_yunet/face_detection_yunet_2023mar.onnx
   ```

2. **Integrate into FaceDetectorFull**:
   - Replace MediaPipe initialization with OpenCV DNN
   - Update `detect_persons_from_faces()` method
   - Keep same API interface

3. **Testing**:
   - Test detection accuracy on sample frames
   - Benchmark latency vs MediaPipe
   - Verify false positive elimination

### Expected Results

- ✅ **False positives eliminated**: Only detects faces (not motorcycles)
- ✅ **Better performance**: 5-8ms vs MediaPipe's 8-10ms
- ✅ **No dependency conflicts**: Works with TensorFlow 2.17+
- ✅ **Stable FPS**: Consistent frame rates
- ⚠️ **Accuracy**: Slightly lower (85-90% vs 90-95%) but acceptable

---

## Comparison Table

| Solution | Speed | Accuracy | Conflicts | Complexity | Recommendation |
|----------|-------|----------|-----------|------------|----------------|
| **OpenCV DNN** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ None | ⭐ Easy | **BEST** |
| TensorFlow Lite | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ None | ⭐⭐ Medium | Good |
| ONNX Runtime | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ None | ⭐⭐ Medium | Good |
| MediaPipe | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ Conflicts | ⭐ Easy | Not viable |
| MTCNN | ⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ None | ⭐⭐⭐ Complex | Too slow |

---

## Next Steps

1. **Implement OpenCV DNN Face Detector** (recommended)
2. Test on live camera stream
3. Compare results with MediaPipe (if working)
4. Document performance metrics

---

*Generated: 2025-11-02*
*For: Kidsplaza Person Detector - Phase 7 Live Camera Integration*



