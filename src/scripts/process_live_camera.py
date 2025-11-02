#!/usr/bin/env python3
"""
Live Camera Processing Script.

This script processes live RTSP camera streams with person detection,
tracking, gender classification, and data storage integration.
"""

import argparse
import logging
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, cast

import cv2  # noqa: E402
import numpy as np

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.modules.camera.camera_config import load_camera_config  # noqa: E402
from src.modules.camera.camera_reader import (CameraReader,  # noqa: E402
                                              CameraReaderError)
from src.modules.database.models import PersonDetection  # noqa: E402
from src.modules.database.postgres_manager import PostgresManager  # noqa: E402
from src.modules.database.redis_manager import RedisManager  # noqa: E402
from src.modules.demographics.async_worker import AsyncGenderWorker  # noqa: E402
from src.modules.demographics.face_detector import FaceDetector  # noqa: E402
from src.modules.demographics.gender_classifier import GenderClassifier  # noqa: E402
from src.modules.demographics.keras_tf_gender_classifier import (  # noqa: E402
    KerasTFGenderClassifier,
)
from src.modules.demographics.metrics import GenderMetrics  # noqa: E402
from src.modules.detection.detector import Detector  # noqa: E402
from src.modules.detection.image_processor import ImageProcessor  # noqa: E402
from src.modules.reid.cache import ReIDCache  # noqa: E402
from src.modules.reid.embedder import ReIDEmbedder  # noqa: E402
from src.modules.reid.arcface_embedder import ArcFaceEmbedder  # noqa: E402
from src.modules.reid.integrator import integrate_reid_for_tracks  # noqa: E402
from src.modules.tracking.tracker import Tracker  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class LiveCameraProcessor:
    """Process live RTSP camera streams with detection pipeline."""

    def __init__(
        self,
        camera_id: int,
        channel_id: int,
        rtsp_url: str,
        model_path: str = "yolov8n.pt",
        output_dir: str = "output/live",
        run_id: Optional[str] = None,
        conf_threshold: float = 0.5,
        tracker_max_age: int = 30,
        tracker_min_hits: int = 3,
        tracker_iou_threshold: float = 0.3,
        tracker_ema_alpha: float = 0.5,
        reid_enable: bool = False,
        reid_use_face: bool = False,
        reid_every_k: int = 10,
        reid_ttl_seconds: int = 60,
        reid_similarity_threshold: float = 0.65,
        gender_enable: bool = False,
        gender_every_k: int = 20,
        gender_model_type: str = "timm_mobile",
        gender_max_per_frame: int = 4,
        gender_timeout_ms: int = 50,
        gender_queue_size: int = 256,
        gender_workers: int = 2,
        gender_min_confidence: float = 0.5,
        gender_voting_window: int = 10,
        gender_female_min_confidence: Optional[float] = None,
        gender_male_min_confidence: Optional[float] = None,
        gender_enable_face_detection: bool = False,
        gender_face_every_k: int = 5,
        gender_cache_ttl_frames: int = 90,
        gender_adaptive_enabled: bool = False,
        gender_queue_high_watermark: int = 200,
        gender_queue_low_watermark: int = 100,
        reid_max_embeddings: int = 1,
        reid_append_mode: bool = False,
        reid_aggregation_method: str = "single",
        db_enable: bool = False,
        db_dsn: Optional[str] = None,
        db_batch_size: int = 100,
        db_flush_interval_ms: int = 500,
        redis_enable: bool = False,
        redis_url: Optional[str] = None,
        max_frames: Optional[int] = None,
        reconnect_interval_seconds: float = 5.0,
        display: bool = False,
        display_fps: float = 15.0,
    ) -> None:
        """
        Initialize live camera processor.

        Args:
            camera_id: Camera ID for database records
            channel_id: Channel ID for this stream
            rtsp_url: RTSP URL for camera stream
            model_path: Path to YOLOv8 model
            output_dir: Output directory for results
            run_id: Optional run identifier
            conf_threshold: Detection confidence threshold
            max_frames: Maximum frames to process (None = unlimited)
            reconnect_interval_seconds: Seconds to wait before reconnecting
        """
        self.camera_id = int(camera_id)
        self.channel_id = int(channel_id)
        self.rtsp_url = str(rtsp_url)
        self.max_frames = max_frames
        self.reconnect_interval = float(reconnect_interval_seconds)

        base_output = Path(output_dir)
        base_output.mkdir(parents=True, exist_ok=True)
        if run_id is None:
            run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = base_output / str(run_id)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.conf_threshold = conf_threshold

        # Initialize detector
        self.detector = Detector(model_path=model_path, conf_threshold=conf_threshold)
        
        # Initialize image processor for drawing detections
        self.processor = ImageProcessor()

        # Initialize tracker
        self.tracker = Tracker(
            max_age=tracker_max_age,
            min_hits=tracker_min_hits,
            iou_threshold=tracker_iou_threshold,
            ema_alpha=tracker_ema_alpha,
            reid_enable=reid_enable,
            reid_similarity_threshold=reid_similarity_threshold,
            reid_cache=None,  # set after cache init
            reid_embedder=None,  # set after embedder init
            reid_aggregation_method=reid_aggregation_method,
        )

        # Initialize Re-ID components (optional)
        self.reid_enable = reid_enable
        self.reid_every_k = reid_every_k
        self.reid_cache = (
            ReIDCache(ttl_seconds=reid_ttl_seconds) if reid_enable else None
        )
        self.reid_embedder: Optional[object]
        if reid_enable:
            self.reid_embedder = ArcFaceEmbedder() if reid_use_face else ReIDEmbedder()
        else:
            self.reid_embedder = None

        if reid_enable:
            self.tracker._reid_cache = self.reid_cache
            self.tracker._reid_embedder = self.reid_embedder

        self.reid_similarity_threshold = reid_similarity_threshold
        self.reid_max_embeddings = reid_max_embeddings
        self.reid_append_mode = reid_append_mode
        self.reid_aggregation_method = reid_aggregation_method

        # Database/Redis integration
        self.db_enable = bool(db_enable)
        self.db_batch_size = int(db_batch_size)
        self.db_flush_interval_ms = int(db_flush_interval_ms)
        self.db_manager: Optional[PostgresManager] = None
        if self.db_enable and db_dsn:
            try:
                self.db_manager = PostgresManager(dsn=db_dsn)
            except Exception as e:
                logger.warning("DB init failed: %s", e)
                self.db_manager = None
                self.db_enable = False

        self.redis_enable = bool(redis_enable)
        self.redis_manager: Optional[RedisManager] = None
        if self.redis_enable and redis_url:
            try:
                self.redis_manager = RedisManager(url=redis_url)
            except Exception as e:
                logger.warning("Redis init failed: %s", e)
                self.redis_manager = None
                self.redis_enable = False

        # DB buffering
        self._db_buffer: List[PersonDetection] = []
        self._last_db_flush_ms: float = time.time() * 1000.0

        # Initialize Gender components (optional)
        self.gender_enable = gender_enable
        self.gender_every_k = gender_every_k
        self.gender_enable_face_detection = gender_enable_face_detection
        self.gender_classifier = (
            GenderClassifier(
                model_type=gender_model_type,
                min_confidence=gender_min_confidence,
                voting_window=gender_voting_window,
                female_min_confidence=gender_female_min_confidence,
                male_min_confidence=gender_male_min_confidence,
            )
            if gender_enable
            else None
        )
        self.face_detector = (
            FaceDetector(min_detection_confidence=0.5)
            if (gender_enable and gender_enable_face_detection)
            else None
        )
        self.face_gender_classifier = None
        if gender_enable and gender_enable_face_detection:
            try:
                self.face_gender_classifier = KerasTFGenderClassifier(
                    min_confidence=gender_min_confidence
                )
            except ImportError:
                logger.warning(
                    "TensorFlow not available; skipping KerasTFGenderClassifier"
                )
        self.gender_worker = (
            AsyncGenderWorker(
                max_workers=gender_workers,
                queue_size=gender_queue_size,
                task_timeout_ms=gender_timeout_ms,
            )
            if gender_enable
            else None
        )
        self.gender_metrics = GenderMetrics() if gender_enable else None
        self.gender_max_per_frame = gender_max_per_frame
        self._pending_gender_tasks: List[str] = []
        self.gender_face_every_k = max(1, int(gender_face_every_k))
        self.gender_cache_ttl_frames = max(1, int(gender_cache_ttl_frames))
        self._face_bbox_cache: Dict[int, np.ndarray] = {}
        self._face_bbox_cache_frame: Dict[int, int] = {}
        self.gender_adaptive_enabled = bool(gender_adaptive_enabled)
        self.gender_queue_high_watermark = int(gender_queue_high_watermark)
        self.gender_queue_low_watermark = int(gender_queue_low_watermark)

        # Display settings
        self.display = bool(display)
        self.display_fps = max(1.0, float(display_fps))  # Minimum 1 FPS
        self.display_frame_skip = max(1, int(24.0 / self.display_fps))  # Skip frames for display
        self._last_display_time = 0.0
        self._display_frame_count = 0
        # Resize for display to reduce lag (max width 1280)
        self.display_max_width = 1280

        # Shutdown flag
        self._shutdown_requested = False

        logger.info("Live camera processor initialized")
        logger.info("Device: %s", self.detector.model_loader.get_device())
        logger.info("MPS enabled: %s", self.detector.model_loader.is_mps_enabled())

    def process_stream(self, session_id: Optional[str] = None) -> Dict:
        """
        Process live camera stream.

        Args:
            session_id: Optional session identifier

        Returns:
            Dictionary with processing results
        """
        if session_id is None:
            session_id = f"live_{self.camera_id}_{self.channel_id}"

        logger.info("Starting live stream processing: %s", self.rtsp_url)

        frame_num = 0
        start_time = time.time()
        unique_track_ids = set()
        track_id_to_gender: Dict[int, str] = {}
        track_id_to_gender_conf: Dict[int, float] = {}
        gender_counts = {"M": 0, "F": 0, "Unknown": 0}

        camera_reader = None
        consecutive_failures = 0
        max_consecutive_failures = 10

        try:
            while not self._shutdown_requested:
                # Initialize or reconnect camera
                if camera_reader is None or not camera_reader.is_streaming():
                    if camera_reader is not None:
                        camera_reader.release()
                        logger.warning("Camera disconnected, reconnecting...")
                        time.sleep(self.reconnect_interval)

                    try:
                        camera_reader = CameraReader(self.rtsp_url)
                        camera_reader._connect()
                        consecutive_failures = 0
                        logger.info("Camera connected successfully")
                    except Exception as e:
                        consecutive_failures += 1
                        logger.error(
                            "Failed to connect to camera (attempt %d/%d): %s",
                            consecutive_failures,
                            max_consecutive_failures,
                            e,
                        )
                        if consecutive_failures >= max_consecutive_failures:
                            logger.error("Max connection failures reached, exiting")
                            break
                        time.sleep(self.reconnect_interval)
                        continue

                # Read frame
                try:
                    frame = camera_reader.read_frame()
                    if frame is None:
                        consecutive_failures += 1
                        logger.warning(
                            "Failed to read frame (consecutive failures: %d)",
                            consecutive_failures,
                        )
                        if consecutive_failures >= max_consecutive_failures:
                            logger.error("Max read failures reached, reconnecting...")
                            camera_reader.release()
                            camera_reader = None
                        continue

                    consecutive_failures = 0
                except CameraReaderError as e:
                    logger.error("Camera reader error: %s", e)
                    if camera_reader is not None:
                        try:
                            camera_reader.release()
                        except Exception:
                            pass
                    camera_reader = None
                    continue

                frame_num += 1

                # Check frame limit
                if self.max_frames is not None and frame_num > self.max_frames:
                    logger.info("Reached max frames limit: %d", self.max_frames)
                    break

                # Process frame (same logic as VideoProcessor)
                frame_height, frame_width = frame.shape[:2]

                # Run detection - only create annotated frame if display is enabled
                detections, annotated = self.detector.detect(
                    frame, return_image=self.display
                )
                
                # Filter false positives: confidence, aspect ratio, size, and area checks
                filtered_detections = []
                for d in detections:
                    conf = d.get("confidence", 0.0)
                    # Strict confidence check - must be above threshold
                    if conf < self.conf_threshold:
                        continue
                    
                    # Get bbox dimensions
                    bbox = d.get("bbox", [])
                    if len(bbox) < 4:
                        continue
                    
                    # Convert numpy array to list if needed
                    if hasattr(bbox, 'tolist'):
                        bbox = bbox.tolist()
                    
                    x1, y1, x2, y2 = float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])
                    w = x2 - x1
                    h = y2 - y1
                    
                    # Validate dimensions
                    if w <= 0 or h <= 0:
                        continue
                    
                    # Calculate metrics
                    aspect_ratio = w / h
                    area = w * h
                    frame_area = frame_width * frame_height
                    area_ratio = area / frame_area if frame_area > 0 else 0
                    
                    # STRICT FILTERING RULES:
                    
                    # 1. Aspect ratio: Person is typically taller than wide (0.25-0.65)
                    #    Motorcycles are wider than tall (> 0.70)
                    #    Make threshold stricter
                    if aspect_ratio > 0.65:  # Stricter: was 0.75, now 0.65
                        if frame_num % 50 == 0:  # Log occasionally
                            logger.debug(
                                "Filtered by aspect ratio: %.3f (w=%.1f, h=%.1f, conf=%.3f)",
                                aspect_ratio, w, h, conf
                            )
                        continue
                    
                    # 2. Minimum size: Person must be reasonably sized
                    #    Increase minimum height requirement
                    if h < 80 or w < 40:  # Stricter: was 50/30, now 80/40
                        if frame_num % 50 == 0:
                            logger.debug(
                                "Filtered by size: w=%.1f, h=%.1f, conf=%.3f", w, h, conf
                            )
                        continue
                    
                    # 3. Maximum size: Filter unrealistically large detections
                    if h > frame_height * 0.85 or w > frame_width * 0.85:
                        continue
                    
                    # 4. Area ratio: Person shouldn't take up too little or too much space
                    #    Very small area ratio might indicate false positive
                    if area_ratio < 0.002:  # Less than 0.2% of frame is suspicious
                        if frame_num % 50 == 0:
                            logger.debug(
                                "Filtered by area ratio: %.4f (area=%d, conf=%.3f)",
                                area_ratio, int(area), conf
                            )
                        continue
                    if area_ratio > 0.7:  # More than 70% of frame is suspicious
                        continue
                    
                    # 5. Height must be significantly greater than width for person
                    #    Additional check: h should be at least 1.5x w for standing person
                    if h < w * 1.3:  # Person height should be at least 1.3x width
                        if frame_num % 50 == 0:
                            logger.debug(
                                "Filtered by height/width ratio: h=%.1f, w=%.1f, ratio=%.2f, conf=%.3f",
                                h, w, h/w, conf
                            )
                        continue
                    
                    # All checks passed
                    filtered_detections.append(d)
                
                detections = filtered_detections
                
                # Re-create annotated frame if display enabled and we filtered detections
                if self.display and annotated is None and len(detections) > 0:
                    annotated = self.processor.draw_detections(frame, detections)
                elif self.display and annotated is not None and len(detections) > 0:
                    # Update annotated frame with filtered detections
                    annotated = self.processor.draw_detections(frame, detections)

                # Run tracking
                tracked_detections = self.tracker.update(
                    detections, frame=frame, session_id=session_id
                )
                detections = tracked_detections

                # Integrate Re-ID
                if (
                    self.reid_enable
                    and self.reid_embedder is not None
                    and self.reid_cache is not None
                ):
                    try:
                        integrate_reid_for_tracks(
                            frame,
                            detections,
                            cast(ReIDEmbedder, self.reid_embedder),
                            self.reid_cache,
                            session_id=session_id,
                            every_k_frames=self.reid_every_k,
                            frame_index=frame_num,
                            max_per_frame=5,
                            min_interval_frames=30,
                            max_embeddings=self.reid_max_embeddings,
                            append_mode=self.reid_append_mode,
                            aggregation_method=self.reid_aggregation_method,
                        )
                    except Exception as e:
                        logger.warning("Re-ID integration error: %s", e)

                # Update unique track id set
                for d in detections:
                    t_id = d.get("track_id")
                    if t_id is not None:
                        unique_track_ids.add(int(t_id))

                # Gender classification (reuse logic from VideoProcessor)
                if (
                    self.gender_enable
                    and self.gender_classifier is not None
                    and self.gender_worker is not None
                ):
                    self._process_gender_classification(
                        frame,
                        detections,
                        frame_num,
                        session_id,
                        frame_width,
                        frame_height,
                        track_id_to_gender,
                        track_id_to_gender_conf,
                    )

                # Display frame if enabled (limit update rate and resize to reduce lag)
                if self.display:
                    current_time = time.time()
                    # Only update display at specified FPS to reduce lag
                    if (
                        current_time - self._last_display_time >= 1.0 / self.display_fps
                    ) or self._last_display_time == 0.0:
                        if annotated is not None:
                            window_name = f"Live Stream - Channel {self.channel_id}"
                            # Resize frame for display to reduce lag (avoid copy if not needed)
                            h, w = annotated.shape[:2]
                            if w > self.display_max_width:
                                scale = self.display_max_width / w
                                new_w = int(w * scale)
                                new_h = int(h * scale)
                                display_frame = cv2.resize(
                                    annotated, (new_w, new_h), interpolation=cv2.INTER_LINEAR
                                )
                            else:
                                display_frame = annotated  # No resize needed, use original
                            cv2.imshow(window_name, display_frame)
                        self._last_display_time = current_time
                        self._display_frame_count += 1
                    # Always check for 'q' key (non-blocking)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q"):
                        logger.info("User pressed 'q', stopping processing.")
                        break

                # Database storage (reuse logic from VideoProcessor)
                if self.db_enable and self.db_manager is not None:
                    self._store_detections(
                        detections,
                        frame_num,
                        track_id_to_gender,
                        track_id_to_gender_conf,
                    )

                # Log progress periodically
                if frame_num % 100 == 0:
                    elapsed = time.time() - start_time
                    fps = frame_num / elapsed if elapsed > 0 else 0
                    logger.info(
                        "Processed %d frames (%.1f FPS) - Tracks: %d",
                        frame_num,
                        fps,
                        len(unique_track_ids),
                    )

        except KeyboardInterrupt:
            logger.info("Processing interrupted by user")
        finally:
            if camera_reader is not None:
                try:
                    if hasattr(camera_reader, "release"):
                        camera_reader.release()
                except Exception:
                    pass

            if self.display:
                cv2.destroyAllWindows()

            # Final DB flush
            if self.db_enable and self.db_manager is not None:
                self._finalize_db_storage(
                    unique_track_ids,
                    track_id_to_gender,
                    track_id_to_gender_conf,
                    session_id,
                )

        elapsed_time = time.time() - start_time
        fps = frame_num / elapsed_time if elapsed_time > 0 else 0

        return {
            "session_id": session_id,
            "frames_processed": frame_num,
            "processing_time_seconds": elapsed_time,
            "avg_fps": fps,
            "unique_tracks": len(unique_track_ids),
            "gender_counts": gender_counts,
        }

    def _process_gender_classification(
        self,
        frame: np.ndarray,
        detections: List[Dict],
        frame_num: int,
        session_id: str,
        frame_width: int,
        frame_height: int,
        track_id_to_gender: Dict[int, str],
        track_id_to_gender_conf: Dict[int, float],
    ) -> None:
        """Process gender classification for detections."""
        # Poll previously enqueued tasks
        if self.gender_worker is None:
            return

        new_pending = []
        for task_id in self._pending_gender_tasks:
            res = self.gender_worker.try_get_result(task_id)
            if res is None:
                new_pending.append(task_id)
                continue
            gender_label, gconf, done_ts = res
            try:
                _, track_str, _ = task_id.split(":", 2)
                t_id_int = int(track_str)
                track_id_to_gender[t_id_int] = gender_label
                track_id_to_gender_conf[t_id_int] = float(gconf)
                if self.gender_metrics is not None:
                    self.gender_metrics.results_total += 1
                    self.gender_metrics.observe_gender(t_id_int, gender_label)
            except Exception:
                pass
        self._pending_gender_tasks = new_pending

        # Adaptive sampling
        eff_every_k = self.gender_every_k
        eff_max_per_frame = self.gender_max_per_frame
        qlen = 0
        if self.gender_worker is not None:
            try:
                qlen = self.gender_worker.get_queue_size()
            except Exception:
                qlen = len(self._pending_gender_tasks)
        else:
            qlen = len(self._pending_gender_tasks)

        if self.gender_adaptive_enabled:
            if qlen >= self.gender_queue_high_watermark:
                eff_every_k = max(self.gender_every_k, self.gender_every_k * 2)
                eff_max_per_frame = max(1, min(self.gender_max_per_frame, 2))
            elif qlen <= self.gender_queue_low_watermark:
                eff_every_k = self.gender_every_k
                eff_max_per_frame = self.gender_max_per_frame

        # Enqueue tasks every K frames
        if frame_num % eff_every_k == 0:
            enqueued_this_frame = 0
            for d in detections:
                if enqueued_this_frame >= eff_max_per_frame:
                    break
                if d.get("track_id") is None:
                    continue

                bbox = d.get("bbox")
                x1, y1, x2, y2 = self._parse_bbox_xyxy(bbox)
                if x1 is None or y1 is None or x2 is None or y2 is None:
                    continue
                xi1 = max(0, min(frame_width - 1, int(x1)))
                yi1 = max(0, min(frame_height - 1, int(y1)))
                xi2 = max(0, min(frame_width - 1, int(x2)))
                yi2 = max(0, min(frame_height - 1, int(y2)))
                if xi2 <= xi1 or yi2 <= yi1:
                    continue

                person_crop = frame[yi1:yi2, xi1:xi2].copy()
                crop, use_face_classifier = self._get_gender_crop(
                    person_crop, frame, frame_num, d, yi1, yi2, xi1, xi2
                )

                if crop is None or crop.size == 0:
                    continue

                t_id_int = int(d["track_id"])
                task_id = f"{session_id}:{t_id_int}:{frame_num}"

                def _make_func(
                    c=crop,
                    track_id_val=t_id_int,
                    use_face=use_face_classifier,
                    _gc=self.gender_classifier,
                    _fgc=self.face_gender_classifier,
                ):
                    def _run():
                        start_ms = time.time() * 1000.0
                        if use_face and _fgc is not None:
                            gender, gconf = _fgc.classify(c)
                        else:
                            if _gc is None:
                                return "Unknown", 0.0
                            gender, gconf = _gc.classify(c, track_id=track_id_val)
                        dur = (time.time() * 1000.0) - start_ms
                        if self.gender_metrics is not None:
                            self.gender_metrics.observe_latency(dur)
                        return gender, float(gconf)

                    return _run

                if self.gender_worker is None:
                    continue
                ok = self.gender_worker.enqueue(
                    task_id=task_id, priority=1, func=_make_func()
                )
                if ok:
                    self._pending_gender_tasks.append(task_id)
                    enqueued_this_frame += 1
                    if self.gender_metrics is not None:
                        self.gender_metrics.inc_call()
                else:
                    if self.gender_metrics is not None:
                        self.gender_metrics.inc_dropped()

    def _parse_bbox_xyxy(self, bbox_obj) -> Tuple[Optional[float], ...]:
        """Parse bbox to (x1, y1, x2, y2)."""
        x1 = y1 = x2 = y2 = None
        try:
            if isinstance(bbox_obj, (list, tuple)) and len(bbox_obj) == 4:
                x1, y1, x2, y2 = bbox_obj
            else:
                if isinstance(bbox_obj, np.ndarray) and bbox_obj.size >= 4:
                    x1, y1, x2, y2 = [float(b) for b in bbox_obj[:4].tolist()]
                elif isinstance(bbox_obj, str):
                    vals = bbox_obj.strip("[]").replace(",", " ").split()
                    if len(vals) >= 4:
                        x1, y1, x2, y2 = map(float, vals[:4])
        except Exception:
            pass
        return x1, y1, x2, y2

    def _get_gender_crop(
        self,
        person_crop: np.ndarray,
        frame: np.ndarray,
        frame_num: int,
        detection: Dict,
        yi1: int,
        yi2: int,
        xi1: int,
        xi2: int,
    ) -> Tuple[Optional[np.ndarray], bool]:
        """Get crop for gender classification (face or upper-body)."""
        crop = None
        use_face_classifier = False

        if self.gender_enable_face_detection and self.face_detector is not None:
            t_id_int_tmp = int(detection["track_id"])
            do_detect_face = frame_num % self.gender_face_every_k == 0

            if not do_detect_face:
                last_frame = self._face_bbox_cache_frame.get(t_id_int_tmp, -(10**9))
                if (
                    (frame_num - last_frame) <= self.gender_cache_ttl_frames
                    and t_id_int_tmp in self._face_bbox_cache
                ):
                    face_bbox_rel = self._face_bbox_cache[t_id_int_tmp]
                    crop = self.face_detector.crop_face(person_crop, face_bbox_rel)
                    use_face_classifier = (
                        True if crop is not None and crop.size > 0 else False
                    )

            if do_detect_face or (crop is None or crop.size == 0):
                face_result = self.face_detector.detect_face(person_crop)
                if face_result is not None:
                    face_bbox_rel, face_conf = face_result
                    self._face_bbox_cache[t_id_int_tmp] = face_bbox_rel
                    self._face_bbox_cache_frame[t_id_int_tmp] = frame_num
                    crop = self.face_detector.crop_face(person_crop, face_bbox_rel)
                    use_face_classifier = True

        if crop is None or crop.size == 0:
            h_box = float(yi2) - float(yi1)
            upper_yi2 = yi1 + int(h_box * 0.6)
            crop = frame[yi1:upper_yi2, xi1:xi2].copy()
            use_face_classifier = False

        return crop, use_face_classifier

    def _store_detections(
        self,
        detections: List[Dict],
        frame_num: int,
        track_id_to_gender: Dict[int, str],
        track_id_to_gender_conf: Dict[int, float],
    ) -> None:
        """Store detections in database buffer."""
        if self.db_manager is None:
            return

        now = datetime.now()
        for d in detections:
            bbox = d.get("bbox")
            x1, y1, x2, y2 = self._parse_bbox_xyxy(bbox)
            if x1 is None or y1 is None or x2 is None or y2 is None:
                continue

            track_id = d.get("track_id")
            gender = track_id_to_gender.get(int(track_id)) if track_id else None
            gender_conf = (
                track_id_to_gender_conf.get(int(track_id)) if track_id else None
            )

            detection_obj = PersonDetection(
                timestamp=now,
                camera_id=self.camera_id,
                channel_id=self.channel_id,
                detection_id=f"{self.camera_id}_{self.channel_id}_{frame_num}_{track_id}",
                track_id=track_id,
                confidence=float(d.get("confidence", 0.0)),
                bbox=(int(x1), int(y1), int(x2 - x1), int(y2 - y1)),
                gender=gender,
                gender_confidence=gender_conf,
                frame_number=frame_num,
            )
            self._db_buffer.append(detection_obj)

        # Flush if buffer full or interval reached
        current_ms = time.time() * 1000.0
        if (
            len(self._db_buffer) >= self.db_batch_size
            or (current_ms - self._last_db_flush_ms) >= self.db_flush_interval_ms
        ):
            if len(self._db_buffer) > 0:
                count = self.db_manager.insert_detections(self._db_buffer)
                logger.debug("DB flush inserted=%d", count)
                self._db_buffer.clear()
                self._last_db_flush_ms = current_ms

    def _finalize_db_storage(
        self,
        unique_track_ids: set,
        track_id_to_gender: Dict[int, str],
        track_id_to_gender_conf: Dict[int, float],
        session_id: str,
    ) -> None:
        """Finalize database storage with track genders and summary."""
        if self.db_manager is None:
            return

        # Final flush
        if len(self._db_buffer) > 0:
            count = self.db_manager.insert_detections(self._db_buffer)
            logger.info("Final DB flush inserted=%d", count)
            self._db_buffer.clear()

        # Store track genders
        male_count = 0
        female_count = 0
        unknown_count = 0

        for track_id in unique_track_ids:
            gender = track_id_to_gender.get(track_id, "Unknown")
            conf = track_id_to_gender_conf.get(track_id, 0.0)

            if gender == "M":
                male_count += 1
            elif gender == "F":
                female_count += 1
            else:
                unknown_count += 1

            try:
                self.db_manager.upsert_track_gender(
                    camera_id=self.camera_id,
                    track_id=track_id,
                    gender=gender,
                    confidence=conf,
                )
            except Exception as e:
                logger.warning("Failed to store track gender: %s", e)

        # Store run summary
        try:
            self.db_manager.insert_run_gender_summary(
                run_id=session_id,
                camera_id=self.camera_id,
                unique_total=len(unique_track_ids),
                male_tracks=male_count,
                female_tracks=female_count,
                unknown_tracks=unknown_count,
            )
            logger.info(
                "DB run summary persisted: unique=%d male=%d female=%d unknown=%d",
                len(unique_track_ids),
                male_count,
                female_count,
                unknown_count,
            )
        except Exception as e:
            logger.warning("Failed to store run summary: %s", e)

    def request_shutdown(self) -> None:
        """Request graceful shutdown."""
        self._shutdown_requested = True

    def release(self) -> None:
        """Release all resources."""
        if self.gender_worker is not None:
            self.gender_worker.shutdown()
        if self.db_manager is not None:
            self.db_manager.close()
        if self.detector is not None:
            self.detector.release()
        logger.info("Resources released")


