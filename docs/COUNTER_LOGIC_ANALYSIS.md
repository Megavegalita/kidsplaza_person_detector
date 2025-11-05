# Phân Tích Logic Đếm Người (Counter Logic Analysis)

## 📋 Tổng Quan

Module `ZoneCounter` sử dụng zone-based counting để đếm người vào/ra các vùng được định nghĩa.

## 🔍 Logic Đếm Chi Tiết

### 1. Cấu Trúc Dữ Liệu

#### 1.1 State Tracking
```python
self.track_positions: Dict[int, Dict[str, Tuple[float, float]]]
# Lưu vị trí centroid của mỗi track_id
# Key: track_id, Value: {"centroid": (x, y)}

self.track_zone_state: Dict[int, Dict[str, bool]]
# Lưu trạng thái trong zone của mỗi track
# Key: track_id, Value: {zone_id: True/False}
```

#### 1.2 Counts
```python
self.zone_counts: Dict[str, Dict[str, int]]
# Key: zone_id, Value: {"enter": int, "exit": int, "total": int}
```

### 2. Quy Trình Đếm (Counting Flow)

#### 2.1 Khởi Tạo (Initialization)
1. Parse và validate zone configs từ JSON
2. Convert percentage coordinates sang absolute (nếu cần)
3. Initialize `zone_counts` cho mỗi zone: `{"enter": 0, "exit": 0, "total": 0}`

#### 2.2 Cập Nhật (Update Process)

**Bước 1: Cập nhật frame size**
```python
if frame is not None:
    frame_height, frame_width = frame.shape[:2]
    self._frame_size = (frame_width, frame_height)
```
- Lưu frame size để convert percentage coordinates

**Bước 2: Xử lý từng detection**
```python
for detection in detections:
    track_id = detection.get("track_id")
    centroid = self._get_track_centroid(detection)  # Lấy tâm bbox
```

**Bước 3: Lấy vị trí trước đó**
```python
prev_centroid = self.track_positions.get(track_id, {}).get("centroid")
prev_centroid = prev_centroid or centroid  # Fallback nếu không có history
```

**Bước 4: Kiểm tra mỗi zone**
```python
for zone in self.zones:
    prev_in_zone = self.track_zone_state.get(track_id, {}).get(zone_id, False)
    
    # Check current state
    if zone_type == "polygon":
        curr_in_zone = self._check_zone_polygon(centroid, zone, frame_width, frame_height)
    elif zone_type == "line":
        curr_in_zone = self._check_zone_line(prev_centroid, centroid, zone, frame_width, frame_height)
```

**Bước 5: Phát hiện thay đổi trạng thái**
```python
if not prev_in_zone and curr_in_zone:
    # ENTER: từ ngoài vào trong
    self.zone_counts[zone_id]["enter"] += 1
    self.zone_counts[zone_id]["total"] += 1
    
elif prev_in_zone and not curr_in_zone:
    # EXIT: từ trong ra ngoài
    self.zone_counts[zone_id]["exit"] += 1
    self.zone_counts[zone_id]["total"] -= 1
```

**Bước 6: Cập nhật state**
```python
self.track_zone_state[track_id][zone_id] = curr_in_zone
self.track_positions[track_id]["centroid"] = centroid
```

### 3. Zone Detection Algorithms

#### 3.1 Polygon Zone Detection
**Algorithm**: Ray Casting (Point-in-Polygon)

```python
def point_in_polygon(point, polygon):
    # Vẽ một đường ngang từ point sang phải
    # Đếm số lần cắt cạnh polygon
    # Nếu số lẻ → bên trong, số chẵn → bên ngoài
```

**Logic**:
- Kiểm tra centroid của track có nằm trong polygon không
- Sử dụng cho bidirectional counting (cả vào và ra)

#### 3.2 Line Zone Detection
**Algorithm**: Cross Product (Line Crossing)

```python
def line_crossing(prev_point, curr_point, line_start, line_end, side):
    # Tính cross product để xác định phía của điểm so với line
    # Phát hiện khi điểm di chuyển từ một phía sang phía kia
```

**Logic**:
- So sánh vị trí trước và hiện tại
- Phát hiện khi track crosses line từ `side` (above/below/left/right)
- Sử dụng cho one-way counting

### 4. State Management

#### 4.1 Track Position History
```python
self.track_positions[track_id] = {"centroid": (x, y)}
```
- Lưu centroid của track để:
  - So sánh với vị trí hiện tại (line crossing)
  - Fallback nếu không có history (dùng current position)

#### 4.2 Zone State Tracking
```python
self.track_zone_state[track_id][zone_id] = True/False
```
- Lưu trạng thái trước đó của track trong zone
- Dùng để phát hiện state change:
  - `False → True`: Enter
  - `True → False`: Exit

#### 4.3 Stale Track Cleanup
```python
stale_tracks = set(self.track_positions.keys()) - current_track_ids
for track_id in stale_tracks:
    # Mark zones as exited if track was in zone
    if self.track_zone_state.get(track_id, {}).get(zone_id, False):
        self.track_zone_state[track_id][zone_id] = False
```
- Xử lý khi track biến mất (không còn trong detections)
- Đánh dấu exit nếu track đang ở trong zone
- Giữ lại position history (có thể track xuất hiện lại)

### 5. Count Calculation

#### 5.1 Enter Count
- Tăng khi: `prev_in_zone = False` và `curr_in_zone = True`
- Tăng `total` cùng lúc

#### 5.2 Exit Count
- Tăng khi: `prev_in_zone = True` và `curr_in_zone = False`
- Giảm `total` cùng lúc

