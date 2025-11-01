#!/usr/bin/env python3
"""
PostgreSQL manager with connection pooling and batch operations.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator, Iterable, Optional
import time

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
        self._ins_lat_ms: list[float] = []

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
                    t0 = time.monotonic()
                    cur.execute(final_sql)
                conn.commit()
            dur_ms = (time.monotonic() - t0) * 1000.0
            self._record_insert_latency_ms(float(dur_ms))
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

    def upsert_track_gender(
        self, camera_id: int, track_id: int, gender: str, confidence: float
    ) -> None:
        """Upsert gender label per track for later unique counting."""
        try:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    sql = (
                        "INSERT INTO track_genders (camera_id, track_id, gender, confidence) "
                        "VALUES (%s,%s,%s,%s) "
                        "ON CONFLICT (camera_id, track_id) DO UPDATE SET "
                        "gender=EXCLUDED.gender, confidence=EXCLUDED.confidence"
                    )
                    cur.execute(sql, (camera_id, track_id, gender, confidence))
                conn.commit()
        except Exception as e:
            logger.error("upsert_track_gender failed: %s", e)

    def insert_run_gender_summary(
        self,
        run_id: str,
        camera_id: int,
        unique_total: int,
        male_tracks: int,
        female_tracks: int,
        unknown_tracks: int,
    ) -> None:
        """Insert a per-run aggregate of unique IDs by gender."""
        try:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    sql = (
                        "INSERT INTO run_gender_summary "
                        "(run_id, camera_id, unique_total, male_tracks, "
                        "female_tracks, unknown_tracks) VALUES (%s,%s,%s,%s,%s,%s)"
                    )
                    cur.execute(
                        sql,
                        (
                            run_id,
                            camera_id,
                            unique_total,
                            male_tracks,
                            female_tracks,
                            unknown_tracks,
                        ),
                    )
                conn.commit()
        except Exception as e:
            logger.error("insert_run_gender_summary failed: %s", e)

    def _record_insert_latency_ms(self, latency_ms: float) -> None:
        self._ins_lat_ms.append(latency_ms)
        if len(self._ins_lat_ms) > 100:
            self._ins_lat_ms.pop(0)

    def snapshot_metrics(self) -> dict:
        data = list(self._ins_lat_ms)
        if not data:
            return {"insert_p50_ms": 0.0, "insert_p95_ms": 0.0, "samples": 0}
        data.sort()
        n = len(data)
        p50 = data[int(0.5 * (n - 1))]
        p95 = data[int(0.95 * (n - 1))]
        return {"insert_p50_ms": round(p50, 1), "insert_p95_ms": round(p95, 1), "samples": n}
