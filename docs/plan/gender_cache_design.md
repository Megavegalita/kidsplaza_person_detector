## Gender Cache & Reporting Design

### Requirements
- If confidence is low or view is ambiguous, output `Unknown`.
- Persist last-known gender per track; hold until next evaluation cycle.
- Aggregate gender decisions periodically per session for reporting.

### Model
- Scope: per-session, per-track cache keyed by `(session_id, track_id)`.
- Contents:
  - last_gender: str in {M,F,Unknown}
  - last_confidence: float
  - last_updated_frame: int
  - history (optional): compact counts {M,F,Unknown}

### Policy
- Update cache only when confidence >= min_confidence or when face-first is used with good face conf.
- If new result is `Unknown`, keep last-known gender but increment history Unknown count.
- Re-evaluate on schedule (every `gender_every_k`) or when face detected.

### TTL & Cleanup
- TTL in frames (e.g., 90 frames) or time-based (seconds); cleanup when tracks end.

### Aggregation
- Periodic snapshot (e.g., every N seconds):
  - By session: total counts, M/F/Unknown, flip rate, latency percentiles.
  - Export JSON for reporting.

### Implementation Notes
- In-memory dict in pipeline; optional Redis for cross-process persistence if needed.
- Thread-safety: updates occur in main thread after async results arrive.



