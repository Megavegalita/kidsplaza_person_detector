# Channel 4 Staff Detection Test - Quick Start Guide

## 🚀 Quick Start

### 1. Start Test (with Display)
```bash
./scripts/test_channel4_staff.sh
```

Hoặc chạy trực tiếp:
```bash
python3 src/scripts/process_live_camera.py \
    --config input/cameras_config/kidsplaza_thanhxuan.json \
    --channel-id 4 \
    --display \
    --display-fps 15.0 \
    --log-level INFO
```

### 2. Monitor Logs (in another terminal)
```bash
./scripts/monitor_channel4.sh
```

Hoặc tail trực tiếp:
```bash
tail -f logs/channel_4_staff_test_*.log | grep -E "Staff|Voting|Filtering|Counter"
```

### 3. Analyze Log (after test)
```bash
python3 scripts/analyze_staff_log.py logs/channel_4_staff_test_*.log
```

---

## 📊 What to Monitor

### In Display Window:
- ✅ **Red boxes** = Staff (không đếm)
- ✅ **Green boxes** = Customer (đếm vào/ra)
- ✅ **Zone overlay** = Global In/Out/Unique counts (chỉ customers)
- ✅ **PID labels** = Person ID (chỉ customers)

### In Logs:
- `Staff classification` = Classification events
- `fixed as STAFF/CUSTOMER` = Voting completed
- `voting` = Still accumulating votes
- `Staff filtering` = Filter stats (staff vs customer counts)
- `Counter event` = Enter/exit events (chỉ customers)

---

## 🔍 Expected Behavior

1. **Staff Detection:**
   - Classify mỗi khi detect person
   - Vote với confidence weighting
   - Fix classification sau 4 votes hoặc 10 frames

2. **Filtering:**
   - Staff được filter trước Re-ID
   - Staff được filter trước Counter
   - Staff được filter trước Database

3. **Display:**
   - Staff: Red boxes, không có PID
   - Customer: Green boxes, có PID nếu có

4. **Counter:**
   - Chỉ đếm customers
   - Global In/Out/Unique chỉ tính customers

---

## 📝 Log Analysis

Sau khi test, chạy analyzer để xem:
- Tổng số frames processed
- Số lần classification
- Voting behavior (staff vs customer)
- Filtering stats
- Counter events
- Errors (nếu có)

---

## ⚠️ Troubleshooting

### Display không mở:
- Kiểm tra X11 forwarding (nếu SSH)
- Kiểm tra DISPLAY variable
- Thử `--display-fps 10.0` (thấp hơn)

### Không detect staff:
- Kiểm tra model path: `models/kidsplaza/best.pt`
- Kiểm tra config: `staff_detection.enabled = true`
- Kiểm tra threshold: `conf_threshold = 0.4`

### Log không có:
- Kiểm tra quyền ghi trong `logs/` directory
- Kiểm tra disk space

