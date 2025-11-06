## Phase 6 DB Metrics Snapshot

### Environment
- PostgreSQL: localhost:5432, DB: gender_analysis, User: autoeyes
- Redis: localhost:6379, DB: 0

### Smoke Run
- Command preset: `gender_main_v1`
- Run ID: `phase6_db_smoke2`
- Video: `input/video/Binh Xa-Thach That_ch4_20251024102450_20251024112450.mp4`
- Duration: 91.31s, Avg frame time: 20.29ms (MPS)

### Insert Latency (detections)
- Per 100-sample snapshots (approx):
  - p50: 4.2–4.5 ms
  - p95: 6.0–6.4 ms
  - samples: 100 per snapshot
- Final flush inserted: 20 rows

### Row Counts (PostgreSQL)
- `detections_total`: 20,970
- `tracks_total`: 0 (track upsert not yet integrated)

### Gender Distribution (detections)
- `M`: 10,331
- `F`: 9,361
- `Unknown`: 1,278

### Time Range
- min(timestamp): 2025-10-31 16:57:33.394674
- max(timestamp): 2025-10-31 16:59:04.002114

### Notes
- Schema file: `schema_phase6.sql`
- Batch: 200, Flush interval: 500ms

