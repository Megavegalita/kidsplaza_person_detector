#!/usr/bin/env python3
"""
Benchmark scenarios for gender classification improvements.

Runs multiple scenarios by invoking process_video_file.py with different configs,
collects logs per scenario, and prepares report paths for later aggregation.
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Dict, List


def run_scenario(
    video: Path, model_path: Path, output_dir: Path, name: str, args: Dict[str, str]
) -> Path:
    out_dir = output_dir / name
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd: List[str] = [
        sys.executable,
        str(Path(__file__).parent / "process_video_file.py"),
        str(video),
        "--model",
        str(model_path),
        "--output",
        str(out_dir),
        "--run-id",
        name,
    ]
    for k, v in args.items():
        cmd.append(k)
        if v:
            cmd.append(v)
    log_path = out_dir / f"run_{name}.log"
    with log_path.open("w") as lf:
        subprocess.run(cmd, stdout=lf, stderr=subprocess.STDOUT, check=False)
    # process_video_file is expected to write a report JSON if enabled in pipeline
    # we return an expected report path for downstream use
    return out_dir / f"report_{video.stem}.json"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark gender improvements scenarios"
    )
    parser.add_argument("video", type=Path, help="Input video file")
    parser.add_argument(
        "--model", type=Path, default=Path("yolov8n.pt"), help="YOLOv8 model path"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/videos"),
        help="Output directory root for scenarios",
    )
    args = parser.parse_args()

    scenarios = {
        # 1) Baseline, e=20, conf=0.4, no face, no adaptive
        "base_e20_c04": {
            "--reid-enable": "",
            "--gender-enable": "",
            "--gender-every-k": "20",
            "--gender-max-per-frame": "4",
            "--gender-model-type": "timm_mobile",
            "--gender-min-confidence": "0.4",
            "--no-annotate": "",
        },
        # 2) Baseline stricter confidence
        "base_e20_c06": {
            "--reid-enable": "",
            "--gender-enable": "",
            "--gender-every-k": "20",
            "--gender-max-per-frame": "4",
            "--gender-model-type": "timm_mobile",
            "--gender-min-confidence": "0.6",
            "--no-annotate": "",
        },
        # 3) Baseline lower frequency
        "base_e30_c04": {
            "--reid-enable": "",
            "--gender-enable": "",
            "--gender-every-k": "30",
            "--gender-max-per-frame": "4",
            "--gender-model-type": "timm_mobile",
            "--gender-min-confidence": "0.4",
            "--no-annotate": "",
        },
        # 4) Face-first
        "face_e20_c04_k5": {
            "--reid-enable": "",
            "--gender-enable": "",
            "--gender-every-k": "20",
            "--gender-max-per-frame": "4",
            "--gender-model-type": "timm_mobile",
            "--gender-min-confidence": "0.4",
            "--gender-enable-face-detection": "",
            "--gender-face-every-k": "5",
            "--no-annotate": "",
        },
        # 5) Adaptive only
        "adapt_e20_c04": {
            "--reid-enable": "",
            "--gender-enable": "",
            "--gender-every-k": "20",
            "--gender-max-per-frame": "4",
            "--gender-model-type": "timm_mobile",
            "--gender-min-confidence": "0.4",
            "--gender-adaptive-enabled": "",
            "--gender-queue-high-watermark": "200",
            "--gender-queue-low-watermark": "100",
            "--no-annotate": "",
        },
        # 6) Face-first + stricter confidence
        "face_e20_c06_k5": {
            "--reid-enable": "",
            "--gender-enable": "",
            "--gender-every-k": "20",
            "--gender-max-per-frame": "4",
            "--gender-model-type": "timm_mobile",
            "--gender-min-confidence": "0.6",
            "--gender-enable-face-detection": "",
            "--gender-face-every-k": "5",
            "--no-annotate": "",
        },
        # 7) Combined
        "combo_e20_c04_k5": {
            "--reid-enable": "",
            "--gender-enable": "",
            "--gender-every-k": "20",
            "--gender-max-per-frame": "4",
            "--gender-model-type": "timm_mobile",
            "--gender-min-confidence": "0.4",
            "--gender-enable-face-detection": "",
            "--gender-face-every-k": "5",
            "--gender-adaptive-enabled": "",
            "--gender-queue-high-watermark": "200",
            "--gender-queue-low-watermark": "100",
            "--no-annotate": "",
        },
        # 8) Combined + stricter confidence
        "combo_e20_c06_k5": {
            "--reid-enable": "",
            "--gender-enable": "",
            "--gender-every-k": "20",
            "--gender-max-per-frame": "4",
            "--gender-model-type": "timm_mobile",
            "--gender-min-confidence": "0.6",
            "--gender-enable-face-detection": "",
            "--gender-face-every-k": "5",
            "--gender-adaptive-enabled": "",
            "--gender-queue-high-watermark": "200",
            "--gender-queue-low-watermark": "100",
            "--no-annotate": "",
        },
    }

    args.output.mkdir(parents=True, exist_ok=True)

    for name, sc_args in scenarios.items():
        print(f"Running scenario: {name}")
        report_path = run_scenario(args.video, args.model, args.output, name, sc_args)
        print(f"Scenario '{name}' completed. Report: {report_path}")


if __name__ == "__main__":
    main()
