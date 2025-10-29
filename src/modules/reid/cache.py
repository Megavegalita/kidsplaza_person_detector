#!/usr/bin/env python3
"""
Redis-backed cache for Re-ID embeddings per track.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import json
import logging
import os
import time

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ReIDCacheItem:
    track_id: int
    embedding: np.ndarray
    updated_at: float


class ReIDCache:
    """Thin Redis-like cache adapter for Re-ID embeddings."""

    def __init__(self, url: Optional[str] = None, ttl_seconds: int = 60) -> None:
        self.url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.ttl_seconds = ttl_seconds
        self._client = None
        self._connect()

    def _connect(self) -> None:
        try:
            import redis  # type: ignore

            self._client = redis.Redis.from_url(self.url)
            # simple ping
            self._client.ping()
            logger.info("ReIDCache connected to %s", self.url)
        except Exception as e:
            logger.warning("ReIDCache connection failed: %s (cache disabled)", e)
            self._client = None

    def _key(self, session_id: str, track_id: int) -> str:
        return f"track:{session_id}:{track_id}:embed"

    def set(self, session_id: str, item: ReIDCacheItem) -> None:
        if self._client is None:
            return
        payload = {
            "track_id": item.track_id,
            "embedding": item.embedding.tolist(),
            "updated_at": item.updated_at,
        }
        try:
            self._client.setex(
                self._key(session_id, item.track_id), self.ttl_seconds, json.dumps(payload)
            )
        except Exception as e:
            logger.warning("ReIDCache.set failed: %s", e)

    def get(self, session_id: str, track_id: int) -> Optional[ReIDCacheItem]:
        if self._client is None:
            return None
        try:
            raw = self._client.get(self._key(session_id, track_id))
            if not raw:
                return None
            data = json.loads(raw)
            return ReIDCacheItem(
                track_id=int(data["track_id"]),
                embedding=np.array(data["embedding"], dtype=np.float32),
                updated_at=float(data["updated_at"]),
            )
        except Exception as e:
            logger.warning("ReIDCache.get failed: %s", e)
            return None


