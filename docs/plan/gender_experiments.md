## Gender Optimization Experiments

### Objectives
- Quantify latency, stability (flip rate), and coverage (Unknown rate) across configurations.
- Evaluate face-first vs fallback-only, sampling/adaptive strategies, and caching policies.

### Datasets
- Short clips (1–3 minutes) with varied angles, occlusions, lighting.
- Include segments where gender is ambiguous to validate Unknown handling.

### Metrics
- Per-task latency: p50/p95/p99.
- Queue length over time; drop rate.
- Flip rate per track (label changes across time).
- Unknown rate when ambiguity present.
- Throughput (pipeline FPS) and CPU/GPU utilization (if available).

### Scenarios
1) Baseline
   - face_detection=off, gender_every_k=20, max_per_frame=4, min_conf=0.5.
2) Face-first
   - face_detection=on, face_every_k=5, with bbox cache ttl=90 frames.
3) Adaptive Sampling
   - adaptive=on, queue HWM/LWM=200/100.
4) Combined
   - face-first + adaptive.

### Procedure
- For each scenario, run benchmark script over the same video(s).
- Collect JSON reports and logs into scenario-specific directories.
- Summarize metrics in a compact table and trend charts (optional).

### Acceptance
- p95 latency <= 50ms/task; FPS steady vs baseline.
- Flip rate reduced > 30% in combined scenario.
- Unknown rate aligned with ambiguous segments (no forced mislabels).



