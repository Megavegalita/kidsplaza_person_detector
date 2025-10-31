## Gender Feature Requirements (Accuracy-First)

### User Stories
- As an operator, I want incorrect labels to be minimized, even if that means more Unknown labels in hard views.
- As an analyst, I want stable labels over time per person, with reduced flip rate.
- As an engineer, I want metrics and reports to validate accuracy gains without sacrificing throughput.

### Acceptance Criteria
- Emit `Unknown` when confidence < threshold; do not force labels.
- Label mapping unified across all classifiers; no inversion/regression.
- Flip rate per track reduced ≥ 30% vs baseline on benchmark clips.
- p95 per-task latency ≤ 50 ms; pipeline FPS not worse than baseline.
- Periodic reports include: M/F/Unknown counts, flip rate, latency percentiles.

### Technical Approach (High-Level)
- Shared label mapper module + unit tests.
- Face-first pipeline with `face_every_k` and track-level face bbox cache.
- Majority voting per track; last-known gender retention until next evaluation.
- Adaptive sampling (secondary) based on queue length thresholds.
- Enhanced metrics and periodic reporting.




