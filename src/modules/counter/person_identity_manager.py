#!/usr/bin/env python3
"""
Person Identity Manager for cross-channel person tracking using Re-ID.

This module maintains consistent person_id across all channels by matching
Re-ID embeddings, ensuring one person = one unique ID system-wide.
"""

import hashlib
import json
import logging
from datetime import date, datetime
from typing import Dict, Optional, Tuple

import numpy as np

from src.modules.reid.cache import ReIDCache

logger = logging.getLogger(__name__)


class PersonIdentityManager:
    """
    Manages unique person identities across channels using Re-ID embeddings.

    Uses Redis to store person_id -> embedding mappings and track_id -> person_id mappings.
    Matches new tracks to existing persons based on cosine similarity of embeddings.
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        similarity_threshold: float = 0.75,
        redis_ttl_seconds: int = 86400,  # 24 hours
    ) -> None:
        """
        Initialize Person Identity Manager.

        Args:
            redis_url: Redis connection URL. If None, uses default from config.
            similarity_threshold: Minimum cosine similarity to match persons (0.0-1.0).
            redis_ttl_seconds: TTL for Redis keys (default: 24 hours = 86400).
        """
        self.similarity_threshold = float(similarity_threshold)
        self.redis_ttl_seconds = int(redis_ttl_seconds)

        # Use ReIDCache for Redis connection
        self.cache: Optional[ReIDCache] = None
        try:
            self.cache = ReIDCache(url=redis_url, ttl_seconds=redis_ttl_seconds)
            if self.cache._client is None:
                logger.warning(
                    "PersonIdentityManager: Redis not available, using in-memory mode"
                )
                self.cache = None
        except Exception as e:
            logger.warning("PersonIdentityManager: Failed to connect to Redis: %s", e)
            self.cache = None

        # In-memory fallback (if Redis unavailable)
        self._in_memory_persons: Dict[str, np.ndarray] = {}  # person_id -> embedding
        self._in_memory_tracks: Dict[str, str] = {}  # "channel:track_id" -> person_id
        self._next_person_id: int = 1

    def _key_person(self, person_id: str) -> str:
        """Generate Redis key for person embedding."""
        return f"person:identity:{person_id}"

    def _key_track_mapping(self, channel_id: int, track_id: int) -> str:
        """Generate Redis key for track_id -> person_id mapping."""
        return f"person:track:{channel_id}:{track_id}"

    def _key_person_counter(self, person_id: str, zone_id: str, date_str: str) -> str:
        """Generate Redis key for daily person counter (per zone)."""
        return f"person:counter:{person_id}:{zone_id}:{date_str}"

    def _key_person_counter_global(self, person_id: str, date_str: str) -> str:
        """Generate Redis key for global daily person counter (across all zones/channels)."""
        return f"person:counter:global:{person_id}:{date_str}"

    def _cosine_similarity(
        self, a: np.ndarray, b: np.ndarray, eps: float = 1e-9
    ) -> float:
        """Calculate cosine similarity between two vectors."""
        norm_a = float(np.linalg.norm(a))
        norm_b = float(np.linalg.norm(b))
        if norm_a < eps or norm_b < eps:
            return 0.0
        dot_product = float(np.dot(a, b))
        return dot_product / (norm_a * norm_b)

    def _generate_person_id(
        self, channel_id: int, track_id: int, timestamp: float
    ) -> str:
        """Generate unique person_id."""
        # Format: P{channel_id}_{timestamp_hash}_{counter}
        timestamp_str = str(int(timestamp))
        hash_input = f"{channel_id}_{track_id}_{timestamp_str}".encode()
        hash_hex = hashlib.md5(hash_input).hexdigest()[:8]
        return f"P{channel_id}_{hash_hex}"

    def _get_today_date(self) -> str:
        """Get today's date string (YYYY-MM-DD)."""
        return date.today().isoformat()

    def get_or_assign_person_id(
        self,
        channel_id: int,
        track_id: int,
        embedding: Optional[np.ndarray],
    ) -> Optional[str]:
        """
        Get or assign person_id for a track based on Re-ID embedding.

        Args:
            channel_id: Camera channel ID.
            track_id: Track ID from tracker.
            embedding: Re-ID embedding vector (L2-normalized, 128-dim).

        Returns:
            person_id if embedding is valid, None otherwise.
        """
        if embedding is None or embedding.size == 0:
            return None

        # Check if track already has assigned person_id
        existing_person_id = self._get_track_person_id(channel_id, track_id)
        if existing_person_id is not None:
            return existing_person_id

        # Try to match with existing persons
        matched_person_id = self._match_person(embedding)
        if matched_person_id is not None:
            # Assign matched person_id to this track
            self._set_track_person_id(channel_id, track_id, matched_person_id)
            logger.debug(
                "Matched track %d (channel %d) to existing person %s",
                track_id,
                channel_id,
                matched_person_id,
            )
            return matched_person_id

        # Create new person_id
        timestamp = datetime.now().timestamp()
        new_person_id = self._generate_person_id(channel_id, track_id, timestamp)

        # Store person embedding
        self._set_person_embedding(new_person_id, embedding)

        # Assign to track
        self._set_track_person_id(channel_id, track_id, new_person_id)

        logger.info(
            "Created new person %s for track %d (channel %d)",
            new_person_id,
            track_id,
            channel_id,
        )
        return new_person_id

    def _get_track_person_id(self, channel_id: int, track_id: int) -> Optional[str]:
        """Get person_id for a track_id."""
        key = self._key_track_mapping(channel_id, track_id)

        if self.cache and self.cache._client:
            try:
                raw = self.cache._client.get(key)
                if raw:
                    return raw.decode("utf-8")
            except Exception as e:
                logger.debug("Redis get failed for track mapping: %s", e)

        # In-memory fallback
        in_mem_key = f"{channel_id}:{track_id}"
        return self._in_memory_tracks.get(in_mem_key)

    def _set_track_person_id(
        self, channel_id: int, track_id: int, person_id: str
    ) -> None:
        """Store track_id -> person_id mapping."""
        key = self._key_track_mapping(channel_id, track_id)

        if self.cache and self.cache._client:
            try:
                self.cache._client.setex(key, self.redis_ttl_seconds, person_id)
            except Exception as e:
                logger.debug("Redis set failed for track mapping: %s", e)

        # In-memory fallback
        in_mem_key = f"{channel_id}:{track_id}"
        self._in_memory_tracks[in_mem_key] = person_id

    def _set_person_embedding(self, person_id: str, embedding: np.ndarray) -> None:
        """Store person_id -> embedding mapping."""
        key = self._key_person(person_id)

        if self.cache and self.cache._client:
            try:
                payload = {
                    "person_id": person_id,
                    "embedding": embedding.tolist(),
                    "updated_at": datetime.now().timestamp(),
                }
                self.cache._client.setex(
                    key, self.redis_ttl_seconds, json.dumps(payload)
                )
            except Exception as e:
                logger.debug("Redis set failed for person embedding: %s", e)

        # In-memory fallback
        self._in_memory_persons[person_id] = embedding.copy()

    def _get_person_embedding(self, person_id: str) -> Optional[np.ndarray]:
        """Get embedding for a person_id."""
        if self.cache and self.cache._client:
            try:
                key = self._key_person(person_id)
                raw = self.cache._client.get(key)
                if raw:
                    data = json.loads(raw)
                    return np.array(data["embedding"], dtype=np.float32)
            except Exception as e:
                logger.debug("Redis get failed for person embedding: %s", e)

        # In-memory fallback
        return self._in_memory_persons.get(person_id)

    def _match_person(self, embedding: np.ndarray) -> Optional[str]:
        """
        Match embedding to existing person.

        Args:
            embedding: Re-ID embedding to match.

        Returns:
            Matched person_id if similarity >= threshold, None otherwise.
        """
        best_match: Optional[str] = None
        best_similarity: float = 0.0

        # Try Redis first
        if self.cache and self.cache._client:
            try:
                # Scan for all person keys
                pattern = "person:identity:*"
                cursor = 0
                while True:
                    cursor, keys = self.cache._client.scan(
                        cursor, match=pattern, count=100
                    )
                    for key in keys:
                        try:
                            raw = self.cache._client.get(key)
                            if raw:
                                data = json.loads(raw)
                                existing_emb = np.array(
                                    data["embedding"], dtype=np.float32
                                )
                                similarity = self._cosine_similarity(
                                    embedding, existing_emb
                                )

                                if similarity > best_similarity:
                                    best_similarity = similarity
                                    best_match = data["person_id"]
                        except Exception:
                            continue

                    if cursor == 0:
                        break
            except Exception as e:
                logger.debug("Redis scan failed: %s", e)

        # Check in-memory fallback
        for person_id, existing_emb in self._in_memory_persons.items():
            similarity = self._cosine_similarity(embedding, existing_emb)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = person_id

        # Return match if above threshold
        if best_match and best_similarity >= self.similarity_threshold:
            logger.debug(
                "Matched embedding to person %s (similarity=%.3f)",
                best_match,
                best_similarity,
            )
            return best_match

        return None

    def check_daily_count(
        self, person_id: str, zone_id: str, event_type: str
    ) -> Tuple[bool, Dict[str, int]]:
        """
        Check if person can be counted for today (once per day per event type, globally across all channels).

        Uses global counter to ensure one person = one enter/exit count per day regardless of channel/zone.

        Args:
            person_id: Person ID.
            zone_id: Zone ID (for display/logging, but counting is global).
            event_type: "enter" or "exit".

        Returns:
            Tuple of (can_count, global_counts) where can_count is True if not yet counted today.
            global_counts contains {"enter": count, "exit": count} for this person globally today.
        """
        date_str = self._get_today_date()
        global_key = self._key_person_counter_global(person_id, date_str)

        global_counts = {"enter": 0, "exit": 0}

        if self.cache and self.cache._client:
            try:
                # Check global counter (across all channels/zones)
                raw = self.cache._client.get(global_key)
                if raw:
                    global_counts = json.loads(raw)

                # Check if already counted this event type today globally (only once per day across all channels)
                if global_counts.get(event_type, 0) >= 1:
                    logger.debug(
                        "Person %s already counted %s today globally (enter=%d, exit=%d)",
                        person_id,
                        event_type,
                        global_counts["enter"],
                        global_counts["exit"],
                    )
                    return (False, global_counts.copy())

                # Increment global count (mark as counted globally)
                global_counts[event_type] = 1

                # Store with TTL until end of day
                ttl_until_midnight = 86400 - int(datetime.now().timestamp() % 86400)
                if (
                    ttl_until_midnight < 3600
                ):  # If less than 1 hour to midnight, add buffer
                    ttl_until_midnight = 86400  # Full day buffer
                self.cache._client.setex(
                    global_key, ttl_until_midnight, json.dumps(global_counts)
                )

                logger.info(
                    "Global daily count updated: person %s %s (global totals: enter=%d, exit=%d)",
                    person_id,
                    event_type,
                    global_counts["enter"],
                    global_counts["exit"],
                )
                return (True, global_counts.copy())
            except Exception as e:
                logger.warning("Redis counter update failed: %s", e)

        # In-memory fallback (not recommended for production)
        in_mem_key_global = f"global:{person_id}:{date_str}"
        if not hasattr(self, "_in_memory_counters_global"):
            self._in_memory_counters_global = {}
        if in_mem_key_global not in self._in_memory_counters_global:
            self._in_memory_counters_global[in_mem_key_global] = {"enter": 0, "exit": 0}

        global_counts = self._in_memory_counters_global[in_mem_key_global].copy()

        # Check and update
        if global_counts.get(event_type, 0) >= 1:
            return (False, global_counts)

        global_counts[event_type] = 1
        self._in_memory_counters_global[in_mem_key_global] = global_counts

        return (True, global_counts.copy())

    def get_global_daily_counts(self, person_id: str) -> Dict[str, int]:
        """
        Get global daily counts for a person (across all channels/zones).

        Args:
            person_id: Person ID.

        Returns:
            Dict with {"enter": count, "exit": count} globally for today.
        """
        date_str = self._get_today_date()
        global_key = self._key_person_counter_global(person_id, date_str)

        if self.cache and self.cache._client:
            try:
                raw = self.cache._client.get(global_key)
                if raw:
                    return json.loads(raw)
            except Exception as e:
                logger.debug("Failed to get global counts: %s", e)

        # In-memory fallback
        in_mem_key = f"global:{person_id}:{date_str}"
        if hasattr(self, "_in_memory_counters_global"):
            return self._in_memory_counters_global.get(
                in_mem_key, {"enter": 0, "exit": 0}
            )

        return {"enter": 0, "exit": 0}

    def get_all_global_daily_counts(self) -> Dict[str, Dict[str, int]]:
        """
        Get all global daily counts for all persons (across all channels).

        Returns:
            Dict mapping person_id to {"enter": count, "exit": count}.
        """
        all_counts: Dict[str, Dict[str, int]] = {}
        date_str = self._get_today_date()

        if self.cache and self.cache._client:
            try:
                # Scan for all global counter keys for today
                pattern = f"person:counter:global:*:{date_str}"
                cursor = 0
                while True:
                    cursor, keys = self.cache._client.scan(
                        cursor, match=pattern, count=100
                    )
                    for key in keys:
                        try:
                            raw = self.cache._client.get(key)
                            if raw:
                                # Extract person_id from key: person:counter:global:{person_id}:{date}
                                key_parts = key.decode("utf-8").split(":")
                                if len(key_parts) >= 5:
                                    person_id = key_parts[3]
                                    counts = json.loads(raw)
                                    all_counts[person_id] = counts
                        except Exception:
                            continue

                    if cursor == 0:
                        break
            except Exception as e:
                logger.debug("Failed to scan global counters: %s", e)

        return all_counts

    def reset_daily_counts(self) -> None:
        """Reset all daily counters (call at midnight)."""
        # Redis TTL will handle expiration automatically
        # Just clear in-memory cache if exists
        if hasattr(self, "_in_memory_counters"):
            self._in_memory_counters = {}
        if hasattr(self, "_in_memory_counters_global"):
            self._in_memory_counters_global = {}
