#!/usr/bin/env python3
"""
Summarize gender benchmark reports across scenarios into a compact table.

Usage:
  python src/scripts/summarize_gender_reports.py \
    --base /Users/autoeyes/Project/kidsplaza/person_detector/output/videos \
    --video "Binh Xa-Thach That_ch4_20251024102450_20251024112450"

Scenarios searched: baseline, face_first, adaptive, combined
Output: prints a table with key metrics per scenario
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

SCENARIOS = [
    "baseline",
    "face_first",
    "adaptive",
    "combined",
    "base_e20_c04",
    "base_e20_c06",
    "base_e30_c04",
    "face_e20_c04_k5",
    "face_e20_c06_k5",
    "adapt_e20_c04",
    "combo_e20_c04_k5",
    "combo_e20_c06_k5",
]


def load_report(base: Path, scenario: str, video_stem: str) -> Optional[Dict[str, Any]]:
    report_path = base / scenario / scenario / f"report_{video_stem}.json"
    if not report_path.exists():
        # fallback to scenario root (if run_id not applied)
        report_path = base / scenario / f"report_{video_stem}.json"
        if not report_path.exists():
            return None
    try:
        with report_path.open("r") as f:
            return json.load(f)
    except Exception:
        return None


def pick_metrics(report: Dict[str, Any]) -> Dict[str, Any]:
    processing = report.get("processing", {})
    video_props = report.get("video_properties", {})
    detector_stats = report.get("detector_stats", {})
    summary = report.get("summary", {})
    gender_total = summary.get("gender_counts_total", {})
    return {
        "time_s": round(float(processing.get("time_seconds", 0.0)), 2),
        "avg_ms": round(float(processing.get("avg_time_per_frame_ms", 0.0)), 2),
        "fps": float(video_props.get("fps", 0.0)),
        "frames": int(video_props.get("total_frames", 0)),
        "proc_frames": int(detector_stats.get("frame_count", 0)),
        "unique_tracks": int(summary.get("unique_tracks_total", 0)),
        "M": int(gender_total.get("M", 0)),
        "F": int(gender_total.get("F", 0)),
        "U": int(gender_total.get("Unknown", 0)),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Summarize gender benchmark reports")
    ap.add_argument(
        "--base", type=Path, required=True, help="Base output/videos directory"
    )
    ap.add_argument(
        "--video", type=str, required=True, help="Video stem (no extension)"
    )
    args = ap.parse_args()

    rows: list[Tuple[str, Optional[Dict[str, Any]]]] = []
    for sc in SCENARIOS:
        rpt = load_report(args.base, sc, args.video)
        if rpt is None:
            rows.append((sc, None))
        else:
            rows.append((sc, pick_metrics(rpt)))

    # Print table
    headers = [
        "scenario",
        "time_s",
        "avg_ms",
        "proc_frames",
        "unique_tracks",
        "M",
        "F",
        "U",
    ]
    print("\t".join(headers))
    for sc, mt in rows:
        if mt is None:
            print(f"{sc}\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A")
        else:
            print(
                f"{sc}\t{mt['time_s']}\t{mt['avg_ms']}\t{mt['proc_frames']}\t{mt['unique_tracks']}\t{mt['M']}\t{mt['F']}\t{mt['U']}"
            )


if __name__ == "__main__":
    main()
