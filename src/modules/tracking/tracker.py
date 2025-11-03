#!/usr/bin/env python3
"""
Object tracker for detected persons.

Uses Kalman filter-based tracking for robust multi-object tracking.
Optimized for person detection use case.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Protocol, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class _SupportsEmbed(Protocol):
    def embed(self, img: np.ndarray) -> np.ndarray:  # pragma: no cover - protocol
        ...


class _SupportsCache(Protocol):
    def get(self, session_id: str, track_id: int) -> object:  # pragma: no cover
        ...


@dataclass
class Track:
    """Represents a tracked object."""

    track_id: int
    bbox: np.ndarray
    confidence: float
    class_name: str
    age: int = 0
    hits: int = 0
    time_since_update: int = 0
    _last_bbox: Optional[np.ndarray] = None

    def update(self, bbox: np.ndarray, confidence: float, ema_alpha: float) -> None:
        """Update track with new detection using EMA smoothing on bbox."""
        # Use tighter EMA for more accurate tracking (less smoothing)
        # Reduced smoothing to keep bbox closer to actual detection
        smoothing_alpha = min(ema_alpha, 0.7)  # Cap at 0.7 for more responsive tracking
        if self._last_bbox is None:
            # Use current bbox as previous for first smoothing step
            self.bbox = self._ema_smooth(self.bbox, bbox, smoothing_alpha)
        else:
            self.bbox = self._ema_smooth(self._last_bbox, bbox, smoothing_alpha)
        self._last_bbox = self.bbox.copy()
        self.confidence = confidence
        self.hits += 1
        self.time_since_update = 0

    def predict(self) -> None:
        """Predict next position (simple constant velocity model)."""
        self.age += 1
        self.time_since_update += 1

    @staticmethod
    def _ema_smooth(
        prev_bbox: np.ndarray, new_bbox: np.ndarray, alpha: float
    ) -> np.ndarray:
        """Apply exponential moving average to smooth bbox coordinates."""
        alpha = float(min(max(alpha, 0.0), 1.0))
        return (alpha * new_bbox) + ((1.0 - alpha) * prev_bbox)


class Tracker:
    """
    Multi-object tracker using simple association algorithm.

    Designed for person tracking with high performance requirements.
    Uses IoU-based matching for simplicity and speed.
    """

    def __init__(
        self,
        max_age: int = 30,
        min_hits: int = 3,
        iou_threshold: float = 0.3,
        ema_alpha: float = 0.5,
        reid_enable: bool = False,
        reid_similarity_threshold: float = 0.65,
        reid_cache: Optional[_SupportsCache] = None,
        reid_embedder: Optional[_SupportsEmbed] = None,
        reid_aggregation_method: str = "single",
    ) -> None:
        """
        Initialize tracker.

        Args:
            max_age: Maximum age of inactive tracks before deletion
            min_hits: Minimum hits required for a track to be confirmed
            iou_threshold: IoU threshold for track-detection association
            ema_alpha: EMA smoothing factor for bbox (0.0-1.0)
        """
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        self.ema_alpha = ema_alpha
        # Re-ID params
        self.reid_enable = bool(reid_enable)
        self.reid_similarity_threshold = float(reid_similarity_threshold)
        self._reid_cache: Optional[_SupportsCache] = reid_cache
        self._reid_embedder: Optional[_SupportsEmbed] = reid_embedder
        self._reid_aggregation_method = reid_aggregation_method
        self._reid_matches: int = 0

        self.tracks: List[Track] = []
        self.next_id = 1

        logger.info(
            f"Tracker initialized: max_age={max_age}, "
            f"min_hits={min_hits}, iou_threshold={iou_threshold}, "
            f"ema_alpha={ema_alpha}"
        )

    def _iou(self, box1: np.ndarray, box2: np.ndarray) -> float:
        """
        Calculate IoU between two bounding boxes.

        Args:
            box1: Bounding box [x1, y1, x2, y2]
            box2: Bounding box [x1, y1, x2, y2]

        Returns:
            IoU value (0-1)
        """
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])

        if x2 <= x1 or y2 <= y1:
            return 0.0

        intersection = (x2 - x1) * (y2 - y1)

        box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
        box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])

        union = box1_area + box2_area - intersection

        return intersection / union if union > 0 else 0.0

    def _convert_detection(self, detection: Dict) -> np.ndarray:
        """
        Convert detection bbox format to [x1, y1, x2, y2].

        Args:
            detection: Detection dict with bbox in [x, y, w, h] format

        Returns:
            Bounding box as [x1, y1, x2, y2]
        """
        bbox = detection["bbox"]
        # Support both [x1,y1,x2,y2] and [x,y,w,h]
        x1 = float(bbox[0])
        y1 = float(bbox[1])
        x2 = float(bbox[2])
        y2 = float(bbox[3])
        # Heuristic: if x2>x1 and y2>y1, assume already xyxy
        if x2 > x1 and y2 > y1:
            return np.array([x1, y1, x2, y2], dtype=np.float32)
        # Else treat as xywh
        return np.array([x1, y1, x1 + x2, y1 + y2], dtype=np.float32)

    def update(
        self,
        detections: List[Dict],
        frame: Optional[np.ndarray] = None,
        session_id: Optional[str] = None,
    ) -> List[Dict]:
        """
        Update tracker with new detections.

        Args:
            detections: List of detection dicts with bbox, confidence, class_name

        Returns:
            List of tracked objects with track_id added
        """
        # Predict next positions for all tracks
        for track in self.tracks:
            track.predict()

        # If no detections, return only recently updated tracks (time_since_update <= 10)
        # This prevents showing stale tracks from false positives
        # 10 frames = ~0.4 seconds at 24 FPS - reasonable for continuous display
        if len(detections) == 0:
            return self._get_confirmed_tracks(max_time_since_update=10)

        # If no tracks yet, create new tracks
        if len(self.tracks) == 0:
            for detection in detections:
                bbox = self._convert_detection(detection)
                track = Track(
                    track_id=self.next_id,
                    bbox=bbox,
                    confidence=detection["confidence"],
                    class_name=detection.get("class_name", "person"),
                )
                track.hits = self.min_hits  # Start confirmed
                self.tracks.append(track)
                self.next_id += 1
            # Return detections with track_ids
            matched_indices = [(i, i) for i in range(len(detections))]
            return self._attach_track_ids_to_detections(detections, matched_indices)

        # Create cost matrix for IoU-based matching
        cost_matrix = self._compute_cost_matrix(detections)

        # Associate detections to tracks
        matched_indices = self._associate_detections_to_tracks(cost_matrix)

        # Update matched tracks
        unmatched_detections = set(range(len(detections)))
        matched_tracks = set()

        for d_idx, t_idx in matched_indices:
            matched_tracks.add(t_idx)
            unmatched_detections.discard(d_idx)
            track = self.tracks[t_idx]
            bbox = self._convert_detection(detections[d_idx])
            track.update(bbox, detections[d_idx]["confidence"], self.ema_alpha)

        # Fallback: if greedy IoU matching produced no match, try to match with lower threshold
        # BUT: Only match if IoU is reasonable (> 0.15) to avoid creating duplicate tracks
        # This helps with sudden jumps while preventing false matches
        if len(unmatched_detections) > 0 and len(self.tracks) > 0:
            for d_idx in list(unmatched_detections):
                best_iou = -1.0
                best_t_idx_fb: Optional[int] = None
                det_bbox_fb = self._convert_detection(detections[d_idx])
                for t_idx, track in enumerate(self.tracks):
                    if t_idx in matched_tracks:
                        continue
                    iou_val = float(self._iou(det_bbox_fb, track.bbox))
                    if iou_val > best_iou:
                        best_iou = iou_val
                        best_t_idx_fb = t_idx
                # FIXED: Only match if IoU >= 0.15 (reasonable overlap)
                # This prevents matching detections that are too far apart, avoiding duplicate tracks
                if best_t_idx_fb is not None and best_iou >= 0.15:
                    track = self.tracks[best_t_idx_fb]
                    track.update(det_bbox_fb, detections[d_idx]["confidence"], self.ema_alpha)
                    matched_tracks.add(best_t_idx_fb)
                    matched_indices.append((d_idx, best_t_idx_fb))
                    unmatched_detections.discard(d_idx)
                    logger.debug(
                        "Fallback match: detection %d → track %d (IoU=%.2f)",
                        d_idx, self.tracks[best_t_idx_fb].track_id, best_iou
                    )

        # Handle remaining unmatched detections (try Re-ID match; else create new track)
        for d_idx in list(unmatched_detections):
            bbox = self._convert_detection(detections[d_idx])
            assigned = False
            if (
                self.reid_enable
                and self._reid_cache is not None
                and self._reid_embedder is not None
                and frame is not None
                and session_id
            ):
                try:
                    xi1, yi1, xi2, yi2 = map(int, bbox.tolist())
                    xi1 = max(0, xi1)
                    yi1 = max(0, yi1)
                    xi2 = max(xi1 + 1, xi2)
                    yi2 = max(yi1 + 1, yi2)
                    crop = frame[yi1:yi2, xi1:xi2].copy()
                    if crop.size > 0:
                        det_emb = self._reid_embedder.embed(crop)
                        # Compare against existing tracks' cached embeddings
                        best_sim = -1.0
                        best_t_idx: Optional[int] = None
                        for t_idx, track in enumerate(self.tracks):
                            # Do not consider tracks already matched in this frame
                            if t_idx in matched_tracks:
                                continue
                            cached = self._reid_cache.get(
                                session_id, int(track.track_id)
                            )
                            if cached is None:
                                continue
                            sim = self._compute_reid_similarity(
                                det_emb, cached, self._reid_aggregation_method
                            )
                            if sim > best_sim:
                                best_sim = sim
                                best_t_idx = t_idx
                        # Ensure the selected track is not already used
                        if (
                            best_t_idx is not None
                            and best_t_idx not in matched_tracks
                            and best_sim >= self.reid_similarity_threshold
                        ):
                            # Assign this detection to the best track
                            track = self.tracks[best_t_idx]
                            track.update(
                                bbox, detections[d_idx]["confidence"], self.ema_alpha
                            )
                            matched_tracks.add(best_t_idx)
                            matched_indices.append((d_idx, best_t_idx))
                            unmatched_detections.discard(d_idx)
                            assigned = True
                            self._reid_matches += 1
                except Exception:
                    assigned = False
            if not assigned:
                track = Track(
                    track_id=self.next_id,
                    bbox=bbox,
                    confidence=detections[d_idx]["confidence"],
                    class_name=detections[d_idx].get("class_name", "person"),
                )
                track.hits = self.min_hits  # Start confirmed
                self.tracks.append(track)
                self.next_id += 1
                # Link this new track to detection for downstream consumers
                matched_indices.append((d_idx, len(self.tracks) - 1))

        # Remove old tracks
        self.tracks = [t for t in self.tracks if t.time_since_update <= self.max_age]

        # Return tracked detections with track_id attached
        return self._attach_track_ids_to_detections(detections, matched_indices)

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray, eps: float = 1e-9) -> float:
        denom = float(np.linalg.norm(a) * np.linalg.norm(b))
        if denom < eps:
            return 0.0
        return float(np.dot(a, b) / denom)

    def _compute_reid_similarity(
        self, det_emb: np.ndarray, cached_item: object, method: str
    ) -> float:
        try:
            embs: List[np.ndarray] = []
            # collect embeddings from cache
            if getattr(cached_item, "embeddings", None):
                for e in cached_item.embeddings:  # type: ignore[attr-defined]
                    arr = np.array(e, dtype=np.float32)
                    if arr.ndim == 1 and arr.size > 0:
                        embs.append(arr)
            base = getattr(cached_item, "embedding", None)
            if base is not None and isinstance(base, np.ndarray) and base.size > 0:
                embs.append(base)
            if len(embs) == 0:
                return 0.0
            method = (method or "single").lower()
            if method == "single":
                return self._cosine_similarity(det_emb, embs[-1])
            if method == "max":
                return max(self._cosine_similarity(det_emb, e) for e in embs)
            if method == "mean":
                mean_emb = np.mean(np.stack(embs, axis=0), axis=0).astype(np.float32)
                # normalize mean
                n = float(np.linalg.norm(mean_emb))
                if n > 0:
                    mean_emb = (mean_emb / n).astype(np.float32)
                return self._cosine_similarity(det_emb, mean_emb)
            if method == "avg_sim":
                sims = [self._cosine_similarity(det_emb, e) for e in embs]
                return float(np.mean(sims)) if len(sims) > 0 else 0.0
            return self._cosine_similarity(det_emb, embs[-1])
        except Exception:
            return 0.0

    def _compute_cost_matrix(self, detections: List[Dict]) -> np.ndarray:
        """Compute IoU cost matrix between detections and tracks."""
        if len(detections) == 0 or len(self.tracks) == 0:
            return np.empty((0, 0))

        cost_matrix = np.zeros((len(detections), len(self.tracks)))

        for d_idx, detection in enumerate(detections):
            detection_bbox = self._convert_detection(detection)
            for t_idx, track in enumerate(self.tracks):
                cost_matrix[d_idx][t_idx] = self._iou(detection_bbox, track.bbox)

        return cost_matrix

    def _associate_detections_to_tracks(
        self, cost_matrix: np.ndarray
    ) -> List[Tuple[int, int]]:
        """
        Associate detections to tracks using one-to-one greedy matching by IoU.

        Ensures each detection maps to at most one track and
        each track is used by at most one detection within a frame.

        Args:
            cost_matrix: IoU cost matrix (shape: num_detections x num_tracks)

        Returns:
            List of (detection_idx, track_idx) matches
        """
        if cost_matrix.size == 0:
            return []

        num_detections, num_tracks = cost_matrix.shape

        # Build candidate pairs above threshold
        candidates: List[Tuple[float, int, int]] = []  # (iou, d_idx, t_idx)
        for d_idx in range(num_detections):
            for t_idx in range(num_tracks):
                iou = float(cost_matrix[d_idx][t_idx])
                if iou >= self.iou_threshold:
                    candidates.append((iou, d_idx, t_idx))

        # Sort by IoU descending for greedy selection
        candidates.sort(key=lambda x: x[0], reverse=True)

        used_detections = set()
        used_tracks = set()
        matches: List[Tuple[int, int]] = []

        for iou, d_idx, t_idx in candidates:
            if d_idx in used_detections or t_idx in used_tracks:
                continue
            used_detections.add(d_idx)
            used_tracks.add(t_idx)
            matches.append((d_idx, t_idx))

        return matches

    def _get_confirmed_tracks(self, max_time_since_update: Optional[int] = None) -> List[Dict]:
        """
        Get confirmed tracks (hits >= min_hits).
        
        Args:
            max_time_since_update: Optional limit on time_since_update (for filtering stale tracks)
        """
        confirmed_tracks = []

        for track in self.tracks:
            if track.hits >= self.min_hits:
                # Filter by time_since_update if specified (only show recently updated tracks)
                if max_time_since_update is not None and track.time_since_update > max_time_since_update:
                    continue
                confirmed_tracks.append(
                    {
                        "track_id": track.track_id,
                        "bbox": track.bbox.tolist(),
                        "confidence": track.confidence,
                        "class_name": track.class_name,
                        "age": track.age,
                        "hits": track.hits,
                    }
                )

        return confirmed_tracks

    def _attach_track_ids_to_detections(
        self, detections: List[Dict], matched_indices: List[Tuple[int, int]]
    ) -> List[Dict]:
        """
        Attach track_id to each detection based on matching results.

        Args:
            detections: List of detection dicts
            matched_indices: List of (detection_idx, track_idx) tuples

        Returns:
            List of detections with track_id added
        """
        tracked_detections = []

        # Create mapping from detection index to track_id
        detection_to_track = {}
        for d_idx, t_idx in matched_indices:
            if t_idx < len(self.tracks):
                detection_to_track[d_idx] = self.tracks[t_idx].track_id

        # Attach track_id to each detection
        for i, detection in enumerate(detections):
            detection_copy = detection.copy()
            t_id = detection_to_track.get(i, None)
            detection_copy["track_id"] = t_id
            if t_id is not None:
                # Attach tracker metadata to support downstream gating (e.g., Re-ID policies)
                track = next((t for t in self.tracks if t.track_id == t_id), None)
                if track is not None:
                    detection_copy["hits"] = track.hits
                    detection_copy["time_since_update"] = track.time_since_update
            tracked_detections.append(detection_copy)

        return tracked_detections

    def reset(self) -> None:
        """Reset tracker state."""
        self.tracks = []
        self.next_id = 1
        logger.info("Tracker reset")

    def get_statistics(self) -> Dict:
        """
        Get tracking statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "active_tracks": len(self.tracks),
            "confirmed_tracks": len(
                [t for t in self.tracks if t.hits >= self.min_hits]
            ),
            "next_id": self.next_id,
            "max_age": self.max_age,
            "min_hits": self.min_hits,
            "reid_matches": int(self._reid_matches),
        }


if __name__ == "__main__":
    # Test the tracker
    logging.basicConfig(level=logging.INFO)

    tracker = Tracker()

    # Simulate detections
    detections = [
        {"bbox": [100, 100, 50, 80], "confidence": 0.9, "class_name": "person"},
        {"bbox": [200, 150, 60, 90], "confidence": 0.85, "class_name": "person"},
    ]

    tracks = tracker.update(detections)
    print(f"Tracked objects: {len(tracks)}")

    # Continue with same objects
    tracks = tracker.update(detections)
    print(f"Tracked objects: {len(tracks)}")

    stats = tracker.get_statistics()
    print(f"Statistics: {stats}")
