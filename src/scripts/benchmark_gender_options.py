#!/usr/bin/env python3
"""
Run 3-minute benchmarks for gender model options and print a compact summary.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run_option(
    video: Path,
    model_path: Path,
    output_dir: Path,
    model_type: str,
) -> Path:
    out_dir = output_dir / f"gender_{model_type}"
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(Path(__file__).parent / "process_video_file.py"),
        str(video),
        "--model",
        str(model_path),
        "--output",
        str(out_dir),
        "--tracker-iou-threshold",
        "0.35",
        "--tracker-ema-alpha",
        "0.4",
        "--tracker-max-age",
        "30",
        "--tracker-min-hits",
        "3",
        "--reid-enable",
        "--reid-every-k",
        "20",
        "--gender-enable",
        "--gender-every-k",
        "30",
        "--gender-model-type",
        model_type,
        "--gender-max-per-frame",
        "4",
        "--gender-timeout-ms",
        "50",
        "--gender-queue-size",
        "256",
        "--gender-workers",
        "2",
    ]
    log_path = out_dir / f"run_{model_type}.log"
    with log_path.open("w") as lf:
        subprocess.run(cmd, stdout=lf, stderr=subprocess.STDOUT, check=False)
    return out_dir / f"report_{video.stem}.json"


def summarize(report_path: Path) -> dict:
    if not report_path.exists():
        return {"error": f"missing report: {report_path}"}
    data = json.loads(report_path.read_text())
    proc = data.get("processing", {})
    summ = data.get("summary", {})
    return {
        "unique": summ.get("unique_tracks_total", 0),
        "gender": summ.get("gender_counts_total", {}),
        "time_s": round(proc.get("time_seconds", 0.0), 2),
        "avg_ms": round(proc.get("avg_time_per_frame_ms", 0.0), 2),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video", type=str)
    ap.add_argument("--model", type=str, default="yolov8n.pt")
    ap.add_argument("--output", type=str, default="output/test_video")
    args = ap.parse_args()

    video = Path(args.video)
    model = Path(args.model)
    out = Path(args.output)

    options = ["resnet18_face", "timm_mobile", "timm_efficient"]
    reports = {}
    for opt in options:
        rp = run_option(video, model, out, opt)
        reports[opt] = summarize(rp)

    print("\n=== Gender Options Summary ===")
    for opt in options:
        print(f"- {opt}: {reports[opt]}")


if __name__ == "__main__":
    main()
