# Face Re-ID Parameter Optimization Report

## Executive Summary

Đã benchmark 8 cấu hình Face Re-ID khác nhau để tìm parameters tối ưu. Kết quả tốt nhất đạt 44 unique tracks (cải thiện từ 64 tracks ban đầu), nhưng vẫn kém hơn Body Re-ID (33 tracks).

## Test Results

### Best Face Re-ID Configuration

**Config Name:** `face_med_sim_very_long_age`

**Parameters:**
```bash
--reid-similarity-threshold 0.5
--tracker-max-age 70
--tracker-iou-threshold 0.4
--reid-every-k 20
```

**Results:**
- Unique Tracks: **44**
- Improvement từ baseline (64): **31.3% giảm**

### Top 3 Configurations

| Rank | Config | Unique Tracks | Key Parameters |
|------|--------|---------------|----------------|
| 🥇 | face_med_sim_very_long_age | **44** | sim=0.5, max_age=70 |
| 🥈 | face_aggressive | 47 | sim=0.35, max_age=60, k=15 |
| 🥉 | face_low_sim_freq_reid | 58 | sim=0.45, k=15 |

## Comparison with Body Re-ID

| Method | Best Config | Unique Tracks | Status |
|--------|-------------|---------------|--------|
| **Body Re-ID** | conf2_med_sim_hi_iou | **33** | ✅ Best |
| **Face Re-ID** | face_med_sim_very_long_age | **44** | ⚠️ Still worse |

**Gap:** Face Re-ID kém hơn 11 tracks (33.3% nhiều hơn)

## Key Findings

### Critical Parameters for Face Re-ID

1. **Tracker Max Age**: **70 frames** (quan trọng nhất)
   - Cho phép track tồn tại lâu hơn
   - Giúp match người quay lại sau khi rời khỏi frame
   - Ảnh hưởng lớn nhất đến kết quả

2. **Similarity Threshold**: **0.5** (vừa phải)
   - Quá thấp (0.3-0.35) → nhiều false positives
   - Quá cao (0.55+) → ít matches
   - 0.5 cân bằng tốt cho face embeddings

3. **Re-ID Frequency** (every_k): **20 frames**
   - Không ảnh hưởng nhiều trong test này
   - 15 vs 20 frames không có khác biệt lớn

### Why Face Re-ID Still Underperforms

1. **Lightweight Embedder**
   - Current face embedder dùng random projection matrix
   - Không capture được đặc trưng face tốt như body features
   - Cần pretrained face recognition model

2. **Face Detection Challenges**
   - CCTV video có faces ở nhiều góc độ
   - Distance/lighting variations
   - Face detection rate có thể không đủ cao

3. **Mixed Embedding Types**
   - Khi face không detect được → fallback body
   - Mixed face + body embeddings khó match hơn
   - Body embedding chất lượng tốt hơn trong trường hợp này

## Recommendations

### For Current Implementation

**Nếu bắt buộc dùng Face Re-ID, sử dụng:**

```bash
--reid-enable
--reid-use-face
--reid-similarity-threshold 0.5
--tracker-max-age 70
--tracker-iou-threshold 0.4
--reid-every-k 20
```

**Kết quả:** 44 unique tracks (vẫn kém Body Re-ID 11 tracks)

### For Better Face Re-ID Performance

1. **Upgrade Face Embedder**
   - **Model Recommendation:** Use pretrained face recognition model
     - **ArcFace** (insightface library): Best accuracy
     - **FaceNet** (TensorFlow): Good balance
     - **ResNet50 face** (trained on VGGFace2): Alternative
   
   - **Implementation:**
     ```python
     # Example using insightface
     from insightface import app
     face_app = app.FaceAnalysis(name='arcface_r100_v1')
     embedding = face_app.get(np_image)
     ```

2. **Separate Thresholds**
   - Face similarity threshold: 0.5-0.55
   - Body similarity threshold: 0.55 (current)
   - Adaptive based on embedding quality

3. **Improve Face Detection**
   - Higher confidence threshold (0.7+) cho quality faces
   - Better preprocessing (normalization, alignment)
   - Use full-range model (model_selection=1) for far faces

4. **Hybrid Strategy** (Future)
   - Use BOTH face and body embeddings
   - Match when either exceeds threshold
   - Weighted combination: `0.6 * face_sim + 0.4 * body_sim`

## Model Recommendations for Production

### Option 1: ArcFace (Recommended)

**Library:** `insightface`
**Model:** `arcface_r100_v1`
**Embedding Dim:** 512

**Pros:**
- State-of-the-art accuracy
- Robust to variations
- Good for CCTV scenarios

**Cons:**
- Larger model size
- Slightly slower inference

**Installation:**
```bash
pip install insightface
```

**Usage:**
```python
import insightface
face_app = insightface.app.FaceAnalysis(name='arcface_r100_v1')
embedding = face_app.get(face_crop)
```

### Option 2: FaceNet (Balanced)

**Library:** TensorFlow Hub
**Model:** `facenet_512`
**Embedding Dim:** 512

**Pros:**
- Good accuracy
- Well-documented
- Balanced performance

**Cons:**
- Requires TensorFlow
- Moderate model size

### Option 3: MobileFaceNet (Fast)

**Library:** Custom PyTorch
**Model:** MobileFaceNet
**Embedding Dim:** 128-512

**Pros:**
- Very fast inference
- Small model size
- Suitable for real-time

**Cons:**
- Slightly lower accuracy
- Requires custom implementation

## Implementation Priority

### Phase 1: Quick Win (Current)
- ✅ Use best config: `face_med_sim_very_long_age`
- Result: 44 tracks (improved from 64)

### Phase 2: Embedder Upgrade
- Replace lightweight projection với ArcFace
- Expected: 35-40 tracks (closer to body Re-ID)

### Phase 3: Full Optimization
- Separate thresholds per embedding type
- Hybrid face+body matching
- Better face detection
- Expected: 30-33 tracks (match or beat body Re-ID)

## Conclusion

**Current Status:**
- ✅ Face Re-ID đã được optimize parameters
- ✅ Best config: 44 tracks (cải thiện 31.3%)
- ⚠️ Vẫn kém Body Re-ID (44 vs 33 tracks)

**Recommendation:**
- **For production:** Continue using Body Re-ID (33 tracks)
- **For Face Re-ID improvement:** Upgrade embedder to ArcFace/FaceNet
- **Future work:** Implement hybrid matching strategy

---
*Generated: 2025-10-29*
*Benchmark Data: output/face_reid_benchmark/benchmark_summary.json*


