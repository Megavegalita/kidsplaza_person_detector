# Pull Request: Phase 6 - Data Storage Implementation

## Branch
`feature/phase6-storage-schema` → `main_func`

## Mục tiêu
Triển khai hệ thống lưu trữ dữ liệu với PostgreSQL và Redis để lưu trữ detections, tracks, và gender statistics cho phân tích và monitoring.

## Phạm vi
- **Database Schema**: Tạo schema cho `detections`, `tracks`, `track_genders`, `run_gender_summary`
- **Database Managers**: Implement `PostgresManager` và `RedisManager` với connection pooling và batch inserts
- **Integration**: Tích hợp vào video processing pipeline với buffered writes
- **Query Tools**: Tạo SQL queries và helper scripts để truy vấn và xem dashboard metrics
- **File Organization**: Tổ chức lại database files vào `database/` directory

## Thay đổi chính

### 1. Database Schema (`database/schema_phase6.sql`)
- 4 tables: `detections`, `tracks`, `track_genders`, `run_gender_summary`
- Indexes cho performance
- Constraints và unique keys

### 2. Database Modules
- `src/modules/database/models.py`: Dataclass models (`PersonDetection`, `PersonTrack`)
- `src/modules/database/postgres_manager.py`: Connection pooling, batch inserts, upserts
- `src/modules/database/redis_manager.py`: Caching với TTL

### 3. Video Processor Integration
- CLI flags: `--db-enable`, `--db-dsn`, `--db-batch-size`, `--db-flush-interval-ms`
- Buffered write mechanism
- Track gender persistence per unique track ID
- Run-level gender summary
- DB metrics logging (p50/p95 latency)

### 4. Query Tools
- `database/queries/query_tracks.sql`: Comprehensive track information queries
- `database/queries/dashboard_summary.sql`: Dashboard-style summary với key metrics
- `database/queries/check_connection.sql`: Connection verification
- `scripts/query_tracks.sh`: Helper script
- `scripts/dashboard_summary.sh`: Helper script

### 5. Documentation
- `database/README.md`: Database documentation
- `database/queries/README.md`: Query documentation
- `docs/plan/PHASE_6_DATA_STORAGE_PLAN.md`: Phase 6 plan
- `docs/reports/PHASE6_DB_METRICS.md`: Performance metrics

### 6. File Organization
- Moved SQL files to `database/queries/`
- Moved schema to `database/schema_phase6.sql`
- Cleaned up root directory

## Metrics & Performance
- **Insert Latency**: p50 ~3.5-4.5ms, p95 ~5.5-6.5ms (from test runs)
- **Batch Size**: 200 detections per batch (configurable)
- **Flush Interval**: 500ms (configurable)
- **Connection Pooling**: 5 connections (configurable)

## Testing
- ✅ Smoke test với video processing và DB enabled
- ✅ Data validation: In-memory aggregates vs DB summaries
- ✅ Query tools tested với PostgreSQL client
- ✅ Database health verification script

## Acceptance Criteria
- [x] Database schema created và applied
- [x] PostgresManager và RedisManager implemented với error handling
- [x] Video processor tích hợp DB với buffered writes
- [x] Unique track gender counts được lưu đúng (không phải detection-level)
- [x] Run-level gender summary persisted
- [x] Query tools hoạt động và hiển thị đúng metrics
- [x] Key metrics (unique_total, unique_male, unique_female) hiển thị trong dashboard query
- [x] Files organized trong `database/` directory
- [x] Documentation đầy đủ

## Files Changed
- **New**: 10 files (schema, queries, scripts, docs)
- **Modified**: 2 files (`process_video_file.py`, `database/queries/README.md`)
- **Total**: ~500 lines added (Phase 6 specific)

## Ảnh hưởng
- **Breaking Changes**: Không
- **Database Migration**: Cần chạy `database/schema_phase6.sql` trên PostgreSQL
- **Configuration**: Cần cấu hình `config/database.json` với PostgreSQL và Redis connection strings
- **Dependencies**: `psycopg2`, `redis` (đã có trong `requirements.txt`)

## Checklist
- [x] Mục tiêu rõ ràng và phạm vi hẹp (Phase 6 data storage only)
- [x] Acceptance Criteria đạt
- [ ] CI xanh (black, isort, flake8, mypy, pytest, bandit) - **Cần verify**
- [ ] Reviewer duyệt
- [ ] Chọn Squash & merge

## Notes
- Database connection info được load từ `config/database.json`
- Batch size và flush interval có thể tune dựa trên workload
- Dashboard query hiển thị key metrics ở đầu để dễ theo dõi
- Tất cả SQL queries sử dụng `public.` schema prefix để tránh confusion

## Related
- Phase 5: Gender classification và tracking (prerequisite)
- Phase 6 Plan: `docs/plan/PHASE_6_DATA_STORAGE_PLAN.md`
- Metrics Report: `docs/reports/PHASE6_DB_METRICS.md`

