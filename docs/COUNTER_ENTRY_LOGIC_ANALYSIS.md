# Phân Tích Logic Ghi Nhận Khách Hàng Vào (Entry Event)

## Tổng Quan

Tài liệu này phân tích chi tiết các điều kiện logic để hệ thống ghi nhận một sự kiện **khách hàng vào (entry)** vào database.

## Luồng Xử Lý Tổng Thể

```
1. Detection (YOLOv8) → 2. Tracking (ByteTrack) → 3. Staff Classification → 
4. Filter Staff → 5. Re-ID → 6. Zone Detection → 7. Daily Count Check → 8. Database Storage
```

---

## Điều Kiện 1: Detection Phải Có `track_id`

**Vị trí:** `src/modules/counter/zone_counter.py:540-543`

```python
for detection in detections:
    track_id = detection.get("track_id")
    if track_id is None:
        continue  # ❌ Bỏ qua nếu không có track_id
```

**Điều kiện:** Detection phải có `track_id` hợp lệ (không phải `None`).

**Kết quả nếu không đạt:** Detection bị bỏ qua, không kiểm tra zone.

---

## Điều Kiện 2: Detection Phải Có Centroid Hợp Lệ

**Vị trí:** `src/modules/counter/zone_counter.py:544-546`

```python
centroid = self._get_track_centroid(detection)
if centroid is None:
    continue  # ❌ Bỏ qua nếu không có centroid
```

**Điều kiện:** Detection phải có bounding box hợp lệ để tính centroid (tâm của bounding box).

**Kết quả nếu không đạt:** Detection bị bỏ qua, không kiểm tra zone.

---

## Điều Kiện 3: Phải Là Khách Hàng (Không Phải Staff)

**Vị trí:** `src/modules/counter/daily_person_counter.py:67-71`

```python
customer_detections = [
    det for det in detections
    if det.get("is_staff") is not True
    and det.get("person_type") != "staff"
]
```

**Điều kiện:** 
- `is_staff` phải là `False` hoặc `None` (không phải `True`)
- `person_type` phải khác `"staff"`

**Kết quả nếu không đạt:** Detection bị loại khỏi danh sách `customer_detections`, không được xử lý tiếp.

**Lưu ý:** Staff detection được thực hiện trước khi đến `DailyPersonCounter`, với voting mechanism để đảm bảo độ chính xác.

---

## Điều Kiện 4: Centroid Phải Nằm Trong Zone (Polygon) hoặc Vượt Qua Line

**Vị trí:** `src/modules/counter/zone_counter.py:571-577`

```python
if zone_type == "polygon":
    curr_in_zone = self._check_zone_polygon(centroid, zone, frame_width, frame_height)
elif zone_type == "line":
    curr_in_zone = self._check_zone_line(prev_centroid, centroid, zone, frame_width, frame_height)
else:
    curr_in_zone = False
```

**Điều kiện:**
- **Polygon:** Centroid phải nằm bên trong polygon được định nghĩa.
- **Line:** Centroid phải vượt qua đường line từ bên này sang bên kia (dựa trên `prev_centroid` và `curr_centroid`).

**Kết quả nếu không đạt:** `curr_in_zone = False`, không tạo entry event.

---

## Điều Kiện 5: Phải Đạt Ngưỡng Enter Threshold (Flickering Protection)

**Vị trí:** `src/modules/counter/zone_counter.py:579-606`

```python
enter_threshold = zone.get("enter_threshold", 1)  # Default: 1 frame

# Track consecutive frames inside/outside
if curr_in_zone:
    if self.track_zone_frame_count[track_id][zone_id] >= 0:
        self.track_zone_frame_count[track_id][zone_id] += 1
    else:
        self.track_zone_frame_count[track_id][zone_id] = 1

# Only consider state change if threshold is met
confirmed_curr_in_zone = (
    curr_in_zone and self.track_zone_frame_count[track_id][zone_id] >= enter_threshold
)
```

**Điều kiện:** 
- Track phải ở trong zone **liên tục** ít nhất `enter_threshold` frames (mặc định: 1 frame).
- Điều này ngăn chặn flickering (nhấp nháy) khi detection dao động ở biên zone.

**Kết quả nếu không đạt:** `confirmed_curr_in_zone = False`, không tạo entry event.

---

## Điều Kiện 6: Trước Đó Phải Ở Ngoài Zone (State Transition)

