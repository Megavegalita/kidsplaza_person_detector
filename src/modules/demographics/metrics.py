#!/usr/bin/env python3
"""
Metrics collection for gender classification pipeline.

Lightweight in-memory counters and histograms suitable for periodic logging.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


def _percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    values_sorted = sorted(values)
    k = max(0, min(len(values_sorted) - 1, int(round((p / 100.0) * (len(values_sorted) - 1)))))
    return values_sorted[k]


@dataclass
class GenderMetrics:
    """Thread-safe metrics aggregator for gender classification."""

    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    calls_total: int = 0
    calls_per_frame: int = 0
    results_total: int = 0
    dropped_total: int = 0
    queue_len: int = 0

    latencies_ms: List[float] = field(default_factory=list)

    gender_counts: Dict[str, int] = field(
        default_factory=lambda: {"M": 0, "F": 0, "Unknown": 0}
    )

    flips_total: int = 0
    last_gender_by_track: Dict[int, str] = field(default_factory=dict)

    def inc_call(self) -> None:
        with self._lock:
            self.calls_total += 1
            self.calls_per_frame += 1

    def inc_dropped(self) -> None:
        with self._lock:
            self.dropped_total += 1

    def observe_latency(self, ms: float) -> None:
        with self._lock:
            self.latencies_ms.append(ms)

    def observe_gender(self, track_id: int, gender: str) -> None:
        with self._lock:
            prev = self.last_gender_by_track.get(track_id)
            if prev and prev != gender:
                self.flips_total += 1
            self.last_gender_by_track[track_id] = gender
            if gender not in self.gender_counts:
                gender = "Unknown"
            self.gender_counts[gender] += 1

    def reset_frame(self) -> None:
        with self._lock:
            self.calls_per_frame = 0

    def set_queue_len(self, qlen: int) -> None:
        with self._lock:
            self.queue_len = qlen

    def snapshot(self) -> Dict[str, float]:
        with self._lock:
            p50 = _percentile(self.latencies_ms, 50)
            p95 = _percentile(self.latencies_ms, 95)
            coverage = (self.results_total / self.calls_total) * 100.0 if self.calls_total else 0.0
            return {
                "calls_total": float(self.calls_total),
                "calls_per_frame": float(self.calls_per_frame),
                "results_total": float(self.results_total),
                "dropped_total": float(self.dropped_total),
                "queue_len": float(self.queue_len),
                "latency_ms_p50": float(p50),
                "latency_ms_p95": float(p95),
                "coverage_percent": float(coverage),
                "flip_rate_percent": float(
                    (self.flips_total / max(1, len(self.last_gender_by_track))) * 100.0
                ),
                "gender_M": float(self.gender_counts.get("M", 0)),
                "gender_F": float(self.gender_counts.get("F", 0)),
                "gender_U": float(self.gender_counts.get("Unknown", 0)),
            }


