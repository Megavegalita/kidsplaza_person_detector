#!/usr/bin/env python3
"""
ArcFace-based face Re-ID embedder using insightface.

Takes a person crop, detects a face, and returns a 512-dim L2-normalized
embedding. Falls back to lightweight embedder if no face found or model missing.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np

from .embedder import ReIDEmbedder


logger = logging.getLogger(__name__)


class ArcFaceEmbedder(ReIDEmbedder):
    """Face-based embedder using insightface ArcFace model.

    If ArcFace cannot be loaded or a face is not detected, falls back to the
    base class embedding method to avoid breaking the pipeline.
    """

    def __init__(self) -> None:
        super().__init__()
        self._face_app = self._try_init_arcface()
        if self._face_app is not None:
            logger.info("ArcFaceEmbedder initialized (insightface)")
        else:
            logger.warning("ArcFace not available; falling back to lightweight embedder")

    def _try_init_arcface(self):
        try:
            import insightface

            face_app = insightface.app.FaceAnalysis(name="buffalo_l")
            # Prepare with default settings; auto-download on first use
            face_app.prepare(ctx_id=0, det_size=(640, 640))
            return face_app
        except Exception as e:
            logger.warning("Failed to initialize ArcFace: %s", e)
            return None

    def embed(self, crop: np.ndarray) -> np.ndarray:
        if self._face_app is None or crop is None or crop.size == 0:
            return super().embed(crop)

        try:
            faces = self._face_app.get(crop)
            if not faces:
                return super().embed(crop)
            # Choose the largest face (by bbox area)
            def _area(f) -> float:
                x1, y1, x2, y2 = f.bbox.astype(int)
                return float(max(0, x2 - x1) * max(0, y2 - y1))

            face = max(faces, key=_area)
            if getattr(face, "normed_embedding", None) is not None:
                emb = np.asarray(face.normed_embedding, dtype=np.float32)
                # Ensure L2-normalized
                norm = float(np.linalg.norm(emb))
                if norm > 0:
                    emb = (emb / norm).astype(np.float32)
                return emb
            elif getattr(face, "embedding", None) is not None:
                emb = np.asarray(face.embedding, dtype=np.float32)
                norm = float(np.linalg.norm(emb))
                if norm > 0:
                    emb = (emb / norm).astype(np.float32)
                return emb
            return super().embed(crop)
        except Exception as e:
            logger.warning("ArcFace embedding failed; fallback used: %s", e)
            return super().embed(crop)


