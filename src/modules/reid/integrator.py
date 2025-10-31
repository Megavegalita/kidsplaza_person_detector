#!/usr/bin/env python3
"""
Utilities to integrate Re-ID into tracking pipeline.
"""

from __future__ import annotations

import logging
import time
from typing import Dict, List

import numpy as np

from .cache import ReIDCache, ReIDCacheItem
from .embedder import ReIDEmbedder

logger = logging.getLogger(__name__)


def cosine_similarity(a: np.ndarray, b: np.ndarray, eps: float = 1e-9) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom < eps:
        return 0.0
    return float(np.dot(a, b) / denom)


def integrate_reid_for_tracks(
    frame: np.ndarray,
    detections_with_tracks: List[Dict],
    embedder: ReIDEmbedder,
    cache: ReIDCache,
    session_id: str,
    every_k_frames: int = 10,
    frame_index: int = 0,
    max_per_frame: int = 5,
    min_interval_frames: int = 30,
    iou_tie_margin: float = 0.1,
    max_embeddings: int = 1,
    append_mode: bool = False,
    aggregation_method: str = "single",
) -> None:
    """
    Compute and cache embeddings for tracked detections at a reduced frequency.

    Args:
        frame: Full frame image
        detections_with_tracks: Detections containing `track_id` and `bbox` (xyxy)
        embedder: Re-ID embedder instance
        cache: Re-ID cache adapter
        session_id: Session identifier for namespacing cache keys
        every_k_frames: Compute embeddings every K frames
        frame_index: Current frame index
    """
    if every_k_frames < 0:
        return  # disabled

    try:
        from modules.detection.image_processor import ImageProcessor

        processor = ImageProcessor()
        embeds_done = 0
        for det in detections_with_tracks:
            if embeds_done >= max_per_frame:
                break
            track_id = det.get("track_id")
            if track_id is None:
                continue
            # Only for confirmed tracks
            hits = int(det.get("hits", 0))
            if hits <= 0:
                continue
            # On-demand policy: only every K frames and with interval gating
            if every_k_frames > 0 and (frame_index % every_k_frames) != 0:
                continue
            cached = cache.get(session_id, int(track_id))
            if cached is not None:
                last_age = (
                    frame_index - int(cached.updated_at)
                    if cached.updated_at > 1e6
                    else 0
                )
                # If we encoded recently, skip
                if last_age < min_interval_frames:
                    continue
            bbox = det.get("bbox")
            if bbox is None:
                continue
            x1, y1, x2, y2 = map(int, bbox)
            crop = processor.crop_person(
                frame, np.array([x1, y1, x2, y2], dtype=np.int32)
            )
            if crop is None:
                continue
            emb = embedder.embed(crop)
            # Multi-embedding support: append up to max_embeddings if requested
            embeddings_list = None
            if append_mode and max_embeddings > 1:
                prev = cache.get(session_id, int(track_id))
                existing = []
                if prev is not None and prev.embeddings:
                    existing = prev.embeddings
                elif (
                    prev is not None
                    and prev.embedding is not None
                    and prev.embedding.size > 0
                ):
                    existing = [prev.embedding.tolist()]
                existing.append(emb.tolist())
                # keep only most recent max_embeddings
                embeddings_list = existing[-int(max_embeddings) :]

            cache.set(
                session_id,
                ReIDCacheItem(
                    track_id=int(track_id),
                    embedding=emb,
                    updated_at=time.time(),
                    embeddings=embeddings_list,
                    aggregation_method=aggregation_method,
                ),
            )
            embeds_done += 1
    except Exception as e:
        logger.warning("Re-ID integration skipped due to error: %s", e)
