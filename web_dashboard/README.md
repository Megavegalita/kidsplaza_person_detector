# Counter Events Web Dashboard

Web dashboard để hiển thị và phân tích dữ liệu counter events từ database.

## Tính năng

- 📊 **Thống kê tổng quan**: Hiển thị số lượt vào/ra, số người unique, số người hiện tại trong khu vực
- 📈 **Biểu đồ phân tích**: 
  - Biểu đồ đường theo giờ (line chart)
  - Biểu đồ cột tổng quan Enter/Exit (bar chart)
- 🔍 **Bộ lọc linh hoạt**:
  - Lọc theo ngày
  - Lọc theo Channel
  - Lọc theo Zone
- 📋 **Bảng events gần đây**: Hiển thị 50 events mới nhất với đầy đủ thông tin
- 🔄 **Auto-refresh**: Tự động cập nhật dữ liệu mỗi 30 giây

## Cài đặt

1. Cài đặt dependencies:

```bash
cd web_dashboard
pip install -r requirements.txt
```

2. Đảm bảo database đã được cấu hình trong `config/database.json`

## Chạy ứng dụng

```bash
cd web_dashboard
python app.py
```

Ứng dụng sẽ chạy tại: `http://localhost:5000`

## Cấu trúc thư mục

```
web_dashboard/
├── app.py                 # Flask application
├── requirements.txt        # Python dependencies
├── templates/
│   └── index.html         # Main dashboard page
└── static/
    ├── css/
    │   └── style.css      # Stylesheet
    └── js/
        └── dashboard.js   # JavaScript logic
```

## API Endpoints

### GET `/api/summary`
Lấy thống kê tổng quan.

**Query parameters:**
- `date` (optional): Ngày cần xem (YYYY-MM-DD), mặc định: hôm nay
- `channel_id` (optional): Lọc theo channel ID
- `zone_id` (optional): Lọc theo zone ID

**Response:**
```json
{
  "date": "2025-11-07",
  "channel_id": 4,
  "zone_id": null,
  "total_enter": 67,
  "total_exit": 65,
  "unique_tracks_entered": 40,
  "unique_tracks_exited": 42,
  "net_count": 2,
  "hourly_data": {
    "09:00": {"enter": 10, "exit": 13},
    "10:00": {"enter": 33, "exit": 28}
  },
  "available_channels": [4],
  "available_zones": ["line_entrance"]
}
```

### GET `/api/recent-events`
Lấy danh sách events gần đây.

**Query parameters:**
- `limit` (optional): Số lượng events (mặc định: 50)
- `channel_id` (optional): Lọc theo channel ID
- `zone_id` (optional): Lọc theo zone ID

**Response:**
```json
{
  "events": [
    {
      "timestamp": "2025-11-07T14:32:55",
      "channel_id": 4,
      "zone_id": "line_entrance",
      "event_type": "enter",
      "track_id": 215,
      "person_id": null
    }
  ]
}
```

## Sử dụng

1. Mở trình duyệt và truy cập `http://localhost:5000`
2. Sử dụng các bộ lọc ở đầu trang:
   - Chọn ngày cần xem
   - Chọn Channel (hoặc để trống để xem tất cả)
   - Chọn Zone (hoặc để trống để xem tất cả)
   - Click "Áp dụng" để lọc dữ liệu
3. Xem các chỉ số trong summary cards
4. Xem biểu đồ phân tích theo giờ
5. Xem bảng events gần đây ở cuối trang

## Ghi chú

- Dashboard tự động refresh mỗi 30 giây
- Dữ liệu được lấy trực tiếp từ PostgreSQL database
- Tất cả timestamps được hiển thị theo múi giờ Việt Nam (UTC+7)

