#!/usr/bin/env python3
"""
Unit tests for tracking module.
"""

from typing import List, Dict
import numpy as np

from src.modules.tracking.tracker import Tracker


def _make_det(x1: float, y1: float, x2: float, y2: float, conf: float = 0.9) -> Dict:
    return {
        "bbox": np.array([x1, y1, x2, y2], dtype=np.float32),
        "confidence": conf,
        "class_name": "person",
    }


def test_tracker_assigns_ids_and_persists():
    tracker = Tracker(max_age=5, min_hits=1, iou_threshold=0.3, ema_alpha=0.0)

    dets_frame1: List[Dict] = [
        _make_det(10, 10, 50, 60),
        _make_det(100, 100, 150, 170),
    ]
    tracked1 = tracker.update(dets_frame1)
    assert len(tracked1) == 2
    ids1 = [d.get("track_id") for d in tracked1]
    assert all(i is not None for i in ids1)

    # Slight movement, should keep same IDs
    dets_frame2: List[Dict] = [
        _make_det(12, 12, 52, 62),
        _make_det(102, 102, 152, 172),
    ]
    tracked2 = tracker.update(dets_frame2)
    ids2 = [d.get("track_id") for d in tracked2]
    assert ids1 == ids2


def test_tracker_lifecycle_removal():
    tracker = Tracker(max_age=2, min_hits=1, iou_threshold=0.3, ema_alpha=0.0)

    dets: List[Dict] = [_make_det(20, 20, 60, 80)]
    _ = tracker.update(dets)

    # No detections for a few frames; track should be removed after max_age
    _ = tracker.update([])
    _ = tracker.update([])

    # New detection far away should create a new id
    dets2: List[Dict] = [_make_det(200, 200, 240, 260)]
    tracked = tracker.update(dets2)
    assert len(tracked) == 1
    assert tracked[0].get("track_id") is not None


def test_tracker_ema_smoothing_effect():
    # With EMA alpha > 0, bbox should move smoothly towards new position
    tracker = Tracker(max_age=5, min_hits=1, iou_threshold=0.3, ema_alpha=0.5)

    det1 = [_make_det(0, 0, 10, 10)]
    _ = tracker.update(det1)

    # Large jump
    det2 = [_make_det(100, 100, 110, 110)]
    _ = tracker.update(det2)

    # Confirm internal state bbox is between start and end due to EMA
    assert len(tracker.tracks) == 1
    bbox = tracker.tracks[0].bbox
    # x1 should be between 0 and 100
    assert 0.0 < float(bbox[0]) < 100.0


