#!/usr/bin/env python3
"""
PostgreSQL manager with connection pooling and batch operations.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator, Iterable, Optional

from .models import PersonDetection, PersonTrack

logger = logging.getLogger(__name__)


class PostgresManager:
    """Minimal synchronous PostgreSQL manager (psycopg2 expected)."""

    def __init__(self, dsn: str, pool_minconn: int = 1, pool_maxconn: int = 5) -> None:
        self.dsn = dsn
        self.pool_minconn = pool_minconn
        self.pool_maxconn = pool_maxconn
        from typing import Any as _Any
        self._pool: Optional[_Any] = None
        self._init_pool()

    def _init_pool(self) -> None:
        try:
            from psycopg2 import pool as _pool

            self._pool = _pool.SimpleConnectionPool(
                self.pool_minconn, self.pool_maxconn, self.dsn
            )
            logger.info(
                "PostgreSQL pool initialized (min=%d, max=%d)",
                self.pool_minconn,
                self.pool_maxconn,
            )
        except Exception as e:
            logger.error("Failed to initialize PostgreSQL pool: %s", e)
            self._pool = None

    @contextmanager
    def _conn(self) -> Generator:
        if self._pool is None:
            raise RuntimeError("PostgreSQL pool not initialized")
        conn = self._pool.getconn()
        try:
            yield conn
        finally:
            self._pool.putconn(conn)

    def insert_detections(self, detections: Iterable[PersonDetection]) -> int:
        """Batch insert detections; returns number of rows inserted."""
        rows = list(detections)
        if len(rows) == 0:
            return 0
        placeholders = (
            "(%(timestamp)s,%(camera_id)s,%(channel_id)s,%(detection_id)s,%(track_id)s,"
            "%(confidence)s,%(bbox_x)s,%(bbox_y)s,%(bbox_w)s,%(bbox_h)s,%(gender)s,"
            "%(gender_confidence)s,%(frame_number)s)"
        )
        params = []
        for d in rows:
            x, y, w, h = d.bbox
            params.append(
                {
                    "timestamp": d.timestamp,
                    "camera_id": d.camera_id,
                    "channel_id": d.channel_id,
                    "detection_id": d.detection_id,
                    "track_id": d.track_id,
                    "confidence": d.confidence,
                    "bbox_x": x,
                    "bbox_y": y,
                    "bbox_w": w,
                    "bbox_h": h,
                    "gender": d.gender,
                    "gender_confidence": d.gender_confidence,
                    "frame_number": d.frame_number,
                }
            )
        try:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    # psycopg2 allows passing a list of params dicts expanded by mogrify.
                    vals = []
                    for p in params:
                        vals.append(cur.mogrify(placeholders, p).decode("utf-8"))
                    base = (
                        "INSERT INTO detections (timestamp,camera_id,channel_id,detection_id,"
                        "track_id,confidence,bbox_x,bbox_y,bbox_width,bbox_height,gender,"
                        "gender_confidence,frame_number) VALUES "
                    )
                    final_sql = base + ",".join(vals)
                    cur.execute(final_sql)
                conn.commit()
            return len(rows)
        except Exception as e:
            logger.error("insert_detections failed: %s", e)
            return 0

    def upsert_track(self, track: PersonTrack) -> None:
        """Upsert single track."""
        try:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    up_sql = (
                        "INSERT INTO tracks (track_id,camera_id,start_time,end_time,"
                        "detection_count,avg_confidence,trajectory) VALUES "
                        "(%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (track_id,camera_id) DO UPDATE SET "
                        "end_time=EXCLUDED.end_time, detection_count=EXCLUDED.detection_count, "
                        "avg_confidence=EXCLUDED.avg_confidence, trajectory=EXCLUDED.trajectory"
                    )
                    cur.execute(
                        up_sql,
                        (
                            track.track_id,
                            track.camera_id,
                            track.start_time,
                            track.end_time,
                            track.detection_count,
                            track.avg_confidence,
                            track.trajectory,
                        ),
                    )
                conn.commit()
        except Exception as e:
            logger.error("upsert_track failed: %s", e)
