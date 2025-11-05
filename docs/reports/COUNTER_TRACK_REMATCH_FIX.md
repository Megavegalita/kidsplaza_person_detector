# Fix Đếm Lặp Khi Track Re-detection Ở Biên Zone

## 🐛 Vấn Đề

**Symptom**: Khi một người đứng ở biên zone và track_id thay đổi do re-detection (tracker assign lại ID), hệ thống đếm vào/ra nhiều lần.

**Nguyên nhân**:
1. Track cũ (track_id=1) ở biên zone → tracker mất track → đếm exit
2. Cùng người đó được detect lại với track_id mới (track_id=2) ở gần vị trí đó
3. Track mới được coi như người mới → đếm enter
4. Kết quả: 1 người → đếm nhiều lần in/out

**Scenario**:
```
Frame 10: Track 1 ở biên zone (inside zone)
Frame 11: Track 1 biến mất (tracker lost)
  → Exit count++

Frame 12: Track 2 xuất hiện ở gần vị trí Track 1 (cùng người)
  → Enter count++ (sai - đây là cùng người!)
```

## ✅ Giải Pháp: Position-Based Matching

### 1. Track Disappeared Tracks

Khi track biến mất, lưu thông tin:
```python
self.disappeared_tracks[stale_track_id] = {
    "position": centroid,  # Vị trí cuối cùng
    "frame": frame_num,    # Frame biến mất
    "zone_states": {...},   # Zone states
    "zone_counted": {...},  # Counted flags
    "zone_frame_count": {...}  # Frame counts
}
```

### 2. Match New Tracks với Disappeared Tracks

Khi track mới xuất hiện, tìm match:
```python
# Tìm track cũ gần nhất trong threshold
distance = sqrt((new_x - stale_x)² + (new_y - stale_y)²)

if distance < threshold (100px) and frame_diff <= 10:
    # Match found - transfer state
```

### 3. Transfer State

Nếu match được tìm thấy:
```python
# Chuyển state từ track cũ sang track mới
self.track_zone_state[new_track_id] = stale_info["zone_states"]
self.track_zone_counted[new_track_id] = stale_info["zone_counted"]
self.track_zone_frame_count[new_track_id] = stale_info["zone_frame_count"]
```

**Kết quả**: Track mới kế thừa state của track cũ → không đếm lại

### 4. Exit Count Chỉ Cho Unmatched Tracks

Chỉ đếm exit cho tracks:
- Biến mất
- VÀ không được match với track mới nào

```python
if stale_track_id not in matched_stale_ids:
    # Chỉ đếm exit nếu không match
    self.zone_counts[zone_id]["exit"] += 1
```

## 📊 Logic Flow Mới

```
Frame 10:
  Track 1 ở biên zone (inside)
  → State: {zone_1: True}, Counted: {zone_1: "enter"}

Frame 11:
  Track 1 biến mất
  → Lưu vào disappeared_tracks: {position, states, counted}
  
Frame 12:
  Track 2 xuất hiện ở (x+5, y+3) - gần vị trí Track 1
  → Match: distance = 5.8px < 100px threshold
  → Transfer state từ Track 1 → Track 2
  → Track 2: {zone_1: True}, Counted: {zone_1: "enter"}
  → KHÔNG đếm enter (vì đã counted)
  
Frame 13:
  Track 2 vẫn ở trong zone
  → Không đếm gì (vì đã counted)
```

## ⚙️ Parameters

- **`_position_match_threshold`**: 100 pixels (default)
  - Khoảng cách tối đa để match tracks
  - Có thể config trong zone hoặc counter init

- **Frame window**: 10 frames
  - Chỉ match tracks biến mất trong 10 frames gần nhất

- **Cleanup**: 30 frames
  - Xóa disappeared tracks sau 30 frames

## 🎯 Kết Quả

### Trước Fix:
- Track re-detection → đếm enter lại
- 1 người ở biên zone → có thể đếm 3-5 lần

### Sau Fix:
- Track re-detection được match → transfer state
- Không đếm lại nếu cùng người
- Chỉ đếm exit nếu track thực sự biến mất (không match)

## 🔍 Logging

Khi match được tìm thấy:
```
INFO - Matched new track 2 with disappeared track 1 
       (distance: 5.8px, frame_diff: 1)
```

## ✅ Test Cases

1. ✅ Track biến mất và xuất hiện lại ở gần → Match và transfer state
2. ✅ Track biến mất và không xuất hiện lại → Count exit
3. ✅ Track biến mất và xuất hiện lại ở xa (>100px) → Không match, count exit
4. ✅ Multiple tracks biến mất cùng lúc → Match correctly per track

## 📝 Code Changes

1. Thêm `disappeared_tracks` dictionary
2. Store disappeared track info khi track biến mất
3. Match logic: Find closest disappeared track
4. Transfer state: Copy zone states, counted flags, frame counts
5. Exit count: Chỉ cho unmatched tracks

## ⚠️ Limitations

1. **Distance Threshold**: 100px có thể không đủ cho các trường hợp:
   - Người di chuyển nhanh
   - Resolution cao → 100px có thể nhỏ
   - **Giải pháp**: Có thể config threshold hoặc dùng percentage

2. **Frame Window**: 10 frames có thể không đủ nếu FPS thấp
   - **Giải pháp**: Có thể tăng window hoặc tính theo time (seconds)

3. **Multiple Matches**: Nếu nhiều tracks biến mất gần nhau, có thể match sai
   - **Giải pháp hiện tại**: Match với closest track
   - **Có thể cải thiện**: Sử dụng Re-ID embeddings

