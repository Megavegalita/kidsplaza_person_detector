#!/usr/bin/env python3
"""
Redis-backed cache for Re-ID embeddings per track.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ReIDCacheItem:
    track_id: int
    embedding: np.ndarray
    updated_at: float
    # Optional multi-embedding support
    embeddings: Optional[List[List[float]]] = None
    aggregation_method: str = "single"


class ReIDCache:
    """Thin Redis-like cache adapter for Re-ID embeddings."""

    def __init__(self, url: Optional[str] = None, ttl_seconds: int = 60) -> None:
        # Ensure url is always a concrete string for downstream clients
        env_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.url: str = url if url is not None else str(env_url)
        self.ttl_seconds = ttl_seconds
        from typing import Any as _Any
        self._client: Optional[_Any] = None
        self._connect()

    def _connect(self) -> None:
        try:
            import redis

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
        payload: Dict[str, Any] = {
            "track_id": item.track_id,
            "embedding": item.embedding.tolist()
            if item.embedding is not None
            else None,
            "updated_at": item.updated_at,
        }
        if item.embeddings is not None:
            payload["embeddings"] = item.embeddings
        if item.aggregation_method:
            payload["aggregation_method"] = item.aggregation_method
        try:
            self._client.setex(
                self._key(session_id, item.track_id),
                self.ttl_seconds,
                json.dumps(payload),
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
            embeddings_list = data.get("embeddings")
            item = ReIDCacheItem(
                track_id=int(data["track_id"]),
                embedding=np.array(data.get("embedding", []), dtype=np.float32)
                if data.get("embedding") is not None
                else np.array([], dtype=np.float32),
                updated_at=float(data.get("updated_at", 0.0)),
                embeddings=embeddings_list
                if isinstance(embeddings_list, list)
                else None,
                aggregation_method=str(data.get("aggregation_method", "single")),
            )
            return item
        except Exception as e:
            logger.warning("ReIDCache.get failed: %s", e)
            return None