#### 5.3 Total Count
```python
total = enter - exit
```
- **Không phải** số người hiện tại trong zone
- Là số chênh lệch (net count)
- Có thể âm nếu exit > enter

### 6. Edge Cases & Special Behaviors

#### 6.1 First Frame
- `prev_centroid = None` → dùng `centroid` làm fallback
- `prev_in_zone = False` (default)

#### 6.2 Track Re-appearance
- Vị trí history được giữ lại
- Nếu track xuất hiện lại, có thể dùng history để detect crossing

#### 6.3 Multiple Zones
- Mỗi track có thể ở nhiều zones cùng lúc
- State tracking độc lập cho mỗi zone

#### 6.4 No Detections
- Không có detections → không có state change
- Counts giữ nguyên
- Stale tracks được cleanup

### 7. Potential Issues & Considerations

#### 7.1 Flickering
**Vấn đề**: Track ở biên zone có thể flicker (vào/ra liên tục)

**Giải pháp hiện tại**: Chưa có threshold
- Có thể thêm: `enter_threshold`, `exit_threshold` (đã có trong config nhưng chưa dùng)
- Yêu cầu: Phải ở trong zone ≥ N frames mới tính enter

#### 7.2 Total Count Accuracy
**Vấn đề**: `total = enter - exit` không phải số người hiện tại

**Giải pháp**: 
- Nếu cần số người hiện tại: Đếm số tracks có `track_zone_state[track_id][zone_id] = True`
- Hoặc thêm counter riêng: `current_count`

#### 7.3 Line Zone Direction
**Hiện tại**: Chỉ detect crossing từ một phía (`side`)
- Không phân biệt direction (vào/ra)
- Cả hai hướng đều tăng `enter`

**Cải thiện có thể**: 
- Thêm direction detection dựa vào movement vector
- Phân biệt enter/exit cho line zones

### 8. Code Flow Summary

```
update(detections, frame)
├── Update frame_size (for percentage conversion)
├── For each detection:
│   ├── Get track_id and centroid
│   ├── Get prev_centroid (or use current as fallback)
│   ├── For each zone:
│   │   ├── Get prev_in_zone state
│   │   ├── Check curr_in_zone (polygon/line detection)
│   │   ├── Detect state change:
│   │   │   ├── False → True: Enter (increment enter, total)
│   │   │   └── True → False: Exit (increment exit, decrement total)
│   │   └── Update state: track_zone_state[track_id][zone_id] = curr_in_zone
│   └── Update position: track_positions[track_id]["centroid"] = centroid
├── Cleanup stale tracks (mark as exited if was in zone)
└── Return: {counts, events, active_tracks}
```

## 📊 Visualization

### Enter Event
```
Frame N:     track outside zone (prev_in_zone = False)
Frame N+1:   track inside zone  (curr_in_zone = True)
→ ENTER event triggered
→ enter++, total++
```

### Exit Event
```
Frame N:     track inside zone  (prev_in_zone = True)
Frame N+1:   track outside zone (curr_in_zone = False)
→ EXIT event triggered
→ exit++, total--
```

## 🎯 Recommendations

1. **Thêm Current Count**: Đếm số tracks hiện tại trong zone
2. **Flickering Prevention**: Implement threshold mechanism
3. **Line Zone Direction**: Phân biệt enter/exit cho line zones
4. **Metrics**: Thêm dwell time, peak times per zone
5. **Validation**: Validate zone configuration (points order, line direction)

## ⚠️ Lưu Ý Quan Trọng

### 1. Total Count Không Phải Số Người Hiện Tại
```python
total = enter - exit  # Đây là net count (số chênh lệch)
```

**Ví dụ**:
- Enter = 10, Exit = 5 → Total = 5
- Nhưng có thể có 3 người đang ở trong zone
- Total chỉ cho biết có 5 người "nhiều hơn" vào so với ra

### 2. Không Có Flickering Protection
- Nếu track ở biên zone, có thể flicker (vào/ra liên tục)
- Mỗi flicker sẽ tăng enter/exit count
- **Giải pháp**: Cần implement threshold (enter_threshold, exit_threshold)

### 3. Line Zone Chỉ Detect Một Hướng
- Chỉ detect crossing từ một phía (`side`)
- Cả hai hướng đều tính là enter
- Không phân biệt được vào/ra dựa trên direction

### 4. Stale Track Cleanup
- Khi track biến mất, đánh dấu exit
- Nhưng không tăng exit count (chỉ update state)
- Có thể gây mất đồng bộ nếu track biến mất khi đang trong zone

## 📝 Ví Dụ Minh Họa

### Scenario 1: Normal Enter/Exit
```
Frame 1: Track 1 outside zone (prev_in_zone=False)
Frame 2: Track 1 inside zone  (curr_in_zone=True)
→ ENTER: enter=1, total=1

Frame 10: Track 1 inside zone  (prev_in_zone=True)
Frame 11: Track 1 outside zone (curr_in_zone=False)
→ EXIT: exit=1, total=0
```

### Scenario 2: Flickering
```
Frame 1:  Track 1 outside (prev=False)
Frame 2:  Track 1 inside  (curr=True)  → ENTER: enter=1
Frame 3:  Track 1 outside (curr=False) → EXIT: exit=1
Frame 4:  Track 1 inside  (curr=True)  → ENTER: enter=2
Frame 5:  Track 1 outside (curr=False) → EXIT: exit=2
...
→ Counts tăng nhanh do flickering
```

### Scenario 3: Track Disappears
```
Frame 10: Track 1 inside zone (state=True)
Frame 11: Track 1 không còn trong detections (biến mất)
→ Cleanup: Mark state=False (không tăng exit count)
→ Vấn đề: Track đang ở trong zone nhưng không được đếm exit
```

