#!/usr/bin/env python3
"""
Redis manager for lightweight caching of recent tracks/detections.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class RedisManager:
    """Thin wrapper around redis-py with JSON serialization."""

    def __init__(self, url: str, default_ttl_seconds: int = 60) -> None:
        self.url = url
        self.default_ttl_seconds = default_ttl_seconds
        from typing import Any as _Any
        self._client: Optional[_Any] = None
        self._connect()

    def _connect(self) -> None:
        try:
            import redis

            self._client = redis.Redis.from_url(self.url)
            self._client.ping()
            logger.info("Redis connected: %s", self.url)
        except Exception as e:
            logger.warning("Redis connection failed: %s", e)
            self._client = None

    def cache_track(
        self,
        session_id: str,
        track_id: int,
        payload: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> None:
        if self._client is None:
            return
        try:
            key = f"track:{session_id}:{track_id}"
            self._client.setex(
                key, ttl or self.default_ttl_seconds, json.dumps(payload)
            )
        except Exception as e:
            logger.warning("cache_track failed: %s", e)

    def get_track(self, session_id: str, track_id: int) -> Optional[Dict[str, Any]]:
        if self._client is None:
            return None
        try:
            key = f"track:{session_id}:{track_id}"
            raw = self._client.get(key)
            if not raw:
                return None
            return json.loads(raw)
        except Exception as e:
            logger.warning("get_track failed: %s", e)
            return None
