## Thiết Lập Tính Năng: Phase 5 — Re-ID Core

Tài liệu liên quan:
- `docs/plan/NEXT_PHASE_IMPROVEMENTS.md`
- `docs/standards/BRANCHING_AND_PR_POLICY.md`

### 1) Yêu Cầu & Tiêu Chí Nghiệm Thu
- Thêm embedding Re-ID cho mỗi `track_id` để giảm đổi ID (ID-switch) khi che khuất/nhảy khung.
- Lưu embedding mới theo tần suất giảm (mỗi K frame hoặc khi track mới/đổi hướng rõ).
- Cache embedding theo `track_id` trong Redis (TTL cấu hình), phục vụ so khớp xuyên thời gian.
- Tích hợp Re-ID vào tracker pipeline theo kiểu “hỗ trợ” (không chặn inference chính).
- Tiêu chí nghiệm thu:
  - Giảm ID-switch ≥ 30% trên video test so với baseline không Re-ID.
  - Độ trễ Re-ID trung bình ≤ 1.5 ms/track (M4) với batch nhỏ.
  - Không ảnh hưởng FPS mục tiêu (≥30 FPS 1 kênh; ≥15 FPS x4 kênh khi mở rộng).

### 2) User Stories
- Là người vận hành, tôi muốn ID ổn định hơn qua che khuất ngắn và di chuyển nhanh.
- Là nhà phân tích, tôi muốn dữ liệu thống kê theo `track_id` nhất quán, ít bị phân mảnh.
- Là kỹ sư, tôi muốn bật/tắt Re-ID, điều chỉnh K, TTL, và ngưỡng cosine qua config nhanh chóng.

### 3) Cách Tiếp Cận Kỹ Thuật
- Mô hình embedding nhẹ: OSNet-x0_25 hoặc MobileNet head được tối ưu kích thước.
- Chuẩn embedding: vector float32 chuẩn hoá L2; so khớp bằng cosine similarity.
- Tích hợp:
  - Tính embedding cho ROI người (crop từ `image_processor.draw_detections`/crop_person) theo K frame.
  - Lưu `last_embed` vào Redis theo key `track:{session}:{track_id}` với TTL.
  - Khi có mất ghép cặp IoU, dùng cosine để cứu vãn so khớp (cosine ≥ threshold cấu hình).
- Hiệu năng:
  - Batch nhỏ theo số track trong frame; tiền cấp phát buffer; chạy song song nhẹ.
  - Giới hạn tối đa số embedding/frame để giữ FPS.

### 4) Kiến Trúc/Tổ Chức Mã
- Thư mục `src/modules/reid/`:
  - `embedder.py`: tải model Re-ID, sinh embedding từ crop.
  - `cache.py`: adapter Redis (get/set với TTL, cấu hình keyspace).
  - `integrator.py`: hàm tiện ích gắn vào pipeline tracker (tính theo K frame, lưu cache).
- Cập nhật `tracker.py` (tùy chọn): hook điểm mở để nhận gợi ý so khớp từ Re-ID khi IoU thấp.
- Cấu hình: thêm vào `.env`/config cho Redis URL, TTL, K, cosine_threshold, batch_size.

### 5) Chiến Lược Kiểm Thử
- Unit tests:
  - `embedder`: đầu vào giả lập → vector chuẩn hoá, kích thước đúng, ổn định.
  - `cache`: set/get, TTL hoạt động, xử lý lỗi Redis.
  - `integrator`: tần suất K, cập nhật `track_id` không làm sập pipeline.
- Integration:
  - Chạy video mẫu, đo ID-switch trước/sau; log thời gian Re-ID trung bình.

### 6) Checklist Thiết Lập
- [ ] Yêu cầu & tiêu chí nghiệm thu được ghi lại (mục 1)
- [ ] User stories hoàn tất (mục 2)
- [ ] Cách tiếp cận kỹ thuật (mục 3)
- [ ] Kiến trúc & tác động code (mục 4)
- [ ] Chiến lược kiểm thử (mục 5)
- [ ] Nhánh tính năng: `feature/phase5-reid-core` (đã tạo)
