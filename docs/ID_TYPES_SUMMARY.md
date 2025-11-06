# Các Loại ID Được Sử Dụng Trong Hệ Thống

## 1. TRACK_ID (TID)
- **Nguồn:** ByteTrack Tracker
- **Loại:** Integer (int)
- **Mục đích:** ID tạm thời cho mỗi track trong một session
- **Đặc điểm:**
  - Thay đổi khi track bị mất và tái xuất hiện
  - Chỉ tồn tại trong một session
  - Được hiển thị trên overlay dạng: `ID{track_id}`
- **Sử dụng trong:**
  - ZoneCounter: tracking zone state per track
  - Staff classification: voting cache key
  - Gender classification: track-based voting

## 2. PERSON_ID (PID)
- **Nguồn:** PersonIdentityManager + Re-ID Embedding
- **Loại:** String (str)
- **Mục đích:** ID duy nhất cho mỗi người, persistent across sessions
- **Đặc điểm:**
  - Được gán từ Re-ID embedding (ArcFace hoặc body Re-ID)
  - Được lưu trong Redis cache
  - Persistent qua nhiều sessions và channels
  - Được hiển thị trên overlay dạng: `PID:{person_id}`
- **Sử dụng trong:**
  - DailyPersonCounter: đếm mỗi người 1 lần/ngày
  - Database counter_events: lưu person_id vào DB
  - Cross-channel synchronization

## 3. CHANNEL_ID
- **Nguồn:** Camera Config
- **Loại:** Integer (int)
- **Mục đích:** ID của camera channel (1, 2, 3, 4)
- **Sử dụng trong:**
  - Database records (detections, counter_events)
  - Redis keys (person_id mapping per channel)
  - Config loading

## 4. ZONE_ID
- **Nguồn:** Camera Config (counter zones)
- **Loại:** String (str)
- **Mục đích:** ID của zone đếm (ví dụ: 'zone_1')
- **Sử dụng trong:**
  - ZoneCounter: tracking enter/exit per zone
  - Database counter_events: zone_id field

## 5. DETECTION_ID
- **Nguồn:** Generated (camera_id_channel_id_frame_num_track_id)
- **Loại:** String (str)
- **Mục đích:** Unique ID cho mỗi detection record trong DB
- **Format:** `{camera_id}_{channel_id}_{frame_num}_{track_id}`
- **Sử dụng trong:**
  - Database detections table (primary key)

## 6. SESSION_ID
- **Nguồn:** Generated (timestamp-based hoặc RTSP URL stem)
- **Loại:** String (str)
- **Mục đích:** ID cho một processing session
- **Sử dụng trong:**
  - Re-ID cache keys
  - Gender classification task IDs
  - Database extra_json fields

## 7. RUN_ID
- **Nguồn:** Generated (timestamp) hoặc user-provided
- **Loại:** String (str)
- **Mục đích:** ID cho một run/experiment
- **Format:** `YYYYMMDD_HHMMSS` (default)
- **Sử dụng trong:**
  - Output directory naming
  - Database extra_json fields

## Hiển Thị Trên Overlay

Trên bounding box, label được hiển thị theo thứ tự ưu tiên:

1. **Nếu có person_id:** `PID:{person_id} - {class_name}: {conf:.2f}`
2. **Nếu không có person_id nhưng có track_id:** `ID{track_id} - {class_name}: {conf:.2f}`
3. **Thêm gender nếu có:** ` | {gender_full}({conf:.2f})`

**Ví dụ:**
- `PID:P123 - Customer: 0.85 | Male(0.92)`
- `ID3 - Staff: 0.76`
- `ID5 - Customer: 0.91 | Female(0.88)`

## Luồng Xử Lý ID

1. **Detection** → `track_id` (từ Tracker)
2. `track_id` + Re-ID embedding → `person_id` (từ PersonIdentityManager)
3. `track_id` + `person_id` → Counter events
4. Counter events → Database (với cả `track_id` và `person_id`)