**Vị trí:** `src/modules/counter/zone_counter.py:558, 620`

```python
# Get previous zone state (confirmed state, not raw)
prev_confirmed_in_zone = self.track_zone_state.get(track_id, {}).get(zone_id, False)

# Detect ENTER: must be outside before, now inside
if not prev_confirmed_in_zone and confirmed_curr_in_zone:
```

**Điều kiện:**
- `prev_confirmed_in_zone` phải là `False` (trước đó ở ngoài zone).
- `confirmed_curr_in_zone` phải là `True` (hiện tại ở trong zone).

**Kết quả nếu không đạt:** Không tạo entry event (có thể đã ở trong zone từ trước).

---

## Điều Kiện 7: Chưa Được Đếm Entry Cho Track/Zone Này

**Vị trí:** `src/modules/counter/zone_counter.py:617, 622`

```python
# Get last counted event for this track/zone
last_counted = self.track_zone_counted[track_id][zone_id]

# Only count if we haven't already counted this enter event
if last_counted != "enter":
```

**Điều kiện:** 
- `last_counted` phải khác `"enter"` (có thể là `None`, `"exit"`, hoặc chưa được set).

**Kết quả nếu không đạt:** Không tạo entry event (đã đếm rồi, tránh duplicate).

---

## Điều Kiện 8: Có `person_id` Hoặc Không (Tùy Chọn)

**Vị trí:** `src/modules/counter/daily_person_counter.py:84-115, 136-140`

```python
# Try to get person_id from detection (if already resolved)
person_id = det.get("person_id")

# If not available, try to resolve using identity manager
if person_id is None:
    embedding = det.get("reid_embedding")
    if embedding is not None:
        person_id = self.identity_manager.get_or_assign_person_id(...)

# Later in event filtering:
if person_id is None:
    # Allow event without person_id (no daily uniqueness applied)
    event["person_id"] = None
    filtered_events.append(event)  # ✅ Vẫn được ghi nhận
    continue
```

**Điều kiện:** 
- **Hiện tại:** Event vẫn được ghi nhận ngay cả khi `person_id = None`.
- `person_id` được resolve từ Re-ID embedding nếu có.

**Kết quả nếu `person_id = None`:**
- ✅ Event vẫn được ghi vào database.
- ❌ Không áp dụng daily count constraint (mỗi người chỉ đếm 1 lần/ngày).

---

## Điều Kiện 9: Daily Count Check (Nếu Có `person_id`)

**Vị trí:** `src/modules/counter/daily_person_counter.py:142-167`

```python
# Check daily count constraint
can_count, current_counts = self.identity_manager.check_daily_count(
    person_id=person_id,
    zone_id=zone_id,
    event_type=event_type,
)

if can_count:
    # ✅ Add event
    event["person_id"] = person_id
    filtered_events.append(event)
else:
    # ❌ Skip (already counted today)
    logger.debug("Skipping %s for person %s...", event_type, person_id)
```

**Vị trí chi tiết:** `src/modules/counter/person_identity_manager.py:311-319`

```python
# Check if already counted this event type today globally
if global_counts.get(event_type, 0) >= 1:
    return (False, global_counts.copy())  # ❌ Đã đếm rồi

# Increment global count (mark as counted globally)
global_counts[event_type] = 1
return (True, global_counts.copy())  # ✅ Chưa đếm, cho phép đếm
```

**Điều kiện:**
- Person này **chưa được đếm** event type này (`"enter"`) trong ngày hôm nay.
- Daily count được lưu trong Redis với key: `person:counter:global:{person_id}:{date}`.

**Kết quả nếu không đạt:** Event bị skip, không ghi vào database (đã đếm rồi trong ngày).

**Lưu ý:** Daily count là **global** (toàn hệ thống), không phải per-zone. Một người chỉ được đếm 1 lần enter và 1 lần exit mỗi ngày, bất kể zone nào.

---

## Điều Kiện 10: Database Storage

**Vị trí:** `src/scripts/process_live_camera.py` (trong `_process_frame`)

```python
# Store counter events to database
if self.db_manager and len(counter_result.get("events", [])) > 0:
    for event in counter_result["events"]:
        logger.info(
            "DB: insert counter_event ch=%s zone=%s evt=%s pid=%s tid=%s frame=%s",
            str(self.channel_id),
            str(event.get("zone_id")),
            str(event.get("type")),
            str(event.get("person_id")),
            str(event.get("track_id")),
            str(frame_num),
        )
        self.db_manager.insert_counter_event(...)
```

