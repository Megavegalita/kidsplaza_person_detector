#!/usr/bin/env python3
"""
Asynchronous worker for gender classification tasks.

Provides a bounded priority queue with a thread pool to process image crops
without blocking the main video pipeline. Designed for eventual consistency.

Usage:
    worker = AsyncGenderWorker(max_workers=2, queue_size=256, task_timeout_ms=50)
    task_id = worker.enqueue(task)
    result = worker.try_get_result(task_id)  # non-blocking
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from queue import Empty, Full, PriorityQueue
from typing import Callable, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass(order=True)
class _QueuedTask:
    priority: int
    enqueued_at: float
    task_id: str
    func: Callable[[], Tuple[str, float]]  # gender, confidence only (age disabled)


class AsyncGenderWorker:
    """Threaded worker processing gender tasks from a bounded priority queue."""

    def __init__(
        self,
        max_workers: int = 2,
        queue_size: int = 256,
        task_timeout_ms: int = 50,
    ) -> None:
        self._queue: PriorityQueue[_QueuedTask] = PriorityQueue(maxsize=queue_size)
        self._results: Dict[str, Tuple[str, float, float]] = {}  # gender, conf, timestamp (age disabled)
        self._results_lock = threading.Lock()
        self._shutdown = threading.Event()
        self._workers = [
            threading.Thread(
                target=self._run_loop, name=f"gender-worker-{i}", daemon=True
            )
            for i in range(max_workers)
        ]
        self._task_timeout_ms = max(1, task_timeout_ms)

        for w in self._workers:
            w.start()

        logger.info(
            "AsyncGenderWorker started with %d workers, queue=%d, timeout=%dms",
            max_workers,
            queue_size,
            self._task_timeout_ms,
        )

    def enqueue(
        self, task_id: str, priority: int, func: Callable[[], Tuple[str, float, int, float]]
    ) -> bool:
        """Enqueue a classification task.

        Args:
            task_id: Unique identifier (e.g., f"{session}:{track_id}:{frame}")
            priority: Lower value processes sooner (0 is highest)
            func: Callable returning (gender_label, confidence) - age disabled

        Returns:
            True if enqueued, False if queue is full.
        """
        try:
            self._queue.put_nowait(
                _QueuedTask(
                    priority=priority,
                    enqueued_at=time.time(),
                    task_id=task_id,
                    func=func,
                )
            )
            return True
        except Full:
            logger.debug("AsyncGenderWorker queue full; dropping task_id=%s", task_id)
            return False

    def try_get_result(self, task_id: str) -> Optional[Tuple[str, float, float]]:
        """Get result if available.

        Returns (gender, confidence, completed_at) or None. Age disabled.
        """
        with self._results_lock:
            return self._results.get(task_id)

    def get_queue_size(self) -> int:
        """Return current queue size (approximate)."""
        try:
            return self._queue.qsize()
        except Exception:
            return 0

    def _run_loop(self) -> None:
        while not self._shutdown.is_set():
            try:
                queued: _QueuedTask = self._queue.get(timeout=0.1)  # may raise Empty
            except Empty:
                continue
            try:
                start = time.time()
                # Soft timeout: if task exceeds budget, we still let it finish
                gender, conf = queued.func()  # Age disabled - only gender
                done = time.time()
                if (done - start) * 1000.0 > self._task_timeout_ms:
                    logger.debug(
                        "Gender task exceeded timeout: %.1fms > %dms (task_id=%s)",
                        (done - start) * 1000.0,
                        self._task_timeout_ms,
                        queued.task_id,
                    )
                with self._results_lock:
                    self._results[queued.task_id] = (gender, conf, done)
            except Exception as e:
                logger.warning("Gender task failed: %s (task_id=%s)", e, queued.task_id)
            finally:
                self._queue.task_done()

    def shutdown(self) -> None:
        """Signal workers to stop."""
        self._shutdown.set()
        # Drain queue fast
        while True:
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except Empty:
                break
