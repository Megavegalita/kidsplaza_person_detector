#!/usr/bin/env python3
"""
Summarize improvement experiment results and compare with baseline.

Usage:
  python src/scripts/summarize_improvements.py \
    --base /Users/autoeyes/Project/kidsplaza/person_detector/output/videos \
    --video "Binh Xa-Thach That_ch4_20251024102450_20251024112450"
"""

import argparse
import json
from pathlib import Path
from typing import Dict, Optional, List, Tuple


IMPROVEMENT_SCENARIOS = [
    ("adapt_e20_c04_reid_opt_v2", "Baseline (Adaptive + Re-ID optimized)"),
    ("improv1_gender_e15", "More frequent gender (every-k=15)"),
    ("improv2_reid_e15", "More frequent Re-ID (every-k=15)"),
    ("improv3_gender_c045", "Stricter gender conf (0.45)"),
    ("improv4_gender_c050", "Stricter gender conf (0.50)"),
    ("improv5_reid_t060", "Relaxed Re-ID threshold (0.60)"),
    ("improv6_reid_t070", "Stricter Re-ID threshold (0.70)"),
    ("improv7_reid_emb4", "More Re-ID embeddings (max=4)"),
    ("improv8_combined", "Combined (gender_e15 + reid_e15 + c045)"),
]


def load_report(base: Path, scenario: str, video_stem: str) -> Optional[Dict]:
    """Load JSON report for a scenario."""
    report_path = base / scenario / f"report_{video_stem}.json"
    if not report_path.exists():
        return None
    try:
        with report_path.open("r") as f:
            return json.load(f)
    except Exception:
        return None


def extract_metrics(report: Dict) -> Dict:
    """Extract key metrics from report."""
    processing = report.get("processing", {})
    video_props = report.get("video_properties", {})
    detector_stats = report.get("detector_stats", {})
    summary = report.get("summary", {})
    gender_total = summary.get("gender_counts_total", {})
    gender_metrics = report.get("gender_metrics", {})
    
    total_gender = gender_total.get("M", 0) + gender_total.get("F", 0) + gender_total.get("Unknown", 0)
    
    return {
        "time_s": round(float(processing.get("time_seconds", 0.0)), 2),
        "avg_ms": round(float(processing.get("avg_time_per_frame_ms", 0.0)), 2),
        "fps": round(float(processing.get("fps", 0.0)), 2),
        "proc_frames": int(detector_stats.get("frame_count", 0)),
        "unique_tracks": int(summary.get("unique_tracks_total", 0)),
        "M": int(gender_total.get("M", 0)),
        "F": int(gender_total.get("F", 0)),
        "U": int(gender_total.get("Unknown", 0)),
        "M_pct": round(100 * gender_total.get("M", 0) / total_gender, 1) if total_gender > 0 else 0,
        "F_pct": round(100 * gender_total.get("F", 0) / total_gender, 1) if total_gender > 0 else 0,
        "U_pct": round(100 * gender_total.get("Unknown", 0) / total_gender, 1) if total_gender > 0 else 0,
        "gender_calls": int(gender_metrics.get("total_calls", 0)),
        "gender_p50_ms": round(float(gender_metrics.get("p50_latency_ms", 0)), 1),
        "gender_p95_ms": round(float(gender_metrics.get("p95_latency_ms", 0)), 1),
    }


