## Gender Classification Optimization Plan

### Goals (Accuracy-First)
- Maximize labeling correctness and stability; prioritize reducing mislabels and flips.
- Emit `Unknown` when ambiguous/low-confidence instead of forcing labels.
- Persist last-known gender per track and re-evaluate on schedule or when higher-quality signal (face) appears.
- Maintain acceptable latency/FPS via sampling and async design (secondary to accuracy).

### Principles
- Non-blocking pipeline: use async workers, sampling, and per-frame budgets.
- Face-first when available, fallback to upper-body/person crop.
- Confidence-thresholded outputs with majority voting to reduce flicker.
- Track-scoped caching of last-known gender; reevaluate at configurable intervals.

### Scope
- Standardize label mapping across classifiers.
- Introduce `face_every_k` and track-level face bbox cache.
- Adaptive sampling based on queue pressure.
- Metrics enhancement: p50/p95/p99 latency, flip rate, queue stats.
- Reporting: periodic aggregation by session.

### Workstream Breakdown (Prioritized)
1. Accuracy Consistency
   - Standardize label mapping via shared mapper; enforce consistent conventions across all classifiers.
   - Unify `min_confidence` handling; ensure `Unknown` on low confidence.
2. Face-First Strategy
   - Introduce `face_every_k` and track-level face bbox cache to prefer high-quality face inputs.
3. Stability Over Time
   - Ensure majority voting per track; keep last-known gender until next scheduled re-evaluation.
4. Metrics for Accuracy
   - Add flip-rate per track, Unknown rate, and latency percentiles; log compactly.
5. Load Safety (Secondary)
   - Adaptive sampling and worker drop policies to protect FPS without harming accuracy.
6. Reporting
   - Periodic aggregation per session for audits and benchmarks.

### Configuration Knobs (proposed)
- gender_every_k: int (default 20)
- gender_max_per_frame: int (default 4)
- gender_min_confidence: float (default 0.5)
- gender_voting_window: int (default 10)
- gender_enable_face_detection: bool
- gender_face_every_k: int (default 5)
- gender_cache_ttl_frames: int (default 90)
- gender_adaptive_enabled: bool (default true)
- gender_queue_high_watermark: int (default 200)
- gender_queue_low_watermark: int (default 100)

### Metrics & Acceptance
- Latency p50/p95/p99 within budget (e.g., p95 < 50ms per task).
- Flip rate per track reduced by X% vs baseline.
- Drop rate under sustained load < Y%.
- Throughput unaffected (baseline FPS maintained).

### Risks & Mitigations
- Face detection overhead: mitigate with face_every_k and bbox cache.
- Label inconsistency: unified mapper and tests.
- Queue saturation: adaptive sampling and drop policy.


