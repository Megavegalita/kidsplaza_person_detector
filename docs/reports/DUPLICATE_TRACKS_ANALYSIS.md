# Phân Tích: 1 Person Có 2 Bounding Boxes

## Vấn Đề
1 person nhưng có 2 bounding boxes hiển thị cùng lúc.

## Nguyên Nhân Có Thể

### 1. **Face Detection Detect 2 Faces Từ Cùng 1 Person** ⚠️ HIGH PROBABILITY

**Vấn đề**: Face detector (YuNet) có thể detect được 2 faces từ cùng 1 person nếu:
- Person quay mặt sang 2 góc khác nhau
- Có reflection hoặc shadow tạo face-like pattern
- Face detection quá sensitive

**Code Location**: `src/modules/detection/face_detector_opencv.py`
```python
# Mỗi face được convert thành 1 person detection
for face in faces:
    # ... convert face to person bbox
    person_detections.append({
        "bbox": [body_x1, body_y1, body_x2, body_y2],
        ...
    })
```

**Kết quả**: 2 detections từ 1 person → tracker tạo 2 tracks riêng

---

### 2. **Fallback Matching Không Check IoU Threshold** ⚠️ MEDIUM

**Vấn đề**: Fallback matching (line 230-247) không check IoU threshold:

```python
# Line 230-247: Fallback matching
if len(unmatched_detections) > 0 and len(self.tracks) > 0:
    for d_idx in list(unmatched_detections):
        best_iou = -1.0
        best_t_idx_fb: Optional[int] = None
        # ... find best IoU
        if best_t_idx_fb is not None:  # ← KHÔNG CHECK IoU THRESHOLD!
            track.update(...)  # Match ngay cả khi IoU rất thấp
```

**Vấn đề**: 
- Match detection với track ngay cả khi IoU < 0.3
- Có thể match 2 detections khác nhau vào 1 track
- Hoặc match 1 detection vào 2 tracks khác nhau (nếu logic không chặt)

---

### 3. **IoU Threshold Quá Thấp (0.3)** ⚠️ LOW

**Current**: `iou_threshold = 0.3`

**Vấn đề**: 
- Với threshold 0.3, 2 detections có thể không overlap đủ để match vào cùng track
- Nếu 2 faces từ 1 person có bboxes không overlap nhiều → tạo 2 tracks

---

### 4. **Re-ID Matching Có Thể Match Sai** ⚠️ LOW

**Code**: Line 249-302

**Vấn đề**:
- 2 detections từ 1 person có thể match với 2 tracks khác nhau qua Re-ID
- Chỉ check `best_t_idx not in matched_tracks` nhưng không check xem track đó đã có detection khác match chưa

---

### 5. **Multiple Detections Không Được Merge** ⚠️ MEDIUM

**Vấn đề**: 
- Không có bước NMS (Non-Maximum Suppression) cho face detections
- Nếu face detector detect 2 faces từ 1 person, cả 2 đều được giữ lại
- Không có logic để merge detections quá gần nhau

---

## Phân Tích Chi Tiết Code

### Tracker Matching Flow:

```
1. IoU Matching (line 214)
   └─> _associate_detections_to_tracks() 
       └─> Chỉ match nếu IoU >= 0.3

2. Fallback Matching (line 230)
   └─> Match best IoU (KHÔNG check threshold!) ⚠️
       └─> Có thể match sai

3. Re-ID Matching (line 249)
   └─> Match qua similarity (>= 0.65)
       └─> Chỉ check track chưa matched

4. Create New Track (line 305)
   └─> Nếu không match được → tạo track mới
       └─> Có thể tạo duplicate tracks
```

### Face Detection → Person Detection:

```
1. YuNet detect faces (line 202)
2. Mỗi face → 1 person detection (line 288-296)
3. Không có merge/NMS
4. 2 faces → 2 person detections
5. 2 detections → 2 tracks
```

---

## Giải Pháp Đề Xuất

### 1. **Thêm NMS cho Face Detections** ⭐ HIGH PRIORITY

Merge các face detections quá gần nhau trước khi convert sang person bbox:

```python
# Thêm vào face_detector_opencv.py
def _nms_faces(self, faces, iou_threshold=0.3):
    """Non-maximum suppression for faces."""
    # Implement NMS logic
    pass
```

### 2. **Fix Fallback Matching** ⭐ HIGH PRIORITY

Thêm IoU threshold check vào fallback:

```python
# Line 242: Thêm check IoU threshold
if best_t_idx_fb is not None and best_iou >= self.iou_threshold:
    track.update(...)
```

### 3. **Tăng IoU Threshold** ⭐ MEDIUM

Tăng từ 0.3 → 0.4 hoặc 0.5 để matching chặt chẽ hơn.

### 4. **Check Overlap Trước Khi Tạo Track Mới** ⭐ MEDIUM

Kiểm tra xem detection mới có overlap với tracks hiện tại không:

```python
# Trước khi tạo track mới (line 305)
if best_iou >= 0.1:  # Có overlap nhỏ → không tạo track mới
    continue  # Skip creating new track
```

### 5. **Logging Để Debug** ⭐ LOW

Thêm logging để track quá trình matching:

```python
logger.debug(
    "Detection %d matched to track %d (IoU=%.2f)",
    d_idx, t_idx, iou_val
)
```

---

## Kiểm Tra Ngay

### 1. Kiểm Tra Face Detection

Thêm logging để xem có bao nhiêu faces được detect:

```python
logger.debug("Detected %d faces from YuNet", len(faces))
```

### 2. Kiểm Tra Tracker Matching

Log các matches:

```python
logger.debug(
    "Frame %d: %d detections, %d tracks, %d matches",
    frame_num, len(detections), len(self.tracks), len(matched_indices)
)
```

### 3. Kiểm Tra Bbox Overlap

Tính IoU giữa các detections:

```python
for i, det1 in enumerate(detections):
    for j, det2 in enumerate(detections[i+1:], i+1):
        iou = compute_iou(det1["bbox"], det2["bbox"])
        if iou > 0.3:
            logger.warning("Detections %d and %d overlap (IoU=%.2f)", i, j, iou)
```

---

## Kết Luận

**Nguyên nhân có khả năng cao nhất**:
1. Face detection detect 2 faces từ 1 person (80%)
2. Fallback matching không check IoU threshold (15%)
3. Không có NMS để merge detections gần nhau (5%)

**Giải pháp ưu tiên**:
1. ✅ Fix fallback matching - thêm IoU threshold check
2. ✅ Thêm NMS cho face detections
3. ⚠️ Thêm logging để debug


