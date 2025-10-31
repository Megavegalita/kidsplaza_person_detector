## Kế Hoạch Cải Tiến Cho Các Giai Đoạn Tiếp Theo

Tài liệu tham chiếu: [Đề xuất Stack Re-ID & Phân loại Giới tính]
(https://docs.google.com/document/d/1OqQ-7W-jSMCALZICdgKIi9sedr_5d1w1aNFuoyzRc_0/edit?usp=sharing)

Bối cảnh:
- Đã hoàn thành các phase 1–3: môi trường, tích hợp camera, phát hiện người bằng YOLOv8
  tốc độ cao với MPS, xuất video có overlay và báo cáo JSON.
- Phase 4 (tracking) sẵn sàng bắt đầu; tracker dựa trên IoU đã có nền tảng và được tích hợp
  một phần tại `src/scripts/process_video_file.py` và `src/modules/tracking/tracker.py`.
- Mục tiêu tiếp theo: bổ sung Re-ID và phân loại giới tính theo tài liệu tham chiếu.

### Phase 4 — Theo Dõi Đa Đối Tượng Ổn Định (MOT)
- Mục tiêu:
  - Ổn định gán `track_id` theo thời gian; giảm lỗi đổi ID và phân mảnh track.
  - Cung cấp API tracker trả về detections kèm `track_id`; quản lý vòng đời track.
  - Lưu tối thiểu thống kê track (age, hits, last_seen) phục vụ các module sau.
- Thiết kế:
  - Giữ liên kết dựa trên IoU nhanh; bổ sung smoothing chuyển động và EMA cho bbox.
  - Ràng buộc ghép cặp bằng ngưỡng cấu hình: IoU + confidence + tương đồng tỉ lệ khung.
  - Tùy chọn: cho phép cắm ByteTrack để cải thiện recall ở cảnh đông người.
- Cột mốc:
  - M1: Refactor tracker trả về detections kèm `track_id` (đã có trong code; xác thực bằng test).
  - M2: Thêm smoothing và ngưỡng vòng đời track; mở cấu hình qua config.
  - M3: Overlay hiển thị số Tracks và `track_id` trên bbox.
- Tiêu chí nghiệm thu:
  - Tỉ lệ đổi ID <2% trên video test; không tái sử dụng ID trong 2 giây kể từ `last_seen`.
  - Báo cáo JSON có `track_id` cho tất cả detections sau khung xác nhận đầu tiên.

### Phase 5 — Re-Identification (Re-ID) và Nhân Khẩu Học (Giới tính/Tuổi)
- Mục tiêu:
  - Thêm embedding Re-ID theo từng track để giảm đổi ID khi che khuất/nhảy khung.
  - Chạy phân loại giới tính (và có thể tuổi) nhẹ trên ROI người được crop.
- Thiết kế:
  - Re-ID: Dùng backbone nhỏ, nhanh (ví dụ OSNet-x0_25 hoặc MobileNet head) với cosine
    similarity; cache embedding theo `track_id` trong Redis với TTL.
  - Giới tính: Classifier nhẹ (ví dụ MobileNetV3-Small) trên crop nửa trên/khuôn mặt; chạy với
    tần suất giảm (mỗi N frame hoặc khi mới xuất hiện).
  - Giới hạn tần suất theo track và tái sử dụng nhãn ổn định gần nhất để tránh nhấp nháy.
- Cột mốc:
  - M1: Thêm `reid_embed: List[float]` vào trạng thái track; tính mỗi K frame; cache Redis.
  - M2: Thêm classifier giới tính; chống rung nhãn bằng bỏ phiếu đa số trên M dự đoán gần nhất.
  - M3: Mở rộng overlay hiển thị `track_id` và giới tính; ghi vào báo cáo JSON.
- Tiêu chí nghiệm thu:
  - Re-ID giảm đổi ID ≥30% trên clip test; độ trễ embedding trung bình ≤1.5 ms/track trên M4.
  - Độ chính xác phân loại giới tính ≥90% trên bộ mẫu gọn; nhãn ổn định, không lật liên tục.

### Phase 6 — Lưu Trữ Dữ Liệu & Schema (PostgreSQL + Redis)
- Mục tiêu:
  - Lưu metadata phiên chạy, detections theo frame, tổng hợp theo track.
  - Dùng Redis cho dữ liệu nóng (cache track, embedding gần nhất), PostgreSQL cho phân tích dài hạn.
- Thiết kế:
  - Bảng:
    - `sessions(id, source_type, source_id, start_time, end_time, fps, device)`
    - `tracks(id, session_id, first_seen, last_seen, total_frames, avg_conf, gender)`
    - `track_events(id, track_id, frame, ts, bbox_xyxy, conf)`
  - Redis keys: `track:{session}:{id}` với các trường `last_bbox`, `last_embed`, `gender`, `updated_at`.
  - Dùng truy vấn tham số; context manager; retry theo backoff hàm mũ.
- Cột mốc:
  - M1: Mô hình Pydantic và DDL SQL; script migration.
  - M2: Luồng ghi: chèn đệm cho `track_events` (batch theo N frame).
  - M3: Luồng đọc: script phân tích cơ bản (số người duy nhất, thời gian dừng).
- Tiêu chí nghiệm thu:
  - Chạy end-to-end ghi ≥95% frame không lỗi; không rò rỉ kết nối.
  - Phân tích cơ bản cho kết quả nhất quán với JSON trong sai số ±1%.

### Phase 7 — Pipeline Camera Live
- Mục tiêu:
  - Chuyển từ video offline sang RTSP live; xử lý kết nối bền vững.
- Thiết kế:
  - `CameraReader` tự kết nối lại/backoff; watchdog theo kênh dùng `health_checker`.
  - Vòng xử lý không chặn; hàng đợi frame với chính sách drop khi quá tải.
  - Tắt an toàn và metrics (FPS, queue size, dropped frames).
- Cột mốc:
  - M1: Ổn định 1 nguồn RTSP trong ≥2 giờ; log metrics mỗi 10 giây.
  - M2: Endpoint/script health cho trạng thái live.
- Tiêu chí nghiệm thu:
  - Không deadlock; tự nối lại trong 10 giây khi mạng lỗi; độ trễ end-to-end trung bình <250 ms.

### Phase 8 — Điều Phối Đa Kênh
- Mục tiêu:
  - Xử lý 4 kênh đồng thời với phân bổ tài nguyên công bằng và cách ly.
- Thiết kế:
  - Mỗi kênh một worker (process hoặc thread) với pipeline độc lập; giới hạn CPU bằng affinity khi
    cần.
  - Chia sẻ model qua process riêng (IPC) hoặc mỗi process một model nhẹ tùy theo benchmark.
- Cột mốc:
  - M1: 2 kênh đạt real-time; M2: 4 kênh đạt ≥15 FPS/kênh với MPS.
- Tiêu chí nghiệm thu:
  - Không đói tài nguyên giữa kênh; FPS và độ trễ từng kênh trong ngưỡng mục tiêu.

### Phase 9 — Tối Ưu Hiệu Năng
- Mục tiêu:
  - Duy trì ≥30 FPS với 1 luồng, ≥15 FPS x4 luồng trên M4 Pro.
- Chiến thuật:
  - Resize frame theo đầu vào model; cấp phát sẵn buffer; tránh copy; cân nhắc half precision nếu
    tương thích.
  - Gom lô inference theo N frame khi phù hợp; giảm tần suất demographics để hạ tải.
  - Dùng bộ đo thời gian nội bộ; báo cáo độ trễ trung bình và p95 cho các bước (capture, detect,
    track, reid, gender).
- Tiêu chí nghiệm thu:
  - CPU <80% ổn định; GPU/MPS được tận dụng nhưng ổn định; không rò rỉ bộ nhớ sau 2 giờ chạy.

### Phase 10 — Đóng Gói & Triển Khai
- Mục tiêu:
  - Môi trường tái lập; script; hook giám sát.
- Sản phẩm bàn giao:
  - Pin `requirements.txt`; pre-commit; dùng `verify_*_health.py` làm health probe.
  - Dockerfile (CPU baseline) và hướng dẫn triển khai trên Mac; cấu hình `.env` cho secrets.
  - Exporter metrics đơn giản kiểu Prometheus hoặc log JSON để thu thập.
- Tiêu chí nghiệm thu:
  - Chạy một lệnh cho chế độ đơn/đa kênh; health probe xanh; tài liệu cập nhật.

### Kiểm Thử & Cổng Chất Lượng
- Unit test cho ghép cặp tracker và vòng đời; mock camera/db.
- Integration test trên video mẫu; so sánh JSON golden (cho phép sai số nhỏ).
- Mục tiêu coverage >80%; `flake8`, `mypy`, `bandit` sạch.

### Ghi Chú
- Re-ID và ngưỡng phân loại giới tính cần hiệu chỉnh trên dữ liệu Kidsplaza.
- Tuyệt đối không hardcode secrets; dùng biến môi trường để cấu hình.