**Điều kiện:**
- `db_manager` phải được khởi tạo (`db_enable = True`).
- Phải có ít nhất 1 event trong `counter_result["events"]`.

**Kết quả nếu không đạt:** Event không được lưu vào database.

---

## Tóm Tắt Các Điều Kiện Bắt Buộc

Để một **entry event** được ghi nhận vào database, **TẤT CẢ** các điều kiện sau phải được thỏa mãn:

1. ✅ Detection có `track_id` hợp lệ
2. ✅ Detection có centroid hợp lệ (bbox hợp lệ)
3. ✅ **Không phải staff** (`is_staff != True` và `person_type != "staff"`)
4. ✅ Centroid nằm trong zone (polygon) hoặc vượt qua line
5. ✅ Đạt ngưỡng `enter_threshold` frames liên tục trong zone
6. ✅ Trước đó ở ngoài zone (`prev_confirmed_in_zone = False`)
7. ✅ Chưa được đếm entry cho track/zone này (`last_counted != "enter"`)
8. ✅ (Nếu có `person_id`) Chưa được đếm entry trong ngày hôm nay (daily count check)
9. ✅ Database được enable và hoạt động

---

## Điều Kiện Tùy Chọn

- **`person_id`:** Không bắt buộc. Nếu `None`, event vẫn được ghi nhưng không áp dụng daily count constraint.

---

## Các Trường Hợp Đặc Biệt

### 1. Track Disappear và Reappear (Position Matching)

**Vị trí:** `src/modules/counter/zone_counter.py:472-537`

Nếu một track biến mất và xuất hiện lại ở vị trí gần (trong vòng 10 frames và khoảng cách < 100px), hệ thống sẽ:
- Match track mới với track cũ.
- **Transfer zone state** từ track cũ sang track mới.
- Giữ nguyên `track_zone_counted` để tránh đếm lại.

**Kết quả:** Nếu track cũ đã đếm entry, track mới sẽ không đếm lại.

### 2. Multiple Zones

Mỗi zone được xử lý độc lập. Một track có thể:
- Vào zone 1 → tạo entry event cho zone 1.
- Vào zone 2 → tạo entry event cho zone 2 (nếu thỏa mãn điều kiện).

### 3. Daily Count là Global

**Quan trọng:** Daily count check sử dụng **global counter** (toàn hệ thống), không phải per-zone.

- Một người vào zone 1 → đếm 1 lần enter.
- Cùng người đó vào zone 2 → **không đếm** (đã đếm enter rồi trong ngày).

Điều này đảm bảo mỗi người chỉ được đếm 1 lần enter và 1 lần exit mỗi ngày, bất kể zone nào.

---

## Logging và Debugging

### Logs Quan Trọng

1. **Zone Entry:**
   ```
   Track {track_id} entered zone {zone_id} ({zone_name})
   ```

2. **Daily Count:**
   ```
   Daily count: person {person_id} enter zone {zone_id} (daily totals: enter={count}, exit={count})
   ```

3. **Skip Event (Already Counted):**
   ```
   Skipping enter for person {person_id} in zone {zone_id} (already counted today: enter={count}, exit={count})
   ```

4. **Database Insert:**
   ```
   DB: insert counter_event ch={channel_id} zone={zone_id} evt={type} pid={person_id} tid={track_id} frame={frame_num}
   ```

### Cách Kiểm Tra

1. Xem logs để theo dõi flow từ detection → zone → daily count → DB.
2. Kiểm tra database: `SELECT * FROM counter_events WHERE event_type = 'enter' ORDER BY occurred_at DESC;`
3. Kiểm tra Redis để xem daily counts: `KEYS person:counter:global:*`

---

## Kết Luận

Logic ghi nhận entry event được thiết kế để:
- ✅ Chỉ đếm khách hàng (loại bỏ staff).
- ✅ Tránh duplicate counting (per-track và daily).
- ✅ Xử lý flickering và track discontinuity.
- ✅ Hỗ trợ multiple zones.
- ✅ Đảm bảo mỗi người chỉ đếm 1 lần/ngày (global).

Nếu một entry event không được ghi nhận, hãy kiểm tra từng điều kiện trên để xác định nguyên nhân.

