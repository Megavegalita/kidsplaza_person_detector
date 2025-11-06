#!/usr/bin/env python3
"""
Database models for detections and tracks.

Defines light Pydantic-style dataclasses for validation and clarity.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple


@dataclass
class PersonDetection:
    """Person detection row destined for PostgreSQL."""

    timestamp: datetime
    camera_id: int
    channel_id: int
    detection_id: str
    track_id: Optional[int]
    confidence: float
    bbox: Tuple[int, int, int, int]
    gender: Optional[str]
    gender_confidence: Optional[float]
    frame_number: int


@dataclass
class PersonTrack:
    """Person track row destined for PostgreSQL."""

    track_id: int
    camera_id: int
    start_time: datetime
    end_time: Optional[datetime]
    detection_count: int
    avg_confidence: float
    trajectory: List[Tuple[float, float]]
