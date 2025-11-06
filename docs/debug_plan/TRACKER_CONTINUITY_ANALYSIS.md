# Phân tích: Tracker không liên tục

## 🔍 Vấn đề phát hiện:

### 1. **Tracker không trả về tracks khi không có detections mới**
- **Logs cho thấy:** "Tracker update: 0 detections, 0 with track_id: none"
- **Nguyên nhân:** Khi không có detections, tracker gọi `_get_confirmed_tracks(max_time_since_update=max_age)`
- **Vấn đề:** Tracks có thể không được confirmed (hits < min_hits=3) hoặc đã bị remove

### 2. **Detections bị filter trước tracker**
- **Size filter:** `h < 50 or w < 30` - có thể filter quá nhiều
- **Location:** Line 775 trong `process_live_camera.py`
- **Impact:** Detections hợp lệ có thể bị filter → tracker không nhận được

### 3. **Stats "Tracks: 0"**
- **Nguyên nhân:** `unique_track_ids` chỉ được update từ `customer_detections`
- **Đã fix:** Update từ ALL detections (trước filtering)
- **Nhưng:** Vẫn có thể = 0 nếu không có detections nào pass filter

## 🔧 Đã Fix:

### 1. **Tracker max_time_since_update**
- **Cũ:** Hardcoded 10 frames
- **Mới:** `max_age` (90 frames)
- **Impact:** Tracks có thể persist lâu hơn khi detections sparse

### 2. **unique_track_ids update**
- **Cũ:** Chỉ từ `customer_detections`
- **Mới:** Từ ALL detections (trước staff filtering)
- **Impact:** Stats reflect tất cả tracks

## ⚠️ Vấn đề còn lại:

### 1. **Detections bị filter quá nhiều**
- Size filter `h < 50 or w < 30` có thể quá strict
- Cần kiểm tra xem có detections nào bị filter không

### 2. **Tracker không trả về predicted tracks**
- Khi không có detections mới, tracker chỉ trả về confirmed tracks
- Nhưng nếu tracks chưa confirmed (hits < min_hits), không được trả về
- **min_hits=3** có thể quá cao cho sparse detections

### 3. **Detection gaps**
- Detections không liên tục (gaps lớn giữa các detections)
- Tracker có thể mất tracks trong gaps này

## 📊 Phân tích từ logs:

```
Person detections: frame 804, 805, 807, 808, 809, 811, 812, 813, 814, 815
Tracker updates: 0 detections (khi không có detections mới)
Tracker stats: Tracks: 0 (consistent)
```

**Vấn đề:**
- Detections có nhưng không liên tục
- Tracker không maintain tracks giữa các detections
- Stats = 0 vì không có tracks được maintain

## 🔧 Giải pháp đề xuất:

### 1. **Giảm min_hits**
- **Hiện tại:** min_hits=3
- **Đề xuất:** min_hits=1 hoặc 2
- **Lý do:** Cho phép tracks được confirmed nhanh hơn

### 2. **Giảm size filter**
- **Hiện tại:** h < 50 or w < 30
- **Đề xuất:** h < 40 or w < 25
- **Lý do:** Giữ lại nhiều detections hợp lệ hơn

### 3. **Tăng max_age**
- **Hiện tại:** max_age=90
- **Đề xuất:** max_age=120 hoặc 150
- **Lý do:** Tracks persist lâu hơn trong gaps

### 4. **Kiểm tra detection filtering**
- Log số detections trước và sau filter
- Xác định xem có detections nào bị filter không cần thiết không

