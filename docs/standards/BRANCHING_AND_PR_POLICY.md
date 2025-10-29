## Chính Sách Nhánh & Pull Request (PR)

### Mục tiêu
- Duy trì lịch sử thay đổi sạch, dễ truy vết, đảm bảo chất lượng qua cổng kiểm soát nghiêm ngặt.

### Nhánh gốc
- `main_func` là branch được bảo vệ. Mọi thay đổi chỉ được merge qua PR đã kiểm duyệt.

### Chiến lược nhánh
- "Nhánh sống ngắn" theo từng hạng mục nhỏ (≤ 1–3 ngày làm việc, ≤ 400 dòng thay đổi).
- Đặt tên theo định dạng: `feature/<phase>-<mô-tả-ngắn>` hoặc `hotfix/<mô-tả-ngắn>`.
- Ví dụ:
  - `feature/phase5-reid-core`
  - `feature/phase5-gender-classifier`
  - `feature/phase6-storage-schema`
  - `feature/phase7-live-pipeline`
  - `feature/phase8-multichannel`

### Quy tắc PR
- Bắt buộc 1 reviewer tối thiểu, CI phải xanh.
- PR nhỏ gọn, mô tả rõ mục tiêu, phạm vi, ảnh hưởng, và "Acceptance Criteria".
- Merge strategy: ưu tiên "Squash & merge" để giữ lịch sử clean.
- Không gộp nhiều hạng mục không liên quan trong cùng một PR.

### Cổng chất lượng (bắt buộc trước khi merge)
- Định dạng & sắp xếp import: `black src/ && isort src/`
- Lint: `flake8 src/ --config=.config/.flake8`
- Type check: `mypy src/ --config-file=.config/mypy.ini`
- Kiểm thử: `pytest -c .config/pytest.ini --cov=src`
- Bảo mật: `bandit -r src/`

### Quản trị cấu hình & bảo mật
- Không hardcode secrets; dùng biến môi trường (`.env`, không commit).
- Thiết lập mặc định an toàn (timeout, backoff, batch-size) trong code.

### Nguyên tắc API nội bộ
- Thay đổi public API trong `src/modules/` phải kèm unit tests và cập nhật tài liệu.
- Không phá vỡ tương thích nếu không cần thiết; nếu bắt buộc, ghi rõ trong PR.

### Hotfix
- Dùng nhánh `hotfix/*` cho lỗi khẩn; vẫn cần CI + 1 review trước khi merge.

### Checklist cho mỗi PR
- [ ] Mục tiêu rõ ràng và phạm vi hẹp
- [ ] Acceptance Criteria đạt
- [ ] CI xanh (black, isort, flake8, mypy, pytest, bandit)
- [ ] Reviewer duyệt
- [ ] Chọn Squash & merge


