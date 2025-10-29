#!/usr/bin/env python3
"""
Object tracker for detected persons.

Uses Kalman filter-based tracking for robust multi-object tracking.
Optimized for person detection use case.
"""

import logging
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)


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
        if self._last_bbox is None:
            self.bbox = bbox
        else:
            self.bbox = self._ema_smooth(self._last_bbox, bbox, ema_alpha)
        self._last_bbox = self.bbox.copy()
        self.confidence = confidence
        self.hits += 1
        self.time_since_update = 0
    
    def predict(self) -> None:
        """Predict next position (simple constant velocity model)."""
        self.age += 1
        self.time_since_update += 1
    
    @staticmethod
    def _ema_smooth(prev_bbox: np.ndarray, new_bbox: np.ndarray, alpha: float) -> np.ndarray:
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
        ema_alpha: float = 0.5
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
        bbox = detection['bbox']
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
    
    def update(self, detections: List[Dict]) -> List[Dict]:
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
        
        # If no detections, just return confirmed tracks
        if len(detections) == 0:
            return self._get_confirmed_tracks()
        
        # If no tracks yet, create new tracks
        if len(self.tracks) == 0:
            for detection in detections:
                bbox = self._convert_detection(detection)
                track = Track(
                    track_id=self.next_id,
                    bbox=bbox,
                    confidence=detection['confidence'],
                    class_name=detection.get('class_name', 'person')
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
            track.update(bbox, detections[d_idx]['confidence'], self.ema_alpha)
        
        # Handle unmatched detections (create new tracks)
        for d_idx in unmatched_detections:
            bbox = self._convert_detection(detections[d_idx])
            track = Track(
                track_id=self.next_id,
                bbox=bbox,
                confidence=detections[d_idx]['confidence'],
                class_name=detections[d_idx].get('class_name', 'person')
            )
            track.hits = self.min_hits  # Start confirmed
            self.tracks.append(track)
            self.next_id += 1
        
        # Remove old tracks
        self.tracks = [
            t for t in self.tracks
            if t.time_since_update <= self.max_age
        ]
        
        # Return tracked detections with track_id attached
        return self._attach_track_ids_to_detections(detections, matched_indices)
    
    def _compute_cost_matrix(self, detections: List[Dict]) -> np.ndarray:
        """Compute IoU cost matrix between detections and tracks."""
        if len(detections) == 0 or len(self.tracks) == 0:
            return np.empty((0, 0))
        
        cost_matrix = np.zeros((len(detections), len(self.tracks)))
        
        for d_idx, detection in enumerate(detections):
            detection_bbox = self._convert_detection(detection)
            for t_idx, track in enumerate(self.tracks):
                cost_matrix[d_idx][t_idx] = self._iou(
                    detection_bbox,
                    track.bbox
                )
        
        return cost_matrix
    
    def _associate_detections_to_tracks(self, cost_matrix: np.ndarray) -> List[Tuple[int, int]]:
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
    
    def _get_confirmed_tracks(self) -> List[Dict]:
        """Get confirmed tracks (hits >= min_hits)."""
        confirmed_tracks = []
        
        for track in self.tracks:
            if track.hits >= self.min_hits:
                confirmed_tracks.append({
                    'track_id': track.track_id,
                    'bbox': track.bbox.tolist(),
                    'confidence': track.confidence,
                    'class_name': track.class_name,
                    'age': track.age,
                    'hits': track.hits
                })
        
        return confirmed_tracks
    
    def _attach_track_ids_to_detections(
        self, 
        detections: List[Dict], 
        matched_indices: List[Tuple[int, int]]
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
            detection_copy['track_id'] = t_id
            if t_id is not None:
                # Attach tracker metadata to support downstream gating (e.g., Re-ID policies)
                track = next((t for t in self.tracks if t.track_id == t_id), None)
                if track is not None:
                    detection_copy['hits'] = track.hits
                    detection_copy['time_since_update'] = track.time_since_update
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
            'active_tracks': len(self.tracks),
            'confirmed_tracks': len([t for t in self.tracks if t.hits >= self.min_hits]),
            'next_id': self.next_id,
            'max_age': self.max_age,
            'min_hits': self.min_hits
        }


if __name__ == "__main__":
    # Test the tracker
    logging.basicConfig(level=logging.INFO)
    
    tracker = Tracker()
    
    # Simulate detections
    detections = [
        {'bbox': [100, 100, 50, 80], 'confidence': 0.9, 'class_name': 'person'},
        {'bbox': [200, 150, 60, 90], 'confidence': 0.85, 'class_name': 'person'},
    ]
    
    tracks = tracker.update(detections)
    print(f"Tracked objects: {len(tracks)}")
    
    # Continue with same objects
    tracks = tracker.update(detections)
    print(f"Tracked objects: {len(tracks)}")
    
    stats = tracker.get_statistics()
    print(f"Statistics: {stats}")

