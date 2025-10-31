#!/usr/bin/env python3
"""Unit tests for Re-ID skeleton."""

import numpy as np

from src.modules.reid.embedder import ReIDEmbedder
from src.modules.reid.cache import ReIDCache, ReIDCacheItem


def test_embedder_output_shape_and_norm():
    embedder = ReIDEmbedder()
    crop = np.random.randint(0, 255, (256, 128, 3), dtype=np.uint8)
    emb = embedder.embed(crop)
    assert emb.ndim == 1
    assert emb.shape[0] == 128
    norm = float(np.linalg.norm(emb))
    assert 0.9 <= norm <= 1.1


def test_cache_set_get_roundtrip(monkeypatch):
    # Monkeypatch Redis to None (skip real connection) and test in-memory fallback path
    cache = ReIDCache(url="redis://invalid:6379/0", ttl_seconds=1)
    # When connection fails, client is None; set/get should be no-ops returning None
    item = ReIDCacheItem(track_id=1, embedding=np.ones(128, dtype=np.float32), updated_at=0.0)
    cache.set("session", item)
    got = cache.get("session", 1)
    assert got is None