def print_comparison_table(scenarios: List[Tuple[str, str]], results: List[Optional[Dict]], baseline_idx: int = 0):
    """Print formatted comparison table."""
    baseline = results[baseline_idx]
    if baseline is None:
        print("ERROR: Baseline report not found!")
        return
    
    print("\n" + "="*120)
    print("IMPROVEMENT EXPERIMENTS COMPARISON REPORT")
    print("="*120)
    print(f"\nBaseline: {scenarios[baseline_idx][1]}")
    print(f"Video: Processed {baseline['proc_frames']} frames, {baseline['unique_tracks']} unique tracks\n")
    
    # Header
    header = (
        f"{'Scenario':<30} "
        f"{'Time(s)':<8} "
        f"{'Avg(ms)':<8} "
        f"{'FPS':<6} "
        f"{'Tracks':<7} "
        f"{'M':<5} "
        f"{'F':<5} "
        f"{'U':<5} "
        f"{'M%':<5} "
        f"{'F%':<5} "
        f"{'U%':<5} "
        f"{'P50(ms)':<8} "
        f"{'P95(ms)':<9}"
    )
    print(header)
    print("-" * 120)
    
    # Baseline row
    b = baseline
    print(
        f"{scenarios[baseline_idx][1]:<30} "
        f"{b['time_s']:<8} "
        f"{b['avg_ms']:<8.1f} "
        f"{b['fps']:<6.1f} "
        f"{b['unique_tracks']:<7} "
        f"{b['M']:<5} "
        f"{b['F']:<5} "
        f"{b['U']:<5} "
        f"{b['M_pct']:<5.1f} "
        f"{b['F_pct']:<5.1f} "
        f"{b['U_pct']:<5.1f} "
        f"{b['gender_p50_ms']:<8.1f} "
        f"{b['gender_p95_ms']:<9.1f} "
        f"[BASELINE]"
    )
    
    # Improvement rows
    for i, (scenario_id, scenario_name) in enumerate(scenarios):
        if i == baseline_idx:
            continue
        
        r = results[i]
        if r is None:
            print(f"{scenario_name:<30} {'N/A':<8} {'N/A':<8} {'N/A':<6} {'N/A':<7} {'N/A':<5} {'N/A':<5} {'N/A':<5} {'N/A':<5} {'N/A':<5} {'N/A':<5} {'N/A':<8} {'N/A':<9}")
            continue
        
        # Calculate differences
        time_diff = r['time_s'] - b['time_s']
        ms_diff = r['avg_ms'] - b['avg_ms']
        fps_diff = r['fps'] - b['fps']
        m_diff = r['M'] - b['M']
        f_diff = r['F'] - b['F']
        u_diff = r['U'] - b['U']
        m_pct_diff = r['M_pct'] - b['M_pct']
        f_pct_diff = r['F_pct'] - b['F_pct']
        
        time_str = f"{r['time_s']} ({time_diff:+.1f})"
        ms_str = f"{r['avg_ms']:.1f} ({ms_diff:+.1f})"
        fps_str = f"{r['fps']:.1f} ({fps_diff:+.1f})"
        m_str = f"{r['M']} ({m_diff:+d})"
        f_str = f"{r['F']} ({f_diff:+d})"
        u_str = f"{r['U']} ({u_diff:+d})"
        m_pct_str = f"{r['M_pct']:.1f} ({m_pct_diff:+.1f})"
        f_pct_str = f"{r['F_pct']:.1f} ({f_pct_diff:+.1f})"
        
        print(
            f"{scenario_name:<30} "
            f"{time_str:<15} "
            f"{ms_str:<15} "
            f"{fps_str:<12} "
            f"{r['unique_tracks']:<7} "
            f"{m_str:<12} "
            f"{f_str:<12} "
            f"{u_str:<12} "
            f"{m_pct_str:<12} "
            f"{f_pct_str:<12} "
            f"{r['U_pct']:<5.1f} "
            f"{r['gender_p50_ms']:<8.1f} "
            f"{r['gender_p95_ms']:<9.1f}"
        )
    
    print("-" * 120)
    print("\nNotes:")
    print("  - Values in parentheses show difference from baseline")
    print("  - M/F/U: Male/Female/Unknown counts")
    print("  - M%/F%/U%: Percentage of total gender classifications")
    print("  - P50/P95: Latency percentiles for gender classification")


def main() -> None:
    ap = argparse.ArgumentParser(description="Summarize improvement experiments")
    ap.add_argument("--base", type=Path, required=True, help="Base output/videos directory")
    ap.add_argument("--video", type=str, required=True, help="Video stem (no extension)")
    ap.add_argument("--output", type=Path, help="Optional: Save markdown report to file")
    args = ap.parse_args()
    
    results = []
    for scenario_id, _ in IMPROVEMENT_SCENARIOS:
        rpt = load_report(args.base, scenario_id, args.video)
        if rpt is None:
            results.append(None)
        else:
            results.append(extract_metrics(rpt))
    
    print_comparison_table(IMPROVEMENT_SCENARIOS, results)
    
    if args.output:
        # Save as markdown
        with args.output.open("w") as f:
            f.write("# Improvement Experiments Comparison Report\n\n")
            f.write(f"**Baseline:** {IMPROVEMENT_SCENARIOS[0][1]}\n\n")
            f.write("| Scenario | Time(s) | Avg(ms) | FPS | Tracks | M | F | U | M% | F% | U% | P50(ms) | P95(ms) |\n")
            f.write("|----------|---------|---------|-----|--------|---|---|---|----|----|----|---------|---------|\n")
            
            baseline = results[0]
            if baseline:
                f.write(
                    f"| {IMPROVEMENT_SCENARIOS[0][1]} | "
                    f"{baseline['time_s']} | {baseline['avg_ms']:.1f} | "
                    f"{baseline['fps']:.1f} | {baseline['unique_tracks']} | "
                    f"{baseline['M']} | {baseline['F']} | {baseline['U']} | "
                    f"{baseline['M_pct']:.1f} | {baseline['F_pct']:.1f} | {baseline['U_pct']:.1f} | "
                    f"{baseline['gender_p50_ms']:.1f} | {baseline['gender_p95_ms']:.1f} |\n"
                )
            
            for i, (scenario_id, scenario_name) in enumerate(IMPROVEMENT_SCENARIOS[1:], 1):
                r = results[i]
                if r:
                    f.write(
                        f"| {scenario_name} | {r['time_s']} | {r['avg_ms']:.1f} | "
                        f"{r['fps']:.1f} | {r['unique_tracks']} | {r['M']} | {r['F']} | {r['U']} | "
                        f"{r['M_pct']:.1f} | {r['F_pct']:.1f} | {r['U_pct']:.1f} | "
                        f"{r['gender_p50_ms']:.1f} | {r['gender_p95_ms']:.1f} |\n"
                    )
        
        print(f"\nReport saved to: {args.output}")


if __name__ == "__main__":
    main()

