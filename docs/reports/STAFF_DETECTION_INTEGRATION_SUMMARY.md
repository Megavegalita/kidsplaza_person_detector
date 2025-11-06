# Staff Detection Integration - Implementation Summary

## ✅ Implementation Completed

### Components Created/Modified

1. **`src/modules/detection/staff_voting_cache.py`** (NEW)
   - Voting mechanism với confidence weighting
   - Vote window: 10 frames
   - Vote threshold: 4/10 weighted votes
   - Cache cleanup: giữ lại 30 frames sau khi track mất

2. **`src/modules/detection/staff_classifier.py`** (NEW)
   - Load và classify staff vs customer model
   - Threshold: 0.4 (đã được test và chọn)

3. **`src/modules/detection/image_processor.py`** (MODIFIED)
   - Color coding: Red = Staff, Green = Customer
   - Label hiển thị: "Staff" hoặc "Customer"

4. **`src/modules/counter/daily_person_counter.py`** (MODIFIED)
   - Filter staff trước khi count (check cả `is_staff` và `person_type`)

5. **`src/scripts/process_live_camera.py`** (MODIFIED)
   - Integrate voting mechanism
   - Filter staff trước Re-ID và Counter
   - Database chỉ lưu customer detections
   - Display cả staff và customer với color coding

6. **`input/cameras_config/kidsplaza_thanhxuan.json`** (MODIFIED)
   - Thêm `staff_detection` config cho channel 4

---

## 🔄 Workflow Integration

### Flow mới:

```
1. YOLOv8 Detection → Detect person
2. Tracking → Assign track_id
3. Staff Classification + Voting → Classify và vote staff vs customer
   ├─ Classify mỗi khi person detect
   ├─ Vote với confidence weighting
   ├─ Fix classification khi đạt threshold (4/10 votes)
   └─ Cache classification theo track_id
4. Filter → Split detections thành customer và staff
5. Re-ID → Chỉ chạy cho customer_detections
6. Counter → Chỉ chạy cho customer_detections
7. Display → Hiển thị cả staff (red) và customer (green)
8. Database → Chỉ lưu customer detections
```

---

## 📊 Voting Mechanism Details

### Parameters:
- **Vote window:** 10 frames
- **Vote threshold:** 4 weighted votes
- **Confidence weighting:**
  - High confidence (>0.7): weight = 2.0
  - Medium confidence (0.5-0.7): weight = 1.5
  - Low confidence (<0.5): weight = 1.0
- **Cache keep frames:** 30 frames sau khi track mất

### Voting Logic:
```
FOR EACH track_id:
  - votes_staff = 0.0 (weighted)
  - votes_customer = 0.0 (weighted)
  
  EACH FRAME khi detect person:
    - Classify person crop
    - Add weighted vote:
      IF staff: votes_staff += weight
      ELSE: votes_customer += weight
    
    - IF votes_staff >= 4:
        → Fix as "staff"
    - ELSE IF votes_customer >= 4:
        → Fix as "customer"
    - ELSE IF frame_count >= 10:
        → Use majority vote
        → Fix classification
    
  - Once fixed: cache result, reuse for all subsequent frames
```

---

## 🎯 Filtering Points

### Staff được filter tại các điểm:

1. **Before Re-ID:**
   ```python
   customer_detections = [d for d in detections if d.get("is_staff") is not True]
   integrate_reid_for_tracks(frame, customer_detections, ...)
   ```

2. **Before Counter:**
   ```python
   counter.update(customer_detections, frame, frame_num)
   ```

3. **Before Database:**
   ```python
   _store_detections(customer_detections, ...)
   ```

4. **In Counter (double-check):**
   ```python
   customer_detections = [d for d in detections if d.get("is_staff") is not True]
   ```

---

## 🎨 Display Logic

### Color Coding:
- **Staff:** Red boxes (0, 0, 255) + Label "Staff"
- **Customer:** Green boxes (0, 255, 0) + Label "Customer" + PID (nếu có)

### Overlay:
- Hiển thị Global In/Out/Unique counts (chỉ tính customer)
- Hiển thị Current count trong zone (chỉ tính customer)
- **KHÔNG** hiển thị số staff hiện tại (theo yêu cầu)

---

## 💾 Database Behavior

### Staff Detections:
- **KHÔNG** được lưu vào database
- Filtered out trong `_store_detections()`

### Customer Detections:
- Được lưu vào `PersonDetection` table
- Counter events được lưu vào `counter_events` table

---

## ⚙️ Configuration

### Channel 4 Config:
```json
{
  "staff_detection": {
    "enabled": true,
    "model_path": "models/kidsplaza/best.pt",
    "conf_threshold": 0.4
  }
}
```

---

## 🔍 Error Handling

### Classification Fail:
- Default: **customer** (đếm hết)
- Rationale: Better safe than sorry (đếm nhiều hơn thiếu)

### Model Load Fail:
- Disable staff detection, treat all as customers
- Log warning và continue processing

---

## 📈 Performance Optimization

1. **Caching:** Classification được cache theo track_id
2. **Early Exit:** Không classify nếu không có person detection
3. **Filtering:** Staff được filter trước Re-ID và Counter để tiết kiệm processing
4. **Cleanup:** Cache được cleanup định kỳ để giữ memory clean

---

## 🧪 Testing Status

- ✅ Unit tests: StaffVotingCache và StaffClassifier
- ✅ Integration tests: Full pipeline với voting
- ✅ Video output tests: 5 videos với các threshold khác nhau
- ⏳ Live camera test: Pending

---

## 📝 Next Steps

1. Test với live camera channel 4
2. Monitor voting behavior và accuracy
3. Fine-tune vote threshold nếu cần
4. Verify counter chỉ đếm customers

---

## 📄 Files Modified/Created

### New Files:
- `src/modules/detection/staff_classifier.py`
- `src/modules/detection/staff_voting_cache.py`
- `docs/plan/PHASE_9_STAFF_DETECTION_FILTER.md`
- `docs/reports/STAFF_DETECTION_THRESHOLD_TEST.md`

### Modified Files:
- `src/modules/detection/image_processor.py`
- `src/modules/counter/daily_person_counter.py`
- `src/scripts/process_live_camera.py`
- `input/cameras_config/kidsplaza_thanhxuan.json`

### Test Files (can be removed later):
- `test_staff_classifier.py`
- `test_staff_integration.py`
- `test_staff_threshold.py`
- `test_staff_threshold_full.py`
- `generate_staff_videos.py`

