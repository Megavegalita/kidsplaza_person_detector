## Phase 6: Data Storage (PostgreSQL + Redis)

### Scope
- Add DB datamodels (`PersonDetection`, `PersonTrack`)
- Implement `PostgresManager` (pooling, batch insert, upsert track)
- Implement `RedisManager` (JSON caching, TTL)
- Integrate buffered DB writes and Redis caching to `src/scripts/process_video_file.py`
- Add DB metrics snapshot in logs and expose `snapshot_metrics()`
- Add CLI flags: `--db-enable`, `--db-dsn`, `--db-batch-size`, `--db-flush-interval-ms`, `--redis-enable`, `--redis-url`, `--redis-ttl-seconds`
- Provide SQL schema `schema_phase6.sql`

### Artifacts
- Plan: `docs/plan/PHASE_6_DATA_STORAGE_PLAN.md`
- Metrics: `docs/reports/PHASE6_DB_METRICS.md`
- Schema: `schema_phase6.sql`
- Smoke report: `output/videos/phase6_db_smoke2/report_Binh Xa-Thach That_ch4_20251024102450_20251024112450.json`

### Quality Gates Checklist
- [x] black src/ && isort src/
- [x] flake8 src/ --config=.config/.flake8
- [x] mypy src/ --config-file=.config/mypy.ini
- [x] pytest -c .config/pytest.ini
- [x] bandit -r src/

### Notes
- DB insert latency (p50≈4.2–4.5ms, p95≈6.0–6.4ms) at batch=200, flush=500ms
- `tracks` upsert hook is implemented but not yet wired into the pipeline (future PR)

