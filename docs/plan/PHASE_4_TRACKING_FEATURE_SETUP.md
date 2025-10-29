## Thiết Lập Tính Năng: Phase 4 — Theo Dõi Ổn Định (MOT)

Tài liệu liên quan:
- `docs/plan/NEXT_PHASE_IMPROVEMENTS.md`
- Tham chiếu phân tích Re-ID & Giới tính: 
  https://docs.google.com/document/d/1OqQ-7W-jSMCALZICdgKIi9sedr_5d1w1aNFuoyzRc_0/edit?usp=sharing

### 1) Yêu Cầu & Tiêu Chí Nghiệm Thu
- Ổn định `track_id` theo thời gian, giảm lỗi đổi ID (ID-switch) và phân mảnh track.
- Trả về detections kèm `track_id` từ tracker; quản lý vòng đời track (age, hits, last_seen).
- Overlay hiển thị số Tracks và `track_id`/giới tính (khi có) trên bbox.
- Báo cáo JSON ghi `track_id` cho tất cả detections sau khung xác nhận đầu tiên.
- Mục tiêu hiệu năng: giữ ≥30 FPS (đơn luồng), với pipeline hiện tại trên M4 Pro.
- Tiêu chí nghiệm thu:
  - Tỉ lệ ID-switch < 2% trên video test cung cấp.
  - Không tái sử dụng `track_id` trong vòng 2 giây kể từ `last_seen`.
  - JSON gồm `track_id` ổn định; overlay thể hiện rõ số lượng Tracks.

### 2) User Stories
- Là người vận hành, tôi muốn thấy `track_id` ổn định trên mỗi người trong video để dễ theo dõi.
- Là nhà phân tích, tôi muốn dữ liệu JSON có `track_id` cho mỗi detection để thống kê thời gian hiện diện.
- Là kỹ sư, tôi muốn cấu hình ngưỡng IoU/độ tin cậy/smoothing qua config để tinh chỉnh nhanh.

### 3) Cách Tiếp Cận Kỹ Thuật
- Liên kết phát hiện-track dựa trên IoU (nhanh), bổ sung:
  - Smoothing chuyển động: EMA trên tọa độ bbox theo `alpha` cấu hình.
  - Ràng buộc ghép cặp: ngưỡng IoU tối thiểu, so khớp tỉ lệ khung, ngưỡng độ tin cậy.
  - Quản lý vòng đời: `max_age`, `min_hits`, loại bỏ track không cập nhật.
- API tracker: `update(detections) -> detections_with_track_id`.
- Overlay: vẽ `track_id` và số lượng Tracks; sẵn sàng hiển thị giới tính ở Phase 5.
- Cấu hình: thêm tham số trong tracker (iou_threshold, max_age, min_hits, ema_alpha).
- Tương thích Phase 5: chuẩn bị chỗ gắn embedding Re-ID và nhãn giới tính trong state track.

### 4) Kiến Trúc/Tổ Chức Mã
- Cập nhật `src/modules/tracking/tracker.py`:
  - Thêm EMA smoothing và tham số cấu hình.
  - Đảm bảo `update` trả về detections kèm `track_id` nhất quán.
- Cập nhật `src/scripts/process_video_file.py`:
  - Sử dụng kết quả từ tracker để vẽ overlay (số Tracks, `track_id`).
  - Đảm bảo ghi `track_id` vào JSON.
- Không thay đổi giao diện detector; giữ nguyên hiệu năng YOLOv8.

### 5) Chiến Lược Kiểm Thử
- Unit tests (pytest) cho tracker:
  - Ghép cặp IoU đúng; vòng đời track (tạo, cập nhật, xóa);
  - Smoothing duy trì ổn định, không rung quá mức.
- Integration test trên video mẫu:
  - So sánh JSON kết quả với kỳ vọng (sai số nhỏ cho bbox);
  - Đo tỉ lệ ID-switch; kiểm tra overlay hiển thị số Tracks.

### 6) Checklist Thiết Lập
- [ ] Yêu cầu & tiêu chí nghiệm thu được ghi lại (mục 1)
- [ ] User stories viết xong (mục 2)
- [ ] Cách tiếp cận kỹ thuật hoàn chỉnh (mục 3)
- [ ] Kiến trúc & tác động code rõ ràng (mục 4)
- [ ] Chiến lược kiểm thử (mục 5)

### 7) Nhánh Tính Năng & Môi Trường
- Nhánh đề xuất: `feature/phase4-tracking`
- Cấu hình/lint/typing/test giữ nguyên theo tiêu chuẩn dự án.

