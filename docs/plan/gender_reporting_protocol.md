## Gender Reporting Protocol

### Snapshot Interval
- Periodic aggregation (e.g., every 30s) during a session.

### Data Collected
- Counts: M, F, Unknown.
- Flip rate per track and overall.
- Latency percentiles (p50/p95/p99) and drop rate.
- Queue stats: avg/max length.

### Output
- JSON file per run/scenario in output directory.
- Optional CSV for quick analysis.

### Retention
- Keep per-run reports; provide a compact summary at the end of benchmarking.



