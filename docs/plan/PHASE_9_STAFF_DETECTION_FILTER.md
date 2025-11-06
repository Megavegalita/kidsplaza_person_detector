# Phase 9: Staff Detection and Filtering

## Mục tiêu

Thêm khả năng phát hiện và phân loại nhân viên Kidsplaza vs khách hàng:
- Sử dụng model mới tại `models/kidsplaza/best.pt` với 2 classes: `kidsplaza` (nhân viên) và `customer` (khách hàng)
- Nhân viên được vẽ với bounding box màu đỏ và label "Staff"
- Nhân viên vẫn được track nhưng KHÔNG được đếm khi vào/ra zone
- Chỉ khách hàng mới được đếm trong counter

## Kiến trúc

### Flow hiện tại:
1. YOLOv8 detection → detect person
2. Tracking → assign track_id
3. Re-ID → assign person_id (optional)
4. Counter → count enter/exit

### Flow mới:
1. YOLOv8 detection → detect person
2. **Staff Classifier → classify staff vs customer** (NEW)
3. Tracking → assign track_id
4. Re-ID → assign person_id (optional)
5. Counter → count enter/exit **chỉ cho customer** (MODIFIED)

## Implementation Plan

### Step 1: Tạo Staff Classifier Module
- File: `src/modules/detection/staff_classifier.py`
- Load model `models/kidsplaza/best.pt` (YOLOv8 format)
- Classify person crops thành "staff" hoặc "customer"
- Return classification với confidence score

### Step 2: Integrate vào Detection Pipeline
- File: `src/modules/detection/detector.py` hoặc `src/scripts/process_live_camera.py`
- Sau khi detect person với YOLOv8, chạy staff classifier trên mỗi person crop
- Thêm field `person_type: "staff" | "customer"` vào detection dict
- Thêm field `staff_confidence: float` vào detection dict

### Step 3: Modify Drawing để hiển thị Staff với màu đỏ
- File: `src/modules/detection/image_processor.py`
- Modify `draw_detections()` để:
  - Staff: màu đỏ `(0, 0, 255)` và label "Staff"
  - Customer: màu xanh lá `(0, 255, 0)` và label "Customer"

### Step 4: Filter Staff trong Counter
- File: `src/modules/counter/daily_person_counter.py`
- Modify `update()` để filter out detections với `person_type == "staff"`
- Chỉ pass customer detections vào zone counter

### Step 5: Update Configuration
- File: `input/cameras_config/kidsplaza_thanhxuan.json`
- Thêm config cho staff detection:
  - `staff_detection.enabled: bool`
  - `staff_detection.model_path: str`
  - `staff_detection.conf_threshold: float`

### Step 6: Database & Logging
- Log staff detections nhưng không count
- Có thể thêm field `person_type` vào detection records (optional)

## Testing Plan

1. **Unit Tests:**
   - Test staff classifier với sample crops
   - Test filtering logic trong counter

2. **Integration Tests:**
   - Test full pipeline với staff và customer
   - Verify counter chỉ count customer

3. **Visual Verification:**
   - Verify staff được vẽ màu đỏ
   - Verify counter không tăng khi staff vào/ra zone

## Files Modified/Created

### New Files:
- `src/modules/detection/staff_classifier.py`
- `tests/unit/test_staff_classifier.py`
- `docs/plan/PHASE_9_STAFF_DETECTION_FILTER.md`

### Modified Files:
- `src/modules/detection/image_processor.py` - Color coding
- `src/modules/counter/daily_person_counter.py` - Filter staff
- `src/scripts/process_live_camera.py` - Integrate classifier
- `input/cameras_config/kidsplaza_thanhxuan.json` - Config

## Notes

- Model `best.pt` là YOLOv8 format nên có thể load bằng `YOLO()` từ ultralytics
- Classes trong model: `0 = kidsplaza`, `1 = customer` (hoặc ngược lại, cần verify)
- Staff classification chỉ chạy trên person crops để tối ưu performance
- Có thể cache classification result theo track_id để tránh classify lại nhiều lần

