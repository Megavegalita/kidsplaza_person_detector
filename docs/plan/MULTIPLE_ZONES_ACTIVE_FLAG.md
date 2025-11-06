# Multiple Counter Zones with Active Flag

## Overview
Hệ thống hỗ trợ multiple counter zones với khả năng bật/tắt từng zone thông qua flag `active` trong config. Mỗi channel có thể có nhiều zones (polygon hoặc line), và chỉ các zones có `active: true` mới được sử dụng để đếm.

## Feature Description

### Active Flag
- Mỗi zone có thể có field `active` (boolean)
- Default: `true` nếu không được chỉ định
- Chỉ các zones có `active: true` mới được load và sử dụng
- Zones có `active: false` sẽ bị bỏ qua hoàn toàn

### Multiple Zones Support
- Mỗi channel có thể có nhiều zones cùng lúc
- Hỗ trợ cả polygon zones và line zones
- Mỗi zone có counter riêng và events riêng
- Events được ghi nhận với `zone_id` để phân biệt

## Configuration

### Example Config
```json
{
  "counter": {
    "enabled": true,
    "zones": [
      {
        "zone_id": "zone_1",
        "name": "Left Bottom Zone",
        "type": "polygon",
        "coordinate_type": "percentage",
        "points": [[0, 30], [50, 30], [50, 100], [0, 100]],
        "enter_threshold": 2,
        "exit_threshold": 2,
        "direction": "bidirectional",
        "active": false,
        "comment": "Inactive zone for testing"
      },
      {
        "zone_id": "line_entrance",
        "name": "Entrance Line",
        "type": "line",
        "coordinate_type": "percentage",
        "start_point": [10, 50],
        "end_point": [90, 50],
        "direction": "top_to_bottom",
        "enter_threshold": 1,
        "exit_threshold": 1,
        "active": true,
        "comment": "Active entrance line"
      }
    ]
  }
}
```

## Implementation Details

### Code Changes

**File: `src/scripts/process_live_camera.py`**
- Filter zones khi load từ config: chỉ lấy zones có `active: true`
- Log số lượng active zones và zone IDs
- Pass only active zones vào `ZoneCounter`

**File: `src/modules/counter/zone_counter.py`**
- Đã hỗ trợ multiple zones từ trước
- Mỗi zone được track độc lập
- Events được ghi nhận với `zone_id`

**File: `src/scripts/test_multiple_zones_video.py`**
- Script test mới để test multiple zones với video
- Load zones từ config và filter theo active flag
- Vẽ tất cả active zones lên video output

## Usage

### Enable/Disable Zones
Để bật/tắt một zone, chỉ cần thay đổi field `active` trong config:

```json
{
  "zone_id": "zone_1",
  "active": false,  // Set false để disable
  ...
}
```

### View Active Zones
Khi start camera processing, log sẽ hiển thị:
```
Counter enabled for channel 4 with 2 active zones (out of 3 total)
Active zone IDs: line_entrance, line_exit
```

## Benefits

1. **Flexibility**: Dễ dàng bật/tắt zones mà không cần xóa config
2. **Testing**: Có thể test nhiều zones và chỉ enable những zones cần thiết
3. **Maintenance**: Giữ lại config của các zones không dùng để dễ dàng enable lại sau
4. **Multiple Zones**: Hỗ trợ nhiều zones cùng lúc cho các use case phức tạp

## Testing

### Test Script
```bash
python src/scripts/test_multiple_zones_video.py \
  input/video/test.mp4 \
  --channel-id 4 \
  --max-seconds 60 \
  --output-video output/videos/test_multiple_zones.mp4
```

### Expected Output
- Video với tất cả active zones được vẽ
- Counter info cho mỗi zone
- Events log cho mỗi zone với zone_id

## Related Features

- **Line Direction Counter**: Hỗ trợ direction-based line crossing
- **Polygon Zones**: Hỗ trợ polygon zones với bidirectional counting
- **Database Storage**: Events được lưu với zone_id để phân biệt

## Files Modified

- `src/scripts/process_live_camera.py` - Zone filtering logic
- `src/scripts/test_multiple_zones_video.py` - Test script
- `input/cameras_config/kidsplaza_thanhxuan.json` - Example config
- `docs/plan/MULTIPLE_ZONES_ACTIVE_FLAG.md` - This document

