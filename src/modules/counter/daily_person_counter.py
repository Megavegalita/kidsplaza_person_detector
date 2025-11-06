#!/usr/bin/env python3
"""
Daily Person Counter - tracks per-person enter/exit counts with daily reset.

This module ensures each person is counted only once per day per zone,
regardless of how many times they cross the boundary.
"""

import logging
from typing import Any, Dict, List, Optional

from .person_identity_manager import PersonIdentityManager
from .zone_counter import ZoneCounter

logger = logging.getLogger(__name__)


class DailyPersonCounter:
    """
    Wraps ZoneCounter to provide daily per-person counting.
    
    Uses PersonIdentityManager to get person_id from track_id + Re-ID embedding.
    Only counts each person once per day per zone (for both enter and exit).
    """

    def __init__(
        self,
        zones: List[Dict[str, Any]],
        person_identity_manager: PersonIdentityManager,
    ) -> None:
        """
        Initialize Daily Person Counter.

        Args:
            zones: List of zone configurations.
            person_identity_manager: PersonIdentityManager instance for person ID resolution.
        """
        self.zone_counter = ZoneCounter(zones)
        self.identity_manager = person_identity_manager
        
        # Track person_id for each track_id (per frame)
        self.track_to_person: Dict[int, Optional[str]] = {}
        
        # Track which persons have been counted today per zone
        self.person_zone_counted_today: Dict[str, Dict[str, Dict[str, bool]]] = {}
        # Format: {person_id: {zone_id: {"enter": bool, "exit": bool}}}

    def update(
        self,
        detections: List[Dict[str, Any]],
        frame: Any,
        frame_num: int = 0,
    ) -> Dict[str, Any]:
        """
        Update counter with new detections.

        Args:
            detections: List of detections with track_id and optional person_id/embedding.
            frame: Frame image.
            frame_num: Frame number.

        Returns:
            Dictionary with counts and events, including person_id in events.
        """
        # Filter out staff - only count customers
        # Check both is_staff flag and person_type for compatibility
        customer_detections = [
            det for det in detections
            if det.get("is_staff") is not True
            and det.get("person_type") != "staff"
        ]
        
        if len(customer_detections) < len(detections):
            staff_count = len(detections) - len(customer_detections)
            logger.debug(
                "Filtered out %d staff detection(s), processing %d customer detection(s)",
                staff_count,
                len(customer_detections),
            )
        
        # Step 1: Resolve person_id for each track
        detections_with_person: List[Dict[str, Any]] = []
        
        for det in customer_detections:
            track_id = det.get("track_id")
            if track_id is None:
                continue
            
            # Try to get person_id from detection (if already resolved)
            person_id = det.get("person_id")
            
            # If not available, try to resolve using identity manager
            if person_id is None:
                # Check if we have embedding in detection
                embedding = det.get("reid_embedding")
                if embedding is not None:
                    # Get channel_id from detection or use default
                    channel_id = det.get("channel_id", 0)
                    person_id = self.identity_manager.get_or_assign_person_id(
                        channel_id=channel_id,
                        track_id=track_id,
                        embedding=embedding,
                    )
            
            # Store person_id mapping
            if person_id:
                self.track_to_person[track_id] = person_id
            else:
                self.track_to_person[track_id] = None
            # No channel mapping needed when fallback is disabled
            
            # Add person_id to detection for zone counter (but zone counter still uses track_id internally)
            det_copy = det.copy()
            det_copy["_person_id"] = person_id  # Internal field
            detections_with_person.append(det_copy)

        # Step 2: Update zone counter (still uses track_id for zone state tracking)
        result = self.zone_counter.update(detections_with_person, frame, frame_num)
        
        # Step 3: Filter events to apply daily counting constraint
        filtered_events: List[Dict[str, Any]] = []
        daily_counts: Dict[str, Dict[str, int]] = {}  # {zone_id: {"enter": count, "exit": count}}
        
        for event in result.get("events", []):
            track_id = event.get("track_id")
            zone_id = event.get("zone_id")
            event_type = event.get("type")  # "enter" or "exit"
            
            if track_id is None or zone_id is None or event_type not in ["enter", "exit"]:
                filtered_events.append(event)
                continue
            
            # Get person_id for this track
            person_id = self.track_to_person.get(track_id)
            
            if person_id is None:
                # Allow event without person_id (no daily uniqueness applied)
                event["person_id"] = None
                filtered_events.append(event)
                continue
            
            # Check daily count constraint
            can_count, current_counts = self.identity_manager.check_daily_count(
                person_id=person_id,
                zone_id=zone_id,
                event_type=event_type,
            )
            
            if can_count:
                # Update daily counts (accumulate across all persons)
                if zone_id not in daily_counts:
                    daily_counts[zone_id] = {"enter": 0, "exit": 0}
                daily_counts[zone_id][event_type] += 1
                
                # Add person_id to event
                event["person_id"] = person_id
                filtered_events.append(event)
                
                logger.info(
                    "Daily count: person %s %s zone %s (daily totals: enter=%d, exit=%d)",
                    person_id,
                    event_type,
                    zone_id,
                    current_counts["enter"],
                    current_counts["exit"],
                )
            else:
                # Already counted today - skip
                logger.debug(
                    "Skipping %s for person %s in zone %s (already counted today: enter=%d, exit=%d)",
                    event_type,
                    person_id,
                    zone_id,
                    current_counts["enter"],
                    current_counts["exit"],
                )
        
        # Step 4: Update result with filtered events and daily counts
        result["events"] = filtered_events
        result["daily_counts"] = daily_counts
        
        # Step 5: Get global counts across ALL channels from Redis
        # Query all global counters to get total unique persons counted system-wide
        all_global_counts = self.identity_manager.get_all_global_daily_counts()
        
        unique_persons_entered = set()
        unique_persons_exited = set()
        
        # Count unique persons who have entered/exited globally (across all channels)
        for person_id, counts in all_global_counts.items():
            if counts.get("enter", 0) > 0:
                unique_persons_entered.add(person_id)
            if counts.get("exit", 0) > 0:
                unique_persons_exited.add(person_id)
        
        # Global totals = count of unique persons who entered/exited (synced across all channels)
        global_enter_total = len(unique_persons_entered)
        global_exit_total = len(unique_persons_exited)
        global_unique_total = len(unique_persons_entered | unique_persons_exited)
        
        # Add global counts to all zones for display (separate from local daily counts)
        for zone_id in result["counts"]:
            # Keep local daily_enter/daily_exit from earlier aggregation
            result["counts"][zone_id]["global_enter"] = global_enter_total
            result["counts"][zone_id]["global_exit"] = global_exit_total
            result["counts"][zone_id]["global_unique_persons"] = global_unique_total
        
        return result

    def draw_zones(self, frame: Any) -> Any:
        """Draw zones on frame (delegate to ZoneCounter)."""
        return self.zone_counter.draw_zones(frame)

    def get_counts(self) -> Dict[str, Dict[str, int]]:
        """Get current zone counts (includes daily counts)."""
        return self.zone_counter.get_counts()

    def reset_all_zones(self) -> None:
        """Reset all zone counts."""
        self.zone_counter.reset_all_zones()
        self.person_zone_counted_today = {}

