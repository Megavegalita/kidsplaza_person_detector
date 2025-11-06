#!/usr/bin/env python3
"""
Staff Voting Cache - Manages voting mechanism for staff classification.

Similar to Re-ID voting: accumulates votes across frames to determine
if a track is staff or customer. Uses confidence weighting for votes.
"""

import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class StaffVotingCache:
    """
    Voting cache for staff classification with confidence weighting.

    Accumulates votes across frames to determine if a track is staff or customer.
    Once threshold is reached, classification is fixed for that track.
    """

    def __init__(
        self,
        vote_window: int = 10,
        vote_threshold: int = 4,
        cache_keep_frames: int = 30,
    ) -> None:
        """
        Initialize staff voting cache.

        Args:
            vote_window: Number of frames to consider for voting.
            vote_threshold: Number of votes needed to fix classification.
            cache_keep_frames: Keep cache entries for N frames after track disappears.
        """
        self.vote_window = vote_window
        self.vote_threshold = vote_threshold
        self.cache_keep_frames = cache_keep_frames

        # Cache structure: track_id -> vote_data
        self._cache: Dict[int, Dict] = {}

        # Frame counter for cleanup
        self._current_frame = 0

        logger.info(
            "Staff voting cache initialized: window=%d, threshold=%d, keep_frames=%d",
            vote_window,
            vote_threshold,
            cache_keep_frames,
        )

    def vote(
        self,
        track_id: int,
        classification: str,
        confidence: float,
        frame_num: int = 0,
    ) -> Tuple[Optional[str], bool]:
        """
        Vote for track classification with confidence weighting.

        Args:
            track_id: Track ID.
            classification: "staff" or "customer".
            confidence: Confidence score (0.0-1.0).
            frame_num: Current frame number.

        Returns:
            Tuple of (final_classification, is_fixed):
            - final_classification: "staff", "customer", or None (if not fixed yet).
            - is_fixed: True if classification is fixed, False if still voting.
        """
        self._current_frame = frame_num

        # Initialize cache entry if new track
        if track_id not in self._cache:
            self._cache[track_id] = {
                "votes_staff": 0.0,  # Weighted votes
                "votes_customer": 0.0,
                "vote_count": 0,  # Number of votes
                "first_frame": frame_num,
                "last_frame": frame_num,
                "fixed": False,
                "final_classification": None,
            }

        entry = self._cache[track_id]
        entry["last_frame"] = frame_num

        # If already fixed, return cached result
        if entry["fixed"]:
            return entry["final_classification"], True

        # Add weighted vote
        # Confidence weight: high confidence (>0.7) = 2.0, medium (0.5-0.7) = 1.5, low (<0.5) = 1.0
        if confidence > 0.7:
            weight = 2.0
        elif confidence > 0.5:
            weight = 1.5
        else:
            weight = 1.0

        if classification == "staff":
            entry["votes_staff"] += weight
        elif classification == "customer":
            entry["votes_customer"] += weight
        else:
            # Unknown classification, vote as customer (default)
            entry["votes_customer"] += weight * 0.5  # Lower weight for unknown

        entry["vote_count"] += 1

        # Check if threshold reached
        total_votes = entry["votes_staff"] + entry["votes_customer"]
        frames_since_first = frame_num - entry["first_frame"] + 1

        # Determine winner
        if entry["votes_staff"] >= self.vote_threshold:
            # Staff wins
            entry["fixed"] = True
            entry["final_classification"] = "staff"
            logger.debug(
                "Track %d fixed as STAFF: votes_staff=%.2f, votes_customer=%.2f, votes=%d",
                track_id,
                entry["votes_staff"],
                entry["votes_customer"],
                entry["vote_count"],
            )
            return "staff", True

        elif entry["votes_customer"] >= self.vote_threshold:
            # Customer wins
            entry["fixed"] = True
            entry["final_classification"] = "customer"
            logger.debug(
                "Track %d fixed as CUSTOMER: votes_staff=%.2f, votes_customer=%.2f, votes=%d",
                track_id,
                entry["votes_staff"],
                entry["votes_customer"],
                entry["vote_count"],
            )
            return "customer", True

        elif frames_since_first >= self.vote_window:
            # Vote window expired, use majority vote
            if entry["votes_staff"] > entry["votes_customer"]:
                entry["fixed"] = True
                entry["final_classification"] = "staff"
                logger.debug(
                    "Track %d fixed as STAFF (majority after window): votes_staff=%.2f, votes_customer=%.2f",
                    track_id,
                    entry["votes_staff"],
                    entry["votes_customer"],
                )
                return "staff", True
            else:
                entry["fixed"] = True
                entry["final_classification"] = "customer"
                logger.debug(
                    "Track %d fixed as CUSTOMER (majority after window): votes_staff=%.2f, votes_customer=%.2f",
                    track_id,
                    entry["votes_staff"],
                    entry["votes_customer"],
                )
                return "customer", True

        # Still voting
        return None, False

    def get_classification(self, track_id: int) -> Optional[str]:
        """
        Get cached classification for track.

        Args:
            track_id: Track ID.

        Returns:
            "staff", "customer", or None if not fixed yet.
        """
        if track_id not in self._cache:
            return None

        entry = self._cache[track_id]
        if entry["fixed"]:
            return entry["final_classification"]

        return None

    def cleanup(self, active_track_ids: set, frame_num: int = 0) -> None:
        """
        Clean up cache entries for stale tracks.

        Args:
            active_track_ids: Set of currently active track IDs.
            frame_num: Current frame number.
        """
        self._current_frame = frame_num

        stale_track_ids = []
        for track_id, entry in self._cache.items():
            if track_id not in active_track_ids:
                # Track is not active, check if should remove
                frames_since_last = frame_num - entry["last_frame"]
                if frames_since_last > self.cache_keep_frames:
                    stale_track_ids.append(track_id)

        for track_id in stale_track_ids:
            del self._cache[track_id]
            logger.debug("Removed stale track %d from staff voting cache", track_id)

        logger.debug(
            "Cache cleanup: removed %d stale tracks, %d active entries",
            len(stale_track_ids),
            len(self._cache),
        )

    def get_stats(self) -> Dict:
        """Get cache statistics."""
        total = len(self._cache)
        fixed_staff = sum(
            1 for e in self._cache.values() if e.get("final_classification") == "staff"
        )
        fixed_customer = sum(
            1
            for e in self._cache.values()
            if e.get("final_classification") == "customer"
        )
        voting = total - fixed_staff - fixed_customer

        return {
            "total_tracks": total,
            "fixed_staff": fixed_staff,
            "fixed_customer": fixed_customer,
            "still_voting": voting,
        }
