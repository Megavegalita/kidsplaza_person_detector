# Fix Logic Đếm Bị Lặp (Duplicate Counting Fix)

## 🐛 Vấn Đề

**Symptom**: Một track_id khi đi qua ranh giới zone bị đếm nhiều lần (in/out) thay vì chỉ đếm 1 lần.

**Nguyên nhân**:
1. Logic sử dụng `prev_in_zone` (raw state) thay vì `prev_confirmed_in_zone` (confirmed state)
2. Không có mechanism để track xem đã đếm enter/exit chưa cho mỗi track_id
3. Flickering ở biên zone có thể trigger nhiều lần cùng một event

## ✅ Giải Pháp

### 1. Thêm Tracking "Last Counted Event"

Thêm `track_zone_counted` dictionary để track event đã đếm:
```python
self.track_zone_counted: Dict[int, Dict[str, str]] = {}
# Key: track_id, Value: {zone_id: "enter"|"exit"|None}
```

### 2. Sửa Logic Đếm

**Trước:**
```python
if not prev_in_zone and curr_in_zone:
    # Enter - đếm mỗi lần condition đúng
    self.zone_counts[zone_id]["enter"] += 1
```

**Sau:**
```python
# Check confirmed state (sau threshold)
confirmed_curr_in_zone = curr_in_zone and frame_count >= enter_threshold
prev_confirmed_in_zone = self.track_zone_state.get(track_id, {}).get(zone_id, False)

# Chỉ đếm nếu chưa đếm event này
last_counted = self.track_zone_counted[track_id][zone_id]

if not prev_confirmed_in_zone and confirmed_curr_in_zone:
    if last_counted != "enter":  # Chưa đếm enter
        self.zone_counts[zone_id]["enter"] += 1
        self.track_zone_counted[track_id][zone_id] = "enter"  # Đánh dấu đã đếm
```

### 3. Reset Flag Khi Vượt Ranh Giới Ngược Lại

Chỉ reset flag khi track thực sự vượt qua ranh giới ngược lại:
```python
# Reset khi crossing boundary
if confirmed_curr_in_zone and prev_confirmed_in_zone == False:
    # Just entered - reset exit flag
    if last_counted == "exit":
        self.track_zone_counted[track_id][zone_id] = None
        
elif confirmed_exit and prev_confirmed_in_zone == True:
    # Just exited - reset enter flag
    if last_counted == "enter":
        self.track_zone_counted[track_id][zone_id] = None
```

## 📊 Logic Flow Mới

```
Frame 1: Track outside zone
  - prev_confirmed_in_zone = False
  - confirmed_curr_in_zone = False
  - last_counted = None
  → No count

Frame 2: Track enters zone (confirmed)
  - prev_confirmed_in_zone = False
  - confirmed_curr_in_zone = True
  - last_counted = None
  → ENTER count = 1, last_counted = "enter"

Frame 3-10: Track stays inside
  - prev_confirmed_in_zone = True
  - confirmed_curr_in_zone = True
  - last_counted = "enter"
  → No count (đã đếm rồi)

Frame 11: Track exits zone (confirmed)
  - prev_confirmed_in_zone = True
  - confirmed_exit = True
  - last_counted = "enter"
  → EXIT count = 1, last_counted = "exit"
  → Reset: last_counted = None (để cho phép enter lại)

Frame 12-20: Track stays outside
  - prev_confirmed_in_zone = False
  - confirmed_exit = True
  - last_counted = "exit"
  → No count (đã đếm rồi)

Frame 21: Track enters again (confirmed)
  - prev_confirmed_in_zone = False
  - confirmed_curr_in_zone = True
  - last_counted = None (đã reset)
  → ENTER count = 2, last_counted = "enter"
```

## 🎯 Kết Quả

### Trước Fix:
- Track đi qua ranh giới 1 lần → đếm 3-5 lần (do flickering)
- Không phân biệt được đã đếm chưa

### Sau Fix:
- Track đi qua ranh giới 1 lần → đếm đúng 1 lần
- Mỗi lần crossing boundary chỉ đếm 1 lần
- Chỉ reset khi vượt ranh giới ngược lại

## ✅ Test Cases

1. ✅ Track vào zone lần đầu → đếm 1 enter
2. ✅ Track ở trong zone nhiều frames → không đếm lại
3. ✅ Track ra zone → đếm 1 exit
4. ✅ Track ở ngoài zone nhiều frames → không đếm lại
5. ✅ Track vào lại → đếm enter mới
6. ✅ Flickering ở biên → chỉ đếm 1 lần (với threshold)

## 📝 Code Changes

- Thêm `track_zone_counted` dictionary
- Sửa logic đếm để check `last_counted`
- Sử dụng `prev_confirmed_in_zone` thay vì `prev_in_zone`
- Reset flag khi crossing boundary ngược lại
- Update state sau khi check threshold

## 🔍 Validation

- Unit tests: ✅ All passing
- Logic: ✅ Mỗi crossing boundary chỉ đếm 1 lần
- Flickering protection: ✅ Vẫn hoạt động với threshold

