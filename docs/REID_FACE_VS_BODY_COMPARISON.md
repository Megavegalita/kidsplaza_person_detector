# Face Re-ID vs Body Re-ID Comparison Report

## Test Results

### Test Configuration

**Common Parameters:**
- Tracker IoU threshold: 0.4
- Tracker max age: 50
- Re-ID similarity threshold: 0.55
- Re-ID every K frames: 20
- Video: Binh Xa-Thach That_ch4_20251024102450_20251024112450.mp4 (3 minutes)

**Body Re-ID (conf2_med_sim_hi_iou):**
- Method: Body crop embeddings
- Unique Tracks: **33**

**Face Re-ID:**
- Method: Face crop embeddings (fallback to body)
- Unique Tracks: **64**
- Flag: `--reid-use-face`

## Comparison Results

| Metric | Body Re-ID | Face Re-ID | Difference |
|--------|------------|-------------|------------|
| Unique Tracks | 33 | 64 | +31 (worse) |
| Method | Body crop | Face crop | - |

**Conclusion:** Body Re-ID performs better than Face Re-ID for this video.

## Analysis

### Possible Reasons for Face Re-ID Underperformance

1. **Face Detection Rate**
   - Lower face detection rate → more fallbacks to body embeddings
   - Mixed embeddings (face + body) may reduce matching accuracy

2. **Embedding Quality**
   - Current face embedder uses lightweight projection matrix
   - Body embedder may capture more distinctive features for re-identification

3. **Video Characteristics**
   - CCTV video may have faces at various angles/distances
   - Body features more stable and consistent than faces

4. **Similarity Threshold**
   - Threshold 0.55 optimized for body embeddings
   - May need different threshold for face embeddings

## Recommendations

### For Production Use:
- ✅ **Use Body Re-ID** (conf2_med_sim_hi_iou configuration)
- ❌ **Do not use Face Re-ID** in current implementation

### Future Improvements:
1. **Better Face Embedder**
   - Use pretrained face recognition model (e.g., ArcFace, FaceNet)
   - Replace lightweight projection with actual face recognition backbone

2. **Adaptive Thresholds**
   - Different similarity thresholds for face vs body
   - Or separate thresholds per embedding type

3. **Hybrid Matching**
   - Use both face and body embeddings with weighted combination
   - Match when either face OR body matches above threshold

4. **Face Detection Quality**
   - Improve face detection rate and accuracy
   - Better preprocessing for challenging lighting/angles

## Technical Details

### Current Implementation
- Face embedder: Lightweight 128-dim projection
- Body embedder: Lightweight 128-dim projection  
- Fallback: Face → Body when face not detected
- Matching: Cross-type comparison with 10% type-match boost

### Suggested Improvements
- Face embedder: Pretrained face recognition model (e.g., ArcFace)
- Body embedder: Pretrained person re-ID model (e.g., ResNet50-based)
- Separate similarity thresholds per embedding type
- Better face detection with higher confidence/quality thresholds

---
*Generated: 2025-10-29*