def build_rtsp_url(
    server_host: str, server_port: int, channel_id: int, credentials: Dict[str, str]
) -> str:
    """
    Build RTSP URL from components.

    Args:
        server_host: Server hostname/IP
        server_port: Server port
        channel_id: Channel ID
        credentials: Dictionary with 'username' and 'password'

    Returns:
        Complete RTSP URL
    """
    username = credentials.get("username", "")
    password = credentials.get("password", "")
    auth = f"{username}:{password}@" if username and password else ""
    return f"rtsp://{auth}{server_host}:{server_port}/Streaming/Channels/{channel_id:02d}01"


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Process live RTSP camera streams with person detection"
    )
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to camera configuration JSON file",
    )
    parser.add_argument(
        "--channel-id",
        type=int,
        required=True,
        help="Channel ID to process (1-4)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="yolov8n.pt",
        help="Path to YOLOv8 model file",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output/live",
        help="Output directory for results",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Optional run identifier",
    )
    parser.add_argument(
        "--preset",
        type=str,
        default=None,
        choices=["gender_main_v1"],
        help="Optional named preset",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=None,
        help="Maximum frames to process (None = unlimited)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )
    parser.add_argument(
        "--display",
        action="store_true",
        help="Display video frames in a window (press 'q' to quit)",
    )
    parser.add_argument(
        "--display-fps",
        type=float,
        default=12.0,
        help="Display update rate (FPS) to reduce lag (default: 12.0)",
    )
    parser.add_argument(
        "--conf-threshold",
        type=float,
        default=0.75,
        help="Detection confidence threshold (default: 0.75, increase to reduce false positives)",
    )

    args = parser.parse_args()

    # Configure logging
    level = getattr(logging, args.log_level.upper(), logging.INFO)
    logging.getLogger().setLevel(level)

    try:
        # Load camera config
        config_path = Path(args.config)
        if not config_path.exists():
            logger.error("Camera config not found: %s", config_path)
            sys.exit(1)

        camera_config = load_camera_config(config_path)
        channel_config = camera_config.get_channel(args.channel_id)

        if channel_config is None:
            logger.error("Channel %d not found in config", args.channel_id)
            sys.exit(1)

        # Use RTSP URL from config if available, otherwise build it
        rtsp_url = channel_config.get("rtsp_url")
        if not rtsp_url:
            server_info = camera_config.get_server_info()
            credentials = camera_config.get_credentials()
            rtsp_url = build_rtsp_url(
                server_info["host"],
                server_info["port"],
                args.channel_id,
                credentials,
            )
            logger.warning("Using auto-built RTSP URL (not in config)")

        credentials = camera_config.get_credentials()
        logger.info(
            "RTSP URL: %s", rtsp_url.replace(credentials.get("password", ""), "***")
        )

        # Load database config if available
        db_config_path = Path("config/database.json")
        db_dsn = None
        redis_url = None
        if db_config_path.exists():
            import json

            with open(db_config_path) as f:
                db_config = json.load(f)
                db_dsn = db_config.get("postgresql", {}).get("dsn")
                redis_url = db_config.get("redis", {}).get("url")

        # Create processor (reuse VideoProcessor args pattern)
        processor_args = {
            "camera_id": 1,  # TODO: get from config
            "channel_id": args.channel_id,
            "rtsp_url": rtsp_url,
            "model_path": args.model,
            "output_dir": args.output,
            "run_id": args.run_id,
            "max_frames": args.max_frames,
            "display": args.display,
            "display_fps": getattr(args, "display_fps", 12.0),  # Lower default for smoother display
            "conf_threshold": getattr(args, "conf_threshold", 0.75),  # Increase to reduce false positives
        }

        # Apply preset if specified
        if args.preset == "gender_main_v1":
            preset_update = {
                "reid_enable": True,
                "reid_every_k": 20,
                "reid_ttl_seconds": 60,
                "reid_similarity_threshold": 0.65,
                "reid_aggregation_method": "avg_sim",
                "reid_append_mode": True,
                "reid_max_embeddings": 3,
                "gender_enable": True,
                "gender_every_k": 15,
                "gender_max_per_frame": 4,
                "gender_model_type": "timm_mobile",
                "gender_min_confidence": 0.50,
                "gender_female_min_confidence": 0.50,
                "gender_male_min_confidence": 0.50,
                "gender_voting_window": 35,
                "gender_adaptive_enabled": True,
                "gender_queue_high_watermark": 200,
                "gender_queue_low_watermark": 100,
                "db_enable": True,
                "db_dsn": db_dsn,
                "db_batch_size": 200,
                "db_flush_interval_ms": 500,
                "redis_enable": True,
                "redis_url": redis_url,
            }
            # Don't override conf_threshold if explicitly set
            if "conf_threshold" not in processor_args:
                preset_update["conf_threshold"] = 0.75  # Higher threshold for preset to reduce false positives
            processor_args.update(preset_update)

        processor = LiveCameraProcessor(**processor_args)

        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info("Received shutdown signal")
            processor.request_shutdown()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            # Process stream
            result = processor.process_stream()

            logger.info("Processing complete")
            logger.info("Frames: %d", result["frames_processed"])
            logger.info("Time: %.2fs", result["processing_time_seconds"])
            logger.info("FPS: %.2f", result["avg_fps"])
            logger.info("Tracks: %d", result["unique_tracks"])

        finally:
            processor.release()

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.exception("Error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
