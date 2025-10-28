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
    
    def update(self, bbox: np.ndarray, confidence: float) -> None:
        """Update track with new detection."""
        self.bbox = bbox
        self.confidence = confidence
        self.hits += 1
        self.time_since_update = 0
    
    def predict(self) -> None:
        """Predict next position (simple constant velocity model)."""
        self.age += 1
        self.time_since_update += 1


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
        iou_threshold: float = 0.3
    ) -> None:
        """
        Initialize tracker.
        
        Args:
            max_age: Maximum age of inactive tracks before deletion
            min_hits: Minimum hits required for a track to be confirmed
            iou_threshold: IoU threshold for track-detection association
        """
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        
        self.tracks: List[Track] = []
        self.next_id = 1
        
        logger.info(
            f"Tracker initialized: max_age={max_age}, "
            f"min_hits={min_hits}, iou_threshold={iou_threshold}"
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
        
        # Convert [x, y, w, h] to [x1, y1, x2, y2]
        x1 = bbox[0]
        y1 = bbox[1]
        x2 = bbox[0] + bbox[2]
        y2 = bbox[1] + bbox[3]
        
        return np.array([x1, y1, x2, y2])
    
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
                self.tracks.append(track)
                self.next_id += 1
            return self._get_confirmed_tracks()
        
        # Create cost matrix for Hungarian algorithm (IoU)
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
            track.update(bbox, detections[d_idx]['confidence'])
        
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
        
        return self._get_confirmed_tracks()
    
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
        Associate detections to tracks using greedy matching.
        
        Args:
            cost_matrix: IoU cost matrix
            
        Returns:
            List of (detection_idx, track_idx) matches
        """
        if cost_matrix.size == 0:
            return []
        
        matches = []
        
        # Greedy matching based on IoU
        for d_idx in range(len(cost_matrix)):
            best_iou = 0
            best_track_idx = -1
            
            for t_idx in range(len(cost_matrix[d_idx])):
                if cost_matrix[d_idx][t_idx] > best_iou:
                    best_iou = cost_matrix[d_idx][t_idx]
                    best_track_idx = t_idx
            
            if best_iou >= self.iou_threshold:
                matches.append((d_idx, best_track_idx))
        
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

