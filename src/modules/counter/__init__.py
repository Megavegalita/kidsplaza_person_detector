#!/usr/bin/env python3
"""
Counter module for person counting.

This module provides zone-based person counting functionality with support
for polygon and line-based zones, plus daily per-person counting with cross-channel
person identity management.
"""

from src.modules.counter.daily_person_counter import DailyPersonCounter
from src.modules.counter.person_identity_manager import PersonIdentityManager
from src.modules.counter.zone_counter import ZoneCounter, point_in_polygon, line_crossing

__all__ = [
    "ZoneCounter",
    "DailyPersonCounter",
    "PersonIdentityManager",
    "point_in_polygon",
    "line_crossing",
]

