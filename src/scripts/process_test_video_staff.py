#!/usr/bin/env python3
"""
Process a local video for 60 seconds with detection, tracking, and staff classification.
Displays frames in a window for visual verification.
This script avoids TensorFlow imports and uses only lightweight modules.
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.detection.detector import Detector  # noqa: E402
from modules.detection.image_processor import ImageProcessor  # noqa: E402
from modules.detection.staff_classifier import StaffClassifier  # noqa: E402
from modules.detection.staff_voting_cache import StaffVotingCache  # noqa: E402
from modules.tracking.tracker import Tracker  # noqa: E402

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_video(
    video_path: Path,
    conf_threshold: float = 0.5,
    tracker_max_age: int = 120,
    tracker_min_hits: int = 2,
    tracker_iou_threshold: float = 0.45,
    tracker_ema_alpha: float = 0.75,
    staff_model: str = "models/kidsplaza/best.pt",
    staff_conf: float = 0.25,
    max_seconds: int = 60,
    window_name: str = "Video Test - Kidsplaza",
) -> None:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    logger.info(
        "Video opened: %s (%dx%d @ %.2f FPS)", video_path.name, width, height, fps
    )

    detector = Detector(model_path="yolov8n.pt", conf_threshold=conf_threshold)
    tracker = Tracker(
        max_age=tracker_max_age,
        min_hits=tracker_min_hits,
        iou_threshold=tracker_iou_threshold,
        ema_alpha=tracker_ema_alpha,
        reid_enable=False,
        reid_similarity_threshold=0.65,
        reid_cache=None,
        reid_embedder=None,
        reid_aggregation_method="single",
    )
    imgproc = ImageProcessor()
    staff = StaffClassifier(model_path=staff_model, conf_threshold=staff_conf)
    vote = StaffVotingCache(vote_window=10, vote_threshold=4, cache_keep_frames=30)

    start_time = time.time()
    frame_num = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_num += 1

        # Limit duration
        if time.time() - start_time >= max_seconds:
            logger.info("Reached max_seconds=%d, stopping", max_seconds)
            break

        # Detect persons
        detections, annotated = detector.detect(frame, return_image=True)

        # Track
        detections = tracker.update(detections, frame=frame, session_id="video_test")

        # Staff classification + voting (only on frames with detections)
        active_ids = set()
        if len(detections) > 0:
            for det in detections:
                tid = det.get("track_id")
                if tid is None:
                    continue
                active_ids.add(int(tid))

                bbox = det.get("bbox")
                if bbox is None or len(bbox) < 4:
                    continue
                x1, y1, x2, y2 = map(int, bbox)
                x1 = max(0, min(width - 1, x1))
                y1 = max(0, min(height - 1, y1))
                x2 = max(0, min(width - 1, x2))
                y2 = max(0, min(height - 1, y2))
                if x2 <= x1 or y2 <= y1:
                    continue
                crop = frame[y1:y2, x1:x2]
                if crop.size == 0:
                    continue

                ptype, pconf = staff.classify(crop)
                final_cls, fixed = vote.vote(
                    track_id=int(tid),
                    classification=ptype,
                    confidence=pconf,
                    frame_num=frame_num,
                )
                if fixed and final_cls is not None:
                    det["person_type"] = final_cls
                    det["is_staff"] = final_cls == "staff"
                else:
                    det["person_type"] = ptype
                    det["is_staff"] = ptype == "staff"

        # Cleanup votes for stale tracks
        vote.cleanup(active_track_ids=active_ids, frame_num=frame_num)

        # Draw
        vis = annotated if annotated is not None else frame.copy()
        vis = imgproc.draw_detections(vis, detections)
        cv2.imshow(window_name, vis)
        if (cv2.waitKey(1) & 0xFF) == ord("q"):
            logger.info("User pressed 'q', stopping")
            break

    cap.release()
    try:
        cv2.destroyAllWindows()
    except Exception:
        pass


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Process test video (60s) with display"
    )
    parser.add_argument("video_path", type=str, help="Path to input video file")
    parser.add_argument("--conf-threshold", type=float, default=0.5)
    parser.add_argument("--max-seconds", type=int, default=60)
    parser.add_argument("--staff-model", type=str, default="models/kidsplaza/best.pt")
    parser.add_argument("--staff-conf", type=float, default=0.25)
    args = parser.parse_args()

    run_video(
        video_path=Path(args.video_path),
        conf_threshold=args.conf_threshold,
        staff_model=args.staff_model,
        staff_conf=args.staff_conf,
        max_seconds=args.max_seconds,
    )


if __name__ == "__main__":
    main()
