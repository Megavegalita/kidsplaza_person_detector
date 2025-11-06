# Phase 6: Data Storage (PostgreSQL + Redis)

## Goals
- Persist detections, tracks, and demographics to PostgreSQL reliably
- Cache short‑lived tracking data in Redis for fast lookup
- Provide metrics, retries, and batch inserts for stable throughput

## Scope
- PostgreSQL schema + indices; batch inserts; basic queries
- Redis cache for recent tracks/detections and embeddings
- Pipeline integration (offline video script) with backpressure

## Deliverables
- `src/modules/database/models.py`
- `src/modules/database/postgres_manager.py`
- `src/modules/database/redis_manager.py`
- CLI flags to enable DB writes and tune batch/flush intervals
- Unit and integration tests + benchmark notes

## Database Schema (initial)
- Table `detections`:
  - columns: timestamp, camera_id, channel_id, detection_id, track_id, confidence,
    bbox_x, bbox_y, bbox_width, bbox_height, gender, gender_confidence, frame_number
  - indices: `idx_detections_timestamp`, `idx_detections_track_id`, `idx_detections_camera_id`
- Table `tracks`:
  - columns: track_id, camera_id, start_time, end_time, detection_count, avg_confidence,
    trajectory (JSONB)
  - indices: `idx_tracks_camera_id`, `idx_tracks_track_id`

## API (first iteration)
- PostgreSQL
  - `insert_detections(detections: list[PersonDetection]) -> int`
  - `upsert_track(track: PersonTrack) -> None`
  - `bulk_upsert_tracks(tracks: list[PersonTrack]) -> int`
  - `query_detections_by_time(start: datetime, end: datetime) -> list[PersonDetection]`
- Redis
  - `cache_track(session_id: str, track_id: int, payload: dict, ttl: int) -> None`
  - `get_track(session_id: str, track_id: int) -> dict | None`

## Integration Points
- `src/scripts/process_video_file.py`:
  - buffer detections to batches of N or T ms before flush
  - guard with `--db-enable`, `--db-batch-size`, `--db-flush-interval-ms`, `--redis-enable`
  - non‑blocking flush with retry + backoff

## Observability
- Metrics: insert_batch_size, insert_latency_p50/p95, failures, retries
- Structured logs for failures and slow queries

## Risks/Mitigations
- DB latency spikes → batch with backoff, drop to minimal fields if saturated
- Redis unavailable → soft‑fail, continue pipeline
- Contention on large batches → tune `insert_batch_size`, add indices selectively

## Exit Criteria
- Batch insert >= 1k detections/s on dev machine (target)
- P95 insert latency < 50 ms per batch (initial target)
- Tests green (unit/integration), mypy/flake8 OK
