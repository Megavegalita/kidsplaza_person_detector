# Phase 8: Zone Configuration Summary

**Date**: 2025-11-03  
**Status**: ✅ Zones Configured

---

## 📊 Zone Configuration by Channel

### Channel 1 & 2 (Outdoor - ben_ngoai)
**Zone Type**: Left Half of Screen  
**Resolution**: 1920x1080

```json
{
  "zone_id": "zone_1",
  "name": "Left Half",
  "type": "polygon",
  "points": [[0, 0], [960, 0], [960, 1080], [0, 1080]],
  "direction": "bidirectional"
}
```

**Description**: 
- Nửa màn hình bên trái
- Covers từ x=0 đến x=960 (half of 1920)
- Full height (y=0 đến y=1080)

---

### Channel 3 (Indoor - ben_trong_thu_ngan)
**Zone Type**: Bottom Half of Screen  
**Resolution**: 1920x1080

```json
{
  "zone_id": "zone_1",
  "name": "Bottom Half",
  "type": "polygon",
  "points": [[0, 540], [1920, 540], [1920, 1080], [0, 1080]],
  "direction": "bidirectional"
}
```

**Description**:
- Nửa màn hình dưới
- Covers từ y=540 đến y=1080 (half of 1080)
- Full width (x=0 đến x=1920)

---

### Channel 4 (Indoor - ben_trong_cua_vao)
**Zone Type**: Bottom Half of Screen  
**Resolution**: 2304x1296

```json
{
  "zone_id": "zone_1",
  "name": "Bottom Half",
  "type": "polygon",
  "points": [[0, 648], [2304, 648], [2304, 1296], [0, 1296]],
  "direction": "bidirectional"
}
```

**Description**:
- Nửa màn hình dưới
- Covers từ y=648 đến y=1296 (half of 1296)
- Full width (x=0 đến x=2304)

---

## 🎯 Zone Visual Layout

### Channel 1 & 2 (1920x1080)
```
┌─────────────────────────────────┐
│ ████████░░░░░░░░░░░░░░░░░░░░░░░ │ ← Left Half Zone
│ ████████░░░░░░░░░░░░░░░░░░░░░░░ │
│ ████████░░░░░░░░░░░░░░░░░░░░░░░ │
│ ████████░░░░░░░░░░░░░░░░░░░░░░░ │
└─────────────────────────────────┘
```

### Channel 3 (1920x1080)
```
┌─────────────────────────────────┐
│                                 │
│                                 │
├─────────────────────────────────┤
│ ███████████████████████████████ │ ← Bottom Half Zone
│ ███████████████████████████████ │
└─────────────────────────────────┘
```

### Channel 4 (2304x1296)
```
┌──────────────────────────────────────────┐
│                                          │
│                                          │
│                                          │
├──────────────────────────────────────────┤
│ ████████████████████████████████████████ │ ← Bottom Half Zone
│ ████████████████████████████████████████ │
└──────────────────────────────────────────┘
```

---

## ✅ Testing

### Start Single Channel Test

```bash
# Test Channel 1 (Left Half)
./scripts/test_single_channel.sh 1

# Test Channel 2 (Left Half)
./scripts/test_single_channel.sh 2

# Test Channel 3 (Bottom Half)
./scripts/test_single_channel.sh 3

# Test Channel 4 (Bottom Half)
./scripts/test_single_channel.sh 4
```

### Start All Channels

```bash
./scripts/start_all_channels.sh
```

### Check Status

```bash
./scripts/check_channels_status.sh
```

### Stop All Channels

```bash
./scripts/stop_all_channels.sh
```

---

## 🔍 What to Expect

### Display Overlay
- **Green polygon** covering the zone area
- **Count display**: `Left Half: In:X Out:Y Total:Z` hoặc `Bottom Half: In:X Out:Y Total:Z`
- **Real-time updates** khi có người vào/ra zone

### Counter Events
Khi có người vào/ra zone, sẽ thấy logs:
```
INFO: Counter event: enter - Zone: zone_1 (Left Half), Track: 123
INFO: Counter event: exit - Zone: zone_1 (Left Half), Track: 123
```

### Counts Tracking
- **Enter**: Tăng khi track vào zone
- **Exit**: Tăng khi track ra khỏi zone  
- **Total**: Running total (enter - exit)

---

## 📝 Notes

- Zone coordinates dựa trên frame resolution:
  - Channel 1-3: 1920x1080
  - Channel 4: 2304x1296

- Nếu camera resolution khác, cần adjust coordinates trong config file.

- Zones có thể được điều chỉnh bất kỳ lúc nào trong config file và sẽ apply sau khi restart.

---

**Status**: ✅ **ZONES CONFIGURED AND READY FOR TESTING**

