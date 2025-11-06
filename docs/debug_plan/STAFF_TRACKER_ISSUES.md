# Phân tích vấn đề: Tracker không liên tục và không phát hiện staff

## 🔍 Vấn đề phát hiện được:

### 1. Staff Classification không chạy
- **Nguyên nhân:** Staff classification chỉ chạy khi `should_detect=True` VÀ có detections VÀ detections có `track_id`
- **Vấn đề:** Logs chỉ có DEBUG level, không hiển thị trong INFO log
- **Giải pháp:** Cần thêm INFO logs để track staff classification

### 2. Tracker không liên tục
- **Nguyên nhân:** 
  - `detect_every_n=1` cho channel 4 (từ config)
  - Nhưng có thể detections bị filter trước khi vào tracker
  - Hoặc tracker không được update đúng cách

### 3. Logic workflow có vấn đề
- Staff classification chỉ chạy khi `should_detect=True`
- Nhưng `should_detect` chỉ True khi `frame_num % detect_every_n == 0`
- Với `detect_every_n=1`, `should_detect` luôn True
- Nhưng có thể detections không có `track_id` sau tracking

## 🔧 Cần sửa:

1. **Thêm INFO logs cho staff classification** để debug
2. **Kiểm tra detections có track_id không** sau tracking
3. **Đảm bảo staff classification chạy trên mọi frame có detections** (không chỉ khi should_detect)
4. **Kiểm tra tracker update logic**

