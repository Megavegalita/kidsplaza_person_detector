# Giải Thích: `reid_ttl_seconds`

## Khái Niệm

**TTL** = **Time To Live** (Thời gian sống)

`reid_ttl_seconds` là thời gian (tính bằng giây) mà Re-ID embedding được lưu trong Redis cache trước khi tự động bị xóa.

## Cách Hoạt Động

### 1. Khi Lưu Embedding vào Cache

```python
# Trong ReIDCache.set() - line 72-76
self._client.setex(
    self._key(session_id, item.track_id),
    self.ttl_seconds,  # ← Thời gian sống (TTL)
    json.dumps(payload),
)
```

**Redis command `SETEX`**:
- `SETEX key seconds value` = Set key với giá trị và thời gian hết hạn
- Sau `ttl_seconds` giây, Redis tự động xóa key này

### 2. Ví Dụ Với TTL = 60 giây

```
Frame 100: Lưu embedding của track_id=5 vào Redis với TTL=60s
Frame 110: Vẫn có thể lấy embedding (chưa hết hạn)
Frame 150: Vẫn có thể lấy embedding (chưa hết hạn) 
Frame 161: Redis đã tự động xóa → get() trả về None
```

### 3. Key Format

```
track:{session_id}:{track_id}:embed
```

Ví dụ: `track:2025-11-02_ch1:123:embed`

## Giá Trị Hiện Tại

### Trong Preset `gender_main_v1`:
```python
"reid_ttl_seconds": 60  # 60 giây = 1 phút
```

### Giá Trị Mặc Định:
- **Default**: 60 giây (1 phút)
- **Định nghĩa**: `def __init__(self, ..., ttl_seconds: int = 60)`

## Tại Sao Cần TTL?

### 1. **Tự Động Dọn Dẹp Cache**
- Tracks cũ (người đã rời khỏi camera) tự động bị xóa
- Không cần code xóa thủ công
- Tránh memory leak trong Redis

### 2. **Re-ID Matching Chính Xác**
- Chỉ match với tracks còn active (trong vòng 60s gần đây)
- Không match với tracks đã cũ (người đã rời khỏi)
- Giảm false positive matches

### 3. **Memory Management**
- Giới hạn memory usage trong Redis
- Tự động giải phóng space cho tracks mới
- Quan trọng khi có nhiều tracks cùng lúc

## Khi Nào Embedding Bị Xóa?

### Scenario 1: Track Vẫn Active
```
Frame 100: Lưu embedding (TTL=60s)
Frame 110: Update embedding (TTL reset về 60s) ← Gia hạn
Frame 150: Update embedding (TTL reset về 60s) ← Gia hạn
```

**Lưu ý**: Mỗi lần `set()`, TTL được reset về 60 giây

### Scenario 2: Track Không Còn (Người Rời Khỏi)
```
Frame 100: Lưu embedding (TTL=60s)
Frame 110: Không có detections mới
Frame 150: Không có detections mới
Frame 161: Redis tự động xóa (TTL hết)
```

## Điều Chỉnh TTL

### Tăng TTL (ví dụ: 120 giây)
**Ưu điểm**:
- Embedding tồn tại lâu hơn
- Có thể match với người quay lại sau 1-2 phút

**Nhược điểm**:
- Tốn nhiều memory hơn
- Có thể match với tracks đã cũ (false positive)

### Giảm TTL (ví dụ: 30 giây)
**Ưu điểm**:
- Tiết kiệm memory
- Chỉ match với tracks rất gần đây

**Nhược điểm**:
- Embedding mất nhanh
- Khó match với người quay lại sau 30s

## Khuyến Nghị

### Cho CCTV Live Streaming:
- **60 giây** (hiện tại) là hợp lý
- Đủ để track người di chuyển trong camera
- Tự động cleanup sau khi người rời khỏi

### Cho Scenarios Đặc Biệt:
- **High Traffic**: Giảm xuống 30-40s để tiết kiệm memory
- **Re-enter Scenarios**: Tăng lên 90-120s để match người quay lại

## Code Flow

```
1. integrate_reid_for_tracks() được gọi
2. Tính embedding từ frame crop
3. Lưu vào Redis cache:
   cache.set(session_id, ReIDCacheItem(...))
4. Redis tự động set expiration = ttl_seconds
5. Sau ttl_seconds, Redis tự động xóa key
```

## Tóm Tắt

| Thuộc Tính | Giá Trị |
|------------|---------|
| **Tên** | `reid_ttl_seconds` |
| **Kiểu** | Integer (giây) |
| **Mặc định** | 60 giây |
| **Hiện tại** | 60 giây (trong preset) |
| **Mục đích** | Thời gian sống của embedding trong Redis |
| **Tác dụng** | Tự động xóa tracks cũ, quản lý memory |

**Kết luận**: `reid_ttl_seconds = 60` có nghĩa là mỗi Re-ID embedding sẽ được lưu trong Redis cache trong **60 giây**, sau đó tự động bị xóa để tránh memory leak và chỉ match với tracks còn active.


