#!/usr/bin/env python3
import types
from datetime import datetime

import pytest

from src.modules.database.models import PersonDetection, PersonTrack
from src.modules.database.postgres_manager import PostgresManager
from src.modules.database.redis_manager import RedisManager


class _FakeCursor:
    def __init__(self) -> None:
        self.executed = []

    def mogrify(self, _tpl: str, _params: dict) -> bytes:  # minimal stub
        return b"(1)"

    def execute(self, sql: str, params: tuple | None = None) -> None:
        self.executed.append((sql, params))

    def __enter__(self) -> "_FakeCursor":
        return self

    def __exit__(self, *_args) -> None:  # noqa: ANN002, ANN003
        return None


class _FakeConn:
    def __init__(self) -> None:
        self.cur = _FakeCursor()
        self.commits = 0

    def cursor(self) -> _FakeCursor:
        return self.cur

    def commit(self) -> None:
        self.commits += 1


class _FakePool:
    def __init__(self) -> None:
        self.conn = _FakeConn()

    def getconn(self) -> _FakeConn:
        return self.conn

    def putconn(self, _c: _FakeConn) -> None:
        return None


def test_postgres_manager_insert_and_upsert_monkeypatch(monkeypatch: pytest.MonkeyPatch) -> None:
    # Monkeypatch pool initializer to fake pool
    def _fake_init_pool(self: PostgresManager) -> None:  # type: ignore[no-redef]
        self._pool = _FakePool()

    monkeypatch.setattr(PostgresManager, "_init_pool", _fake_init_pool)
    mgr = PostgresManager(dsn="postgres://fake")

    det = PersonDetection(
        timestamp=datetime.now(),
        camera_id=1,
        channel_id=1,
        detection_id="d1",
        track_id=123,
        confidence=0.9,
        bbox=(0, 0, 10, 10),
        gender="M",
        gender_confidence=0.88,
        frame_number=5,
    )
    inserted = mgr.insert_detections([det])
    assert inserted == 1

    tr = PersonTrack(
        track_id=123,
        camera_id=1,
        start_time=datetime.now(),
        end_time=None,
        detection_count=10,
        avg_confidence=0.8,
        trajectory=[(0.0, 0.0)],
    )
    mgr.upsert_track(tr)
    # Ensure our fake cursor captured at least one execute call
    pool = mgr._pool  # type: ignore[attr-defined]
    assert isinstance(pool, _FakePool)
    assert len(pool.conn.cur.executed) >= 1


class _FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, bytes] = {}

    def ping(self) -> None:  # pragma: no cover
        return None

    def setex(self, key: str, _ttl: int, value: str) -> None:
        self.store[key] = value.encode("utf-8")

    def get(self, key: str) -> bytes | None:
        return self.store.get(key)


def test_redis_manager_cache_and_get(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeRedis()

    def _fake_connect(self: RedisManager) -> None:  # type: ignore[no-redef]
        self._client = fake

    monkeypatch.setattr(RedisManager, "_connect", _fake_connect)
    mgr = RedisManager(url="redis://fake")
    mgr.cache_track("s", 1, {"a": 1}, ttl=10)
    out = mgr.get_track("s", 1)
    assert out == {"a": 1}


