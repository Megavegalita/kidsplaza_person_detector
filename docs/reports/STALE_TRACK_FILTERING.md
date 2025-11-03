# Stale Track Filtering - Fix False Positive Bounding Boxes

**Date**: 2025-11-03  
**Status**: ✅ Fixed

---

## 🔍 VẤN ĐỀ

### **Camera 4: Bounding Box Không Có Người Vẫn Hiển Thị**
- Không có detections mới (`detected=0 persons`)
- Nhưng vẫn có `Tracks: 1` và bounding box hiển thị
- Gender classification vẫn chạy cho track cũ
- Track này có thể là từ false positive trước đó

### **Root Cause**
```python
# _get_confirmed_tracks() - line 430-447
def _get_confirmed_tracks(self):
    for track in self.tracks:
        if track.hits >= self.min_hits:  # ✅ Check hits
            # ❌ KHÔNG check time_since_update
            confirmed_tracks.append(...)
```

**Vấn đề**:
1. Tracker.update([]) → returns `_get_confirmed_tracks()`
2. `_get_confirmed_tracks()` chỉ filter theo `hits >= min_hits`
3. **KHÔNG filter theo `time_since_update`** → Tracks cũ vẫn được return
4. Track có thể tồn tại đến 30 frames (max_age) dù không có detections mới
5. False positive từ trước vẫn hiển thị

---

## ✅ FIX

### **Filter Stale Tracks**
```python
# Before
def _get_confirmed_tracks(self):
    for track in self.tracks:
        if track.hits >= self.min_hits:
            # No time_since_update check
            confirmed_tracks.append(...)

# After
def _get_confirmed_tracks(self, max_time_since_update: Optional[int] = None):
    for track in self.tracks:
        if track.hits >= self.min_hits:
            # Filter stale tracks (only show recently updated)
            if max_time_since_update is not None and track.time_since_update > max_time_since_update:
                continue
            confirmed_tracks.append(...)

# When no detections, only show tracks updated within 10 frames (~0.4s)
if len(detections) == 0:
    return self._get_confirmed_tracks(max_time_since_update=10)
```

**Impact**:
- Chỉ hiển thị tracks có detections trong 10 frames gần nhất (~0.4 giây)
- Tracks cũ (false positives) sẽ không hiển thị sau 10 frames không có detections
- Tracks mới vẫn hiển thị liên tục khi có detections

---

## 📊 BEHAVIOR

### **When No New Detections**:
- Tracker.update([]) → `_get_confirmed_tracks(max_time_since_update=10)`
- **Chỉ return tracks với `time_since_update <= 10`**
- Tracks cũ hơn 10 frames → **KHÔNG hiển thị**

### **When New Detections Arrive**:
- Tracker.update([detections]) → Normal flow
- Tracks được update → `time_since_update = 0`
- Tracks được hiển thị bình thường

### **Track Lifecycle**:
1. New detection → Create track, `time_since_update = 0`
2. No detection → `time_since_update++` mỗi frame
3. If `time_since_update > 10` → Track không hiển thị (nhưng vẫn tồn tại trong tracker)
4. If `time_since_update > 30` (max_age) → Track bị remove khỏi tracker

---

## 🔧 IMPACT

### **Before**:
- ❌ Tracks cũ (30 frames) vẫn hiển thị dù không có detections
- ❌ False positives persist quá lâu
- ❌ Bounding boxes từ false positives vẫn hiển thị

### **After**:
- ✅ Chỉ hiển thị tracks có detections trong 10 frames gần nhất
- ✅ False positives disappear sau 10 frames (~0.4s)
- ✅ Bounding boxes chỉ hiển thị khi có detections gần đây

---

## 📝 FILES MODIFIED

1. **`src/modules/tracking/tracker.py`**:
   - Added `max_time_since_update` parameter to `_get_confirmed_tracks()`
   - Filter stale tracks khi không có detections mới
   - Limit: 10 frames (~0.4s at 24 FPS)

---

## ✅ VERIFICATION

### **Expected Behavior**:
- ✅ Camera 4: Tracks cũ sẽ disappear sau 10 frames không có detections
- ✅ Bounding boxes chỉ hiển thị khi có detections gần đây
- ✅ False positives sẽ được cleanup nhanh hơn

### **Performance**:
- Minimal overhead (chỉ thêm một check condition)
- Không ảnh hưởng đến FPS

---

**Status**: Ready for testing ✅

