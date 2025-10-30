#!/usr/bin/env python3
"""
Lightweight Re-ID embedder interface.

Provides an abstraction for generating normalized embeddings from person crops.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ReIDConfig:
    """Configuration for Re-ID embedder."""

    target_size: Tuple[int, int] = (64, 128)
    normalize: bool = True


class ReIDEmbedder:
    """Generates L2-normalized embeddings for person crops."""

    def __init__(self, config: Optional[ReIDConfig] = None) -> None:
        self.config = config or ReIDConfig()
        self._proj: Optional[np.ndarray] = None
        self._init_projection()
        logger.info(
            "ReIDEmbedder initialized: target_size=%s normalize=%s",
            self.config.target_size,
            self.config.normalize,
        )

    def _preprocess(self, crop: np.ndarray) -> np.ndarray:
        import cv2

        h, w = self.config.target_size[1], self.config.target_size[0]
        resized = cv2.resize(crop, (w, h))
        if self.config.normalize:
            resized = resized.astype(np.float32) / 255.0
        return resized

    def _init_projection(self) -> None:
        # Precompute a fixed lightweight projection once (deterministic)
        w, h = self.config.target_size
        in_dim = h * w * 3
        rng = np.random.default_rng(12345)
        self._proj = rng.standard_normal((128, in_dim), dtype=np.float32) * 0.05

    def _forward_model(self, tensor: np.ndarray) -> np.ndarray:
        # Lightweight linear projection as placeholder for real backbone
        assert self._proj is not None
        flat = tensor.flatten().astype(np.float32)
        # Ensure length matches; pad or trim if needed
        if flat.shape[0] < self._proj.shape[1]:
            pad = np.zeros(self._proj.shape[1] - flat.shape[0], dtype=np.float32)
            flat = np.concatenate([flat, pad], axis=0)
        elif flat.shape[0] > self._proj.shape[1]:
            flat = flat[: self._proj.shape[1]]
        embedding = self._proj @ flat
        return embedding.astype(np.float32)

    def _l2_normalize(self, vec: np.ndarray, eps: float = 1e-9) -> np.ndarray:
        norm = float(np.linalg.norm(vec))
        if norm < eps:
            return vec
        return (vec / norm).astype(np.float32)

    def embed(self, crop: np.ndarray) -> np.ndarray:
        """
        Compute a normalized embedding for a person crop.

        Args:
            crop: Person image crop (H, W, 3) in uint8

        Returns:
            L2-normalized embedding vector (dim 128)
        """
        tensor = self._preprocess(crop)
        embedding = self._forward_model(tensor)
        return self._l2_normalize(embedding)
