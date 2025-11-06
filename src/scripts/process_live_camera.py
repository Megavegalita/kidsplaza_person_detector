#!/usr/bin/env python3
"""
Live Camera Processing Script.

This script processes live RTSP camera streams with person detection,
tracking, gender classification, and data storage integration.
"""

import argparse
import logging
import queue
import signal
import sys
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, cast

import cv2  # noqa: E402
import numpy as np
import torch  # noqa: E402

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.modules.camera.camera_config import load_camera_config  # noqa: E402
from src.modules.camera.camera_reader import CameraReader  # noqa: E402
from src.modules.camera.camera_reader import CameraReaderError
from src.modules.database.models import PersonDetection  # noqa: E402
from src.modules.database.postgres_manager import PostgresManager  # noqa: E402
from src.modules.database.redis_manager import RedisManager  # noqa: E402

# PyTorch-based gender/age classification (no TensorFlow/MediaPipe conflicts)
from src.modules.demographics.async_worker import AsyncGenderWorker  # noqa: E402
from src.modules.demographics.face_gender_classifier import (
    FaceGenderClassifier,
)  # noqa: E402
from src.modules.demographics.gender_opencv import GenderOpenCV  # noqa: E402
from src.modules.demographics.metrics import GenderMetrics  # noqa: E402
from src.modules.detection.detector import Detector  # noqa: E402
from src.modules.detection.face_detector_opencv import FaceDetectorOpenCV
from src.modules.detection.face_detector_retinaface import (  # noqa: E402
    RETINAFACE_AVAILABLE,
    FaceDetectorRetinaFace,
)
from src.modules.detection.image_processor import ImageProcessor  # noqa: E402
from src.modules.detection.staff_classifier import StaffClassifier  # noqa: E402
from src.modules.detection.staff_voting_cache import StaffVotingCache  # noqa: E402
from src.modules.reid.arcface_embedder import ArcFaceEmbedder  # noqa: E402
from src.modules.reid.cache import ReIDCache  # noqa: E402
from src.modules.reid.embedder import ReIDEmbedder  # noqa: E402
from src.modules.reid.integrator import integrate_reid_for_tracks  # noqa: E402
from src.modules.tracking.tracker import Tracker  # noqa: E402
from src.modules.counter.zone_counter import ZoneCounter  # noqa: E402
from src.modules.counter.daily_person_counter import DailyPersonCounter  # noqa: E402
from src.modules.counter.person_identity_manager import PersonIdentityManager  # noqa: E402

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
        tracker_max_age: int = 30,  # Reduced from 50 to 30 to remove stale tracks faster
        tracker_min_hits: int = 2,  # Reduced from 3 to 2 for faster track confirmation
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
        counter_zones: Optional[List[Dict[str, Any]]] = None,
        detect_every_n: Optional[int] = None,
        staff_detection_enable: bool = False,
        staff_detection_model_path: str = "models/kidsplaza/best.pt",
        staff_detection_conf_threshold: float = 0.5,
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

        # Initialize face-based detector (replaces YOLOv8 for person detection)
        # Priority: RetinaFace (best accuracy) > YuNet (fallback)
        # RetinaFace solves false positive issues (motorcycles) and improves accuracy

        # Different thresholds for outdoor vs indoor cameras
        # Channel 1, 2: Outdoor (ben_ngoai) - people further away, need lower threshold
        # Channel 3, 4: Indoor (ben_trong) - people closer, can use higher threshold
        is_outdoor = channel_id in [1, 2]

        if is_outdoor:
            # Outdoor cameras: lower confidence threshold to detect distant faces
            # Channel 1 has false positive issue with motorcycles
            if channel_id == 1:
                face_confidence_threshold = max(
                    0.45, conf_threshold * 0.9
                )  # 0.45 for Channel 1
                logger.info(
                    "Outdoor camera (channel %d): Threshold 0.45 (RetinaFace handles false positives well)",
                    channel_id,
                )
            else:
                face_confidence_threshold = max(
                    0.35, conf_threshold * 0.7
                )  # 0.35 for other outdoor cameras
                logger.info(
                    "Outdoor camera (channel %d): Lower confidence threshold for distant faces",
                    channel_id,
                )
            input_size = (
                640,
                480,
            )  # Higher resolution for better distant face detection
            detect_resize = (640, 480)
        else:
            # Indoor cameras: higher confidence threshold to reduce false positives
            face_confidence_threshold = max(
                0.4, conf_threshold * 0.8
            )  # 0.4 for indoor (lower than YuNet due to better accuracy)
            input_size = (480, 360)  # Standard resolution for close faces
            detect_resize = (480, 360)
            logger.info(
                "Indoor camera (channel %d): Threshold 0.4 (RetinaFace has better accuracy)",
                channel_id,
            )

        # Try RetinaFace first (best accuracy, low false positives)
        # Fallback to YuNet if RetinaFace not available
        if RETINAFACE_AVAILABLE:
            logger.info(
                "Using RetinaFace detector (high accuracy, low false positives)"
            )
            self.face_detector_full = FaceDetectorRetinaFace(
                min_detection_confidence=face_confidence_threshold,
                model_selection="mobile",  # Fast variant (~10ms), use "resnet50" for higher accuracy (~15ms)
                body_expand_ratio=3.0,
                body_expand_vertical=0.5,
                detect_resize=detect_resize,
            )
            logger.info(
                "RetinaFace confidence threshold: %.2f", face_confidence_threshold
            )
        else:
            logger.info(
                "RetinaFace not available - using YuNet (install with: pip install retinaface)"
            )
            self.face_detector_full = FaceDetectorOpenCV(
                min_detection_confidence=face_confidence_threshold,
                model_selection=1,  # Full range (2-5m) for CCTV cameras
                body_expand_ratio=3.0,  # Increased from 2.5 to 3.0 for more accurate full-body bbox
                body_expand_vertical=0.5,  # Increased from 0.4 to 0.5 for better vertical expansion
                input_size=input_size,
                detect_resize=detect_resize,
            )
            logger.info("YuNet confidence threshold: %.2f", face_confidence_threshold)

        # Switch back to body detection (YOLOv8) - more reliable than face detection
        self.use_face_detection = False  # Use YOLOv8 body detection instead
        self.face_detector_full = None  # Disable face detection

        # Initialize YOLOv8 detector for body/person detection
        try:
            self.detector = Detector(
                model_path=model_path, conf_threshold=conf_threshold
            )
            logger.info(
                "YOLOv8 body detector initialized: model=%s, conf=%.2f",
                model_path,
                conf_threshold,
            )
        except Exception as e:
            logger.error("Failed to initialize YOLOv8 detector: %s", e, exc_info=True)
            self.detector = None

        # Initialize image processor for drawing detections
        self.processor = ImageProcessor()

        logger.info("Using YOLOv8 body detection for person detection")
        logger.info("YOLOv8 detection confidence threshold: %.2f", conf_threshold)

        # Initialize staff classifier (optional)
        self.staff_detection_enable = bool(staff_detection_enable)
        self.staff_classifier: Optional[StaffClassifier] = None
        self.staff_voting_cache: Optional[StaffVotingCache] = None
        if self.staff_detection_enable:
            try:
                self.staff_classifier = StaffClassifier(
                    model_path=staff_detection_model_path,
                    conf_threshold=staff_detection_conf_threshold,
                )
                # Initialize voting cache with threshold 0.4 parameters
                self.staff_voting_cache = StaffVotingCache(
                    vote_window=10,
                    vote_threshold=4,
                    cache_keep_frames=30,
                )
                logger.info(
                    "Staff classifier initialized: model=%s, conf=%.2f, vote_window=10, vote_threshold=4",
                    staff_detection_model_path,
                    staff_detection_conf_threshold,
                )
            except Exception as e:
                logger.error("Failed to initialize staff classifier: %s", e)
                self.staff_classifier = None
                self.staff_voting_cache = None
                self.staff_detection_enable = False

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

        # Initialize Gender and Age components (PyTorch-based, no TensorFlow conflicts)
        self.gender_enable = bool(gender_enable)
        self.gender_every_k = gender_every_k
        self.gender_enable_face_detection = True  # Use face crops from OpenCV detection
        # Face detector for gender classification (not needed - using OpenCV face detection)
        self.face_detector_gender = None  # Not needed
        self.face_detector = (
            None  # Not needed - OpenCV DNN already provides face detection
        )

        # Initialize PyTorch-based classifiers
        if self.gender_enable:
            try:
                # FaceGenderClassifier uses PyTorch MobileNetV2 (no TensorFlow)
                self.face_gender_classifier = FaceGenderClassifier(
                    device="mps" if torch.backends.mps.is_available() else "cpu",
                    min_confidence=0.65,  # Increased threshold for better accuracy
                )
                logger.info("FaceGenderClassifier initialized (PyTorch-based)")
            except Exception as e:
                logger.error("Failed to initialize FaceGenderClassifier: %s", e)
                self.face_gender_classifier = None
                self.gender_enable = False

            # Initialize gender classifier (OpenCV DNN - pretrained models, recommended)
            self.gender_opencv = None
            try:
                # Try OpenCV DNN first (pretrained on Adience, more accurate ~85-90%)
                self.gender_opencv = GenderOpenCV(
                    device="opencl",  # Try OpenCL for GPU acceleration
                    min_confidence=0.65,  # Higher threshold for better accuracy
                )
                if self.gender_opencv.gender_net is not None:
                    logger.info(
                        "GenderOpenCV initialized (OpenCV DNN pretrained models)"
                    )
                    # Use OpenCV model for gender (more accurate than PyTorch fallback)
                    self.face_gender_classifier = (
                        None  # Disable PyTorch gender, use OpenCV instead
                    )
                else:
                    logger.warning(
                        "OpenCV DNN gender model not loaded, using PyTorch fallback"
                    )
                    self.gender_opencv = None
            except Exception as e:
                logger.warning("Failed to initialize GenderOpenCV: %s", e)
                self.gender_opencv = None

            # Initialize async worker for gender classification
            if (
                self.face_gender_classifier is not None
                or self.gender_opencv is not None
            ):
                self.gender_worker = AsyncGenderWorker(max_workers=2, queue_size=128)
                self.gender_metrics = GenderMetrics()
                if self.gender_opencv is not None:
                    logger.info(
                        "Gender classification enabled with OpenCV DNN (pretrained models)"
                    )
                else:
                    logger.info(
                        "Gender classification enabled with PyTorch (MobileNetV2)"
                    )
            else:
                self.gender_worker = None
                self.gender_metrics = None
                self.gender_enable = False
        else:
            self.face_gender_classifier = None
            self.gender_opencv = None
            self.gender_worker = None
            self.gender_metrics = None
            logger.info("Gender classification disabled by config")
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
        self.display_frame_skip = max(
            1, int(24.0 / self.display_fps)
        )  # Skip frames for display
        self._last_display_time = 0.0
        self._display_frame_count = 0
        # Resize for display to reduce lag (max width 1280)
        self.display_max_width = 1280

        # Counter initialization (PID disabled) — always use ZoneCounter
        # Zones will be loaded from camera config if counter is enabled
        self.person_identity_manager = None
        if counter_zones and len(counter_zones) > 0:
            try:
                self.counter = ZoneCounter(counter_zones)
                logger.info(
                    "ZoneCounter initialized with %d zones for channel %d",
                    len(counter_zones),
                    channel_id,
                )
            except Exception as e:
                logger.error("Failed to initialize ZoneCounter: %s", e, exc_info=True)
                self.counter = None
        else:
            self.counter = None

        # Face verification no longer needed - using face-based detection directly

        # Frame skipping for detection (detect every N frames to boost FPS)
        # Use config value if provided, otherwise channel-specific defaults
        if detect_every_n is not None:
            self.detect_every_n = detect_every_n
        elif channel_id == 4:
            self.detect_every_n = (
                2  # Detect every 2 frames for Channel 4 (better coverage)
            )
        else:
            self.detect_every_n = 4  # Detect every 4 frames for others (4x speed boost, tracker handles continuity well)
        self._last_detect_frame = -1
        self._cached_detections = []  # Cache detections for skipped frames

        # Multi-threading for parallel processing
        # OPTIMIZED: Increased workers for better parallelization
        import os

        num_cores = os.cpu_count() or 4
        # Use 2 workers for detection (can process multiple frames in parallel)
        detection_workers = min(2, max(1, num_cores // 2))

        self._frame_queue: queue.Queue[Optional[np.ndarray]] = queue.Queue(maxsize=2)
        self._detection_queue: queue.Queue[Tuple[int, List[Dict]]] = queue.Queue(
            maxsize=2
        )
        self._detection_executor = ThreadPoolExecutor(
            max_workers=detection_workers, thread_name_prefix="detection"
        )
        self._db_executor = (
            ThreadPoolExecutor(max_workers=1, thread_name_prefix="db-writer")
            if db_enable
            else None
        )
        logger.info("Detection executor initialized with %d workers", detection_workers)

        # Threading synchronization
        self._frame_reader_thread: Optional[threading.Thread] = None
        self._detection_future: Optional[Future] = None
        self._pending_frame_num = 0

        # Shutdown flag
        self._shutdown_requested = False
        self._shutdown_lock = threading.Lock()

        logger.info("Live camera processor initialized")
        # logger.info("Device: %s", self.detector.model_loader.get_device())  # Disabled - using face detection
        logger.info("Using OpenCV DNN face detection (no YOLOv8 device needed)")
        # logger.info("MPS enabled: %s", self.detector.model_loader.is_mps_enabled())  # Disabled

    def _frame_reader_worker(self, camera_reader: CameraReader) -> None:
        """Worker thread to continuously read frames from camera."""
        consecutive_failures = 0
        max_consecutive_failures = 10

        while not self._shutdown_requested:
            try:
                frame = camera_reader.read_frame()
                if frame is None:
                    consecutive_failures += 1
                    if consecutive_failures >= max_consecutive_failures:
                        logger.warning("Max read failures in worker thread")
                        break
                    time.sleep(0.01)  # Small delay before retry
                    continue

                consecutive_failures = 0

                # Put frame in queue (non-blocking, drop if full to prevent lag)
                try:
                    self._frame_queue.put_nowait(frame)
                except queue.Full:
                    # Drop oldest frame if queue is full (prevent memory buildup)
                    try:
                        self._frame_queue.get_nowait()
                        self._frame_queue.put_nowait(frame)
                    except queue.Empty:
                        pass

            except Exception as e:
                logger.error("Frame reader worker error: %s", e)
                break

        # Put None to signal end
        try:
            self._frame_queue.put_nowait(None)
        except queue.Full:
            pass

    def process_stream(self, session_id: Optional[str] = None) -> Dict:
        """
        Process live camera stream with parallel processing.

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

                        # Start frame reader thread if not already running
                        if (
                            self._frame_reader_thread is None
                            or not self._frame_reader_thread.is_alive()
                        ):
                            self._frame_reader_thread = threading.Thread(
                                target=self._frame_reader_worker,
                                args=(camera_reader,),
                                name="frame-reader",
                                daemon=True,
                            )
                            self._frame_reader_thread.start()
                            logger.info(
                                "Frame reader thread started for parallel processing"
                            )
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

                # Get frame from queue (read by worker thread) or read directly if no worker
                # Fallback to direct reading if worker thread not started yet
                if (
                    self._frame_reader_thread is None
                    or not self._frame_reader_thread.is_alive()
                ):
                    # Fallback: read directly
                    try:
                        frame = camera_reader.read_frame()
                        if frame is None:
                            consecutive_failures += 1
                            if consecutive_failures >= max_consecutive_failures:
                                logger.error(
                                    "Max read failures reached, reconnecting..."
                                )
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
                else:
                    # Get frame from worker thread queue
                    try:
                        frame = self._frame_queue.get(timeout=0.1)
                        if frame is None:  # Signal to stop
                            logger.info("Frame reader signaled end")
                            break
                    except queue.Empty:
                        # No frame available yet, check for previous detection result
                        continue

                frame_num += 1

                # Check frame limit
                if self.max_frames is not None and frame_num > self.max_frames:
                    logger.info("Reached max frames limit: %d", self.max_frames)
                    break

                # Process frame (same logic as VideoProcessor)
                frame_height, frame_width = frame.shape[:2]

                # PARALLEL PROCESSING: Submit detection task to worker thread
                # Main thread can continue with other tasks while detection runs
                detections = []
                should_detect = frame_num % self.detect_every_n == 0

                if (
                    should_detect
                    and not self.use_face_detection
                    and self.detector is not None
                ):
                    # OPTIMIZED: Check previous detection result first (non-blocking)
                    if self._detection_future is not None:
                        try:
                            (
                                prev_frame_num,
                                prev_detections,
                            ) = self._detection_future.result(timeout=0.0)
                            if prev_detections is not None:
                                detections = prev_detections
                                self._last_detect_frame = prev_frame_num
                                if len(detections) > 0:
                                    logger.debug(
                                        "Got detection result from previous frame %d: %d persons",
                                        prev_frame_num,
                                        len(detections),
                                    )
                        except Exception as e:
                            # Previous detection not ready - will use empty detections
                            # Tracker will maintain tracks from previous frames
                            detections = []
                            logger.debug("Previous detection not ready yet: %s", e)
                    else:
                        detections = []

                    # Submit new detection task (async, non-blocking)
                    # Pre-resize frame for faster detection (avoid double resize)
                    # Use larger size for better face detection accuracy
                    h_orig, w_orig = frame.shape[:2]
                    target_w, target_h = (
                        480,
                        360,
                    )  # Increased to 480x360 for better face detection
                    if w_orig > target_w or h_orig > target_h:
                        small_frame = cv2.resize(
                            frame, (target_w, target_h), interpolation=cv2.INTER_LINEAR
                        )
                        scale_w = w_orig / target_w
                        scale_h = h_orig / target_h
                    else:
                        small_frame = frame
                        scale_w = scale_h = 1.0

                    current_frame_num = frame_num
                    logger.debug(
                        "Submitting YOLOv8 detection task: frame=%d, resized=%dx%d, scale=(%.2f, %.2f)",
                        current_frame_num,
                        small_frame.shape[1],
                        small_frame.shape[0],
                        scale_w,
                        scale_h,
                    )
                    self._detection_future = self._detection_executor.submit(
                        self._detect_frame_async,
                        small_frame,
                        current_frame_num,
                        scale_w,
                        scale_h,
                    )
                else:
                    # On skipped frames, check if we have a pending detection result
                    if self._detection_future is not None:
                        try:
                            _, cached_detections = self._detection_future.result(
                                timeout=0.001
                            )
                            if cached_detections:
                                detections = cached_detections
                        except Exception:
                            pass
                    else:
                        detections = []

                # Create annotated frame if display enabled
                annotated = None
                if self.display and len(detections) > 0:
                    annotated = self.processor.draw_detections(frame, detections)

                # Face-based detection already filters out non-faces
                # No need for complex geometric filtering - faces are reliable indicators
                # Only basic validation needed
                filtered_detections = []
                for d in detections:
                    # Basic validation: ensure bbox is valid
                    bbox = d.get("bbox", [])
                    if len(bbox) < 4:
                        continue

                    if hasattr(bbox, "tolist"):
                        bbox = bbox.tolist()

                    x1, y1, x2, y2 = (
                        float(bbox[0]),
                        float(bbox[1]),
                        float(bbox[2]),
                        float(bbox[3]),
                    )
                    w = x2 - x1
                    h = y2 - y1

                    # Validate dimensions
                    if w <= 0 or h <= 0:
                        continue

                    # Basic size check: filter tiny detections
                    if h < 50 or w < 30:
                        continue

                    # Basic max size check
                    if h > frame_height * 0.9 or w > frame_width * 0.9:
                        continue

                    filtered_detections.append(d)

                detections = filtered_detections

                # Log stats periodically - ALWAYS log detection attempts
                if (
                    should_detect and frame_num % 10 == 0
                ):  # Log every 10 detection frames (every 40 frames total)
                    logger.info(
                        "YOLOv8 detection attempt: frame=%d, detected=%d persons, should_detect=%s",
                        frame_num,
                        len(detections),
                        should_detect,
                    )
                elif len(detections) > 0:  # Always log when we detect someone
                    logger.info(
                        "YOLOv8 body detection: %d persons detected at frame %d",
                        len(detections),
                        frame_num,
                    )

                # Run tracking - ALWAYS update tracker to get predicted tracks
                # IMPORTANT: Update tracker with ALL detections (before staff filtering)
                # This ensures tracker maintains continuity even when detections are sparse
                # Tracker can maintain and predict tracks even without new detections
                # This ensures bounding boxes display continuously
                tracked_detections = self.tracker.update(
                    detections, frame=frame, session_id=session_id
                )
                detections = tracked_detections
                
                # Update unique_track_ids from ALL tracked detections (before filtering)
                # This ensures stats reflect all tracks, not just customers
                for d in detections:
                    t_id = d.get("track_id")
                    if t_id is not None:
                        unique_track_ids.add(int(t_id))

                # Log tracker stats for debugging (including when no detections)
                if frame_num % 100 == 0:
                    track_ids = [d.get("track_id") for d in detections if d.get("track_id") is not None]
                    logger.info(
                        "Tracker update: %d detections, %d with track_id: %s (should_detect=%s)",
                        len(detections),
                        len(track_ids),
                        track_ids[:5] if track_ids else "none",
                        should_detect,
                    )

                # Staff classification with voting mechanism
                # IMPORTANT: Only run when we have person detections (should_detect=True)
                # This ensures we only classify when person is actually detected
                if (
                    self.staff_detection_enable
                    and self.staff_classifier is not None
                    and self.staff_voting_cache is not None
                    and len(detections) > 0
                    and should_detect  # Only classify when person is detected
                ):
                    # Debug: Log when staff classification block is entered
                    if frame_num % 50 == 0:
                        track_ids = [d.get("track_id") for d in detections if d.get("track_id") is not None]
                        logger.info(
                            "Staff classification block: %d detections, %d with track_id: %s",
                            len(detections),
                            len(track_ids),
                            track_ids[:5] if track_ids else "none",
                        )
                    try:
                        # Get active track IDs for cache cleanup
                        active_track_ids = {
                            int(det.get("track_id"))
                            for det in detections
                            if det.get("track_id") is not None
                        }

                        # Cleanup stale tracks periodically
                        if frame_num % 60 == 0:  # Every 60 frames
                            self.staff_voting_cache.cleanup(active_track_ids, frame_num)

                        # Process each detection
                        for det in detections:
                            track_id = det.get("track_id")
                            if track_id is None:
                                continue

                            track_id_int = int(track_id)

                            # Check if classification is fixed in cache
                            cached_classification = self.staff_voting_cache.get_classification(
                                track_id_int
                            )

                            if cached_classification is not None:
                                # Use cached classification
                                det["is_staff"] = cached_classification == "staff"
                                det["person_type"] = cached_classification
                                logger.debug(
                                    "Staff classification [track %d]: cached=%s",
                                    track_id_int,
                                    cached_classification,
                                )
                            else:
                                # Need to classify and vote
                                # Classify on detection frames OR when we have a valid bbox
                                # This ensures classification happens even on interpolation frames
                                bbox = det.get("bbox")
                                if bbox is not None:
                                    # Only classify on detection frames to avoid redundant processing
                                    # But check cache on all frames
                                    if should_detect:
                                        # Crop person region
                                        x1, y1, x2, y2 = map(int, bbox)
                                        # Create bbox array (np is imported at module level)
                                        bbox_array = np.array([x1, y1, x2, y2], dtype=np.int32)
                                        person_crop = self.processor.crop_person(frame, bbox_array)

                                        if person_crop is not None:
                                            try:
                                                # Classify as staff or customer
                                                person_type, staff_confidence = (
                                                    self.staff_classifier.classify(person_crop)
                                                )

                                                # Default to customer if classification fails
                                                if person_type not in ["staff", "customer"]:
                                                    person_type = "customer"
                                                    staff_confidence = 0.0

                                                # Vote with confidence weighting
                                                final_classification, is_fixed = (
                                                    self.staff_voting_cache.vote(
                                                        track_id=track_id_int,
                                                        classification=person_type,
                                                        confidence=staff_confidence,
                                                        frame_num=frame_num,
                                                    )
                                                )

                                                # Set is_staff flag
                                                if is_fixed and final_classification is not None:
                                                    det["is_staff"] = final_classification == "staff"
                                                    det["person_type"] = final_classification
                                                    logger.info(
                                                        "Staff classification [track %d]: FIXED=%s (votes: type=%s, conf=%.3f)",
                                                        track_id_int,
                                                        final_classification,
                                                        person_type,
                                                        staff_confidence,
                                                    )
                                                else:
                                                    # Still voting, use current classification temporarily
                                                    det["is_staff"] = person_type == "staff"
                                                    det["person_type"] = person_type
                                                    logger.info(
                                                        "Staff classification [track %d]: VOTING (type=%s, conf=%.3f)",
                                                        track_id_int,
                                                        person_type,
                                                        staff_confidence,
                                                    )
                                            except Exception as e:
                                                logger.warning(
                                                    "Staff classification failed for track %d: %s",
                                                    track_id_int,
                                                    e,
                                                )
                                                # Default to customer on error
                                                det["is_staff"] = False
                                                det["person_type"] = "customer"
                                    else:
                                        # Not a detection frame, use cached classification if available
                                        # If not fixed yet, default to customer (will be updated on next detection frame)
                                        if cached_classification is None:
                                            det["is_staff"] = False
                                            det["person_type"] = None  # Not classified yet
                                else:
                                    # No bbox, cannot classify
                                    if cached_classification is None:
                                        det["is_staff"] = False
                                        det["person_type"] = None

                    except Exception as e:
                        logger.warning("Staff classification error: %s", e)

                # Filter staff detections BEFORE Re-ID and Counter
                # Staff detections will be skipped from Re-ID and Counter processing
                customer_detections = []
                staff_detections = []
                
                if self.staff_detection_enable and self.staff_voting_cache is not None:
                    # Split detections based on is_staff flag
                    for det in detections:
                        if det.get("is_staff") is True:
                            staff_detections.append(det)
                        else:
                            customer_detections.append(det)
                else:
                    # Staff detection not enabled, treat all as customers
                    customer_detections = detections
                    staff_detections = []

                # Log filtering stats periodically
                if len(staff_detections) > 0 and frame_num % 100 == 0:
                    logger.info(
                        "Staff filtering: %d staff (filtered), %d customer (processing)",
                        len(staff_detections),
                        len(customer_detections),
                    )

                # Prepare detections for display with gender/age info
                # Merge customer and staff detections for display
                display_detections = []
                if self.display:
                    # Add gender info to customer detections only (staff don't need gender)
                    for d in customer_detections:
                        display_det = d.copy()
                        track_id = d.get("track_id")
                        if track_id is not None:
                            track_id_int = int(track_id)
                            # Add gender info if available (only display if confidence is high enough)
                            gender = track_id_to_gender.get(track_id_int)
                            gender_conf = track_id_to_gender_conf.get(track_id_int)
                            if (
                                gender is not None
                                and gender != "Unknown"
                                and gender_conf is not None
                                and gender_conf >= 0.65
                            ):
                                display_det["gender"] = gender
                                display_det["gender_confidence"] = gender_conf
                        display_detections.append(display_det)
                    
                    # Add staff detections (no gender info needed)
                    for d in staff_detections:
                        display_det = d.copy()
                        display_detections.append(display_det)

                # Defer annotation until after Re-ID and Counter so PID can be rendered
                annotated = None

                # Face verification no longer needed since we're using face-based detection
                # All detections already have faces (detected from faces directly)
                # This eliminates false positives like motorcycles naturally

                # Integrate Re-ID - ONLY for customer detections (skip staff)
                # This saves significant processing time since staff don't need Re-ID
                if (
                    len(customer_detections)
                    > 0  # CRITICAL: Only run Re-ID if we have customer detections
                    and should_detect  # Only on detection frames (skip on interpolation frames)
                    and self.reid_enable
                    and self.reid_embedder is not None
                    and self.reid_cache is not None
                ):
                    try:
                        integrate_reid_for_tracks(
                            frame,
                            customer_detections,  # Only process customers
                            cast(ReIDEmbedder, self.reid_embedder),
                            self.reid_cache,
                            session_id=session_id,
                            every_k_frames=self.reid_every_k,
                            frame_index=frame_num,
                            max_per_frame=3,  # Reduced from 5 for better performance
                            min_interval_frames=40,  # Increased from 30 to reduce frequency
                            max_embeddings=self.reid_max_embeddings,
                            append_mode=self.reid_append_mode,
                            aggregation_method=self.reid_aggregation_method,
                        )
                        
                        # Extract Re-ID embeddings from cache and add to detections
                        # for PersonIdentityManager to resolve person_id
                        if (
                            self.person_identity_manager is not None
                            and self.reid_embedder is not None
                        ):
                            # np is already imported at module level
                            from typing import cast as _cast
                            # Try to attach embedding/person_id from cache; if missing, compute on-demand (limited)
                            on_demand_budget = 10  # compute up to 10 embeddings per frame to ensure PID resolution
                            for det in customer_detections:  # Only process customers
                                track_id = det.get("track_id")
                                if track_id is None:
                                    continue
                                got_embedding = False
                                # Prefer cache if available
                                try:
                                    if self.reid_cache is not None:
                                        cached_item = self.reid_cache.get(session_id, int(track_id))
                                        if cached_item is not None and cached_item.embedding is not None:
                                            det["reid_embedding"] = cached_item.embedding
                                            det["channel_id"] = self.channel_id
                                            pid = self.person_identity_manager.get_or_assign_person_id(
                                                channel_id=self.channel_id,
                                                track_id=int(track_id),
                                                embedding=cached_item.embedding,
                                            )
                                            if pid:
                                                det["person_id"] = pid
                                            got_embedding = True
                                except Exception as e:
                                    logger.debug("Re-ID cache get failed for track %d: %s", track_id, e)

                                # On-demand embedding if cache missing and budget remains
                                if not got_embedding and on_demand_budget > 0:
                                    try:
                                        bbox = det.get("bbox")
                                        if bbox is None:
                                            continue
                                        x1, y1, x2, y2 = map(int, bbox)
                                        crop = self.processor.crop_person(frame, np.array([x1, y1, x2, y2], dtype=np.int32))
                                        if crop is None:
                                            continue
                                        emb = _cast(ReIDEmbedder, self.reid_embedder).embed(crop)
                                        det["reid_embedding"] = emb
                                        det["channel_id"] = self.channel_id
                                        pid = self.person_identity_manager.get_or_assign_person_id(
                                            channel_id=self.channel_id,
                                            track_id=int(track_id),
                                            embedding=emb,
                                        )
                                        if pid:
                                            det["person_id"] = pid
                                        on_demand_budget -= 1
                                    except Exception as e:
                                        logger.debug("On-demand Re-ID embedding failed for track %d: %s", track_id, e)
                    except Exception as e:
                        logger.warning("Re-ID integration error: %s", e)

                # Always try to attach person_id from cache every frame (independent of counter)
                # Only for customer detections
                if self.reid_enable and self.person_identity_manager is not None and self.reid_cache is not None:
                    for det in customer_detections:  # Only process customers
                        track_id = det.get("track_id")
                        if track_id is None:
                            continue
                        try:
                            cached_item = self.reid_cache.get(session_id, int(track_id))
                            if cached_item is not None and cached_item.embedding is not None:
                                # Resolve/assign person_id using cached embedding
                                pid_cached = self.person_identity_manager.get_or_assign_person_id(
                                    channel_id=self.channel_id,
                                    track_id=int(track_id),
                                    embedding=cached_item.embedding,
                                )
                                if pid_cached:
                                    det["person_id"] = pid_cached
                        except Exception as e:
                            logger.debug("Attach PID from cache failed for track %d: %s", track_id, e)

                # Note: unique_track_ids already updated from all detections above
                # This ensures stats include all tracks (staff + customer) for continuity tracking

                # Counter update (if enabled) — ONLY for customer detections
                counter_result = None
                if self.counter is not None and len(customer_detections) > 0:
                    try:
                        counter_result = self.counter.update(customer_detections, frame, frame_num=frame_num)
                        if counter_result.get("events"):
                            for event in counter_result["events"]:
                                logger.info(
                                    "Counter event: %s - Zone: %s (%s), Track: %d",
                                    event["type"],
                                    event["zone_id"],
                                    event["zone_name"],
                                    event["track_id"],
                                )
                                # DB write (non-blocking best-effort)
                                # Only log customer events (staff events are filtered out)
                                if self.db_manager is not None:
                                    try:
                                        self.db_manager.insert_counter_event(
                                            channel_id=self.channel_id,
                                            zone_id=str(event.get("zone_id")),
                                            zone_name=str(event.get("zone_name")),
                                            event_type=str(event.get("type")),
                                            track_id=int(event.get("track_id")) if event.get("track_id") is not None else None,
                                            person_id=event.get("person_id"),
                                            frame_number=int(frame_num),
                                            extra_json={"run_id": self.run_id or "", "session_id": session_id},
                                        )
                                    except Exception as e:
                                        logger.debug("Failed to insert counter_event: %s", e)
                    except Exception as e:
                        logger.warning("Counter update error: %s", e)

                # Merge customer and staff detections for display
                # Staff will be displayed with red boxes, customers with green boxes
                all_detections_for_display = display_detections if self.display else (customer_detections + staff_detections)

                # Now render overlay after Re-ID and Counter so PID shows up
                if self.display:
                    if annotated is None:
                        annotated = frame.copy()
                    if len(all_detections_for_display) > 0:
                        annotated = self.processor.draw_detections(annotated, all_detections_for_display)
                    if self.counter is not None:
                        annotated = self.counter.draw_zones(annotated)

                # Gender and Age classification (PyTorch-based, no TensorFlow)
                # Only for customer detections (staff don't need gender classification)
                if (
                    self.gender_enable
                    and (
                        self.face_gender_classifier is not None
                        or self.gender_opencv is not None
                    )
                    and self.gender_worker is not None
                ):
                    self._process_gender_classification(
                        frame,
                        customer_detections,  # Only process customers
                        frame_num,
                        session_id,
                        frame_width,
                        frame_height,
                        track_id_to_gender,
                        track_id_to_gender_conf,
                    )

                # Display frame if enabled - OPTIMIZED for minimum overhead
                if self.display:
                    current_time = time.time()
                    # Only update display at specified FPS to reduce lag
                    time_since_last_display = current_time - self._last_display_time
                    display_interval = 1.0 / self.display_fps

                    if (
                        time_since_last_display >= display_interval
                        or self._last_display_time == 0.0
                    ):
                        window_name = f"Live Stream - Channel {self.channel_id}"

                        # Use annotated frame if available, otherwise original frame
                        frame_to_display = annotated if annotated is not None else frame

                        # Resize frame for display to reduce lag (only if larger than max width)
                        h, w = frame_to_display.shape[:2]
                        if w > self.display_max_width:
                            scale = self.display_max_width / w
                            new_w = int(w * scale)
                            new_h = int(h * scale)
                            # Cache resized frame to avoid repeated resize on same size
                            display_frame = cv2.resize(
                                frame_to_display,
                                (new_w, new_h),
                                interpolation=cv2.INTER_LINEAR,
                            )
                        else:
                            display_frame = frame_to_display  # No resize needed

                        cv2.imshow(window_name, display_frame)
                        self._last_display_time = current_time
                        self._display_frame_count += 1

                    # Always check for 'q' key (non-blocking, minimal overhead)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q"):
                        logger.info("User pressed 'q', stopping processing.")
                        break

                # Database storage (async write to avoid blocking)
                # Only store customer detections (staff are filtered out)
                if should_detect and self.db_enable and self.db_manager is not None:
                    if self._db_executor is not None:
                        # Submit async write (non-blocking)
                        self._db_executor.submit(
                            self._store_detections_async,
                            customer_detections.copy(),  # Only store customers
                            frame_num,
                            track_id_to_gender.copy(),
                            track_id_to_gender_conf.copy(),
                        )
                    else:
                        # Fallback to sync write
                        self._store_detections(
                            customer_detections,  # Only store customers
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
        """Process gender classification for detections using face crops from OpenCV."""
        # Poll previously enqueued tasks
        if self.gender_worker is None:
            return

        # Implement voting mechanism: collect multiple predictions per track for stability
        # Use a window of recent predictions to determine stable gender
        new_pending = []
        track_predictions_temp: Dict[
            int, List[Tuple[str, float]]
        ] = {}  # track_id -> [(gender, gconf), ...]

        for task_id in self._pending_gender_tasks:
            res = self.gender_worker.try_get_result(task_id)
            if res is None:
                new_pending.append(task_id)
                continue
            # Format: (gender, conf, done_ts) or (gender, conf)
            if len(res) >= 3:
                gender_label, gconf, done_ts = res[:3]
            elif len(res) >= 2:
                gender_label, gconf = res[:2]
            else:
                continue
            try:
                _, track_str, _ = task_id.split(":", 2)
                t_id_int = int(track_str)

                # Collect predictions for voting
                if t_id_int not in track_predictions_temp:
                    track_predictions_temp[t_id_int] = []
                track_predictions_temp[t_id_int].append((gender_label, float(gconf)))

            except Exception as e:
                logger.warning(
                    "Failed to parse task_id for voting: %s", e, exc_info=True
                )

        # Apply voting: use majority vote with confidence weighting for gender
        for t_id_int, predictions in track_predictions_temp.items():
            if len(predictions) == 0:
                continue

            # Filter out "Unknown" for voting (only count if all are Unknown)
            valid_predictions = [p for p in predictions if p[0] != "Unknown"]
            if len(valid_predictions) == 0:
                # All predictions are Unknown - use highest confidence
                best = max(predictions, key=lambda x: x[1])
                gender_label, gconf = best
            else:
                # Gender: Majority vote with confidence weighting
                gender_votes: Dict[str, List[float]] = {"M": [], "F": []}

                for pred_gender, pred_gconf in valid_predictions:
                    if pred_gender in ("M", "F"):
                        gender_votes[pred_gender].append(pred_gconf)

                # Gender: Weighted by confidence, majority wins
                m_total = sum(gender_votes.get("M", []))
                f_total = sum(gender_votes.get("F", []))
                if m_total > f_total:
                    gender_label = "M"
                    gconf = (
                        m_total / len(valid_predictions)
                        if len(valid_predictions) > 0
                        else 0.0
                    )
                elif f_total > m_total:
                    gender_label = "F"
                    gconf = (
                        f_total / len(valid_predictions)
                        if len(valid_predictions) > 0
                        else 0.0
                    )
                else:
                    # Tie - use highest confidence prediction
                    best = max(valid_predictions, key=lambda x: x[1])
                    gender_label, gconf = best[0], best[1]

            # Store final voted results
            track_id_to_gender[t_id_int] = gender_label
            track_id_to_gender_conf[t_id_int] = float(gconf)

            logger.info(
                "Gender result stored (voted from %d predictions): track_id=%d, gender=%s(%.2f)",
                len(predictions),
                t_id_int,
                gender_label,
                float(gconf),
            )

            if self.gender_metrics is not None:
                self.gender_metrics.results_total += 1
                self.gender_metrics.observe_gender(t_id_int, gender_label)

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
                    logger.debug(
                        "Gender/Age: Skipping track_id=%s - crop is None or empty",
                        d.get("track_id"),
                    )
                    continue

                t_id_int = int(d["track_id"])
                task_id = f"{session_id}:{t_id_int}:{frame_num}"

                # Debug logging
                logger.debug(
                    "Gender/Age: Enqueuing task for track_id=%d, frame=%d, crop_size=%s, use_face=%s",
                    t_id_int,
                    frame_num,
                    crop.shape if crop is not None else "None",
                    use_face_classifier,
                )

                def _make_func(
                    c=crop,
                    track_id_val=t_id_int,
                    use_face=use_face_classifier,
                    _fgc=self.face_gender_classifier,
                    _goc=self.gender_opencv,
                ):
                    def _run():
                        start_ms = time.time() * 1000.0

                        # Use OpenCV DNN model if available (pretrained, more accurate ~85-90%)
                        if _goc is not None:
                            try:
                                gender, gconf = _goc.classify(c)
                                logger.info(
                                    "Gender (OpenCV DNN): track_id=%d, gender=%s(%.2f)",
                                    track_id_val,
                                    gender,
                                    gconf,
                                )
                                dur = (time.time() * 1000.0) - start_ms
                                if self.gender_metrics is not None:
                                    self.gender_metrics.observe_latency(dur)
                                return gender, float(gconf)
                            except Exception as e:
                                logger.warning(
                                    "OpenCV gender classification error: %s",
                                    e,
                                    exc_info=True,
                                )

                        # Fallback to PyTorch models
                        if _fgc is not None:
                            gender, gconf = _fgc.classify(c)
                            logger.info(
                                "Gender (PyTorch MobileNetV2): track_id=%d, gender=%s(%.2f)",
                                track_id_val,
                                gender,
                                gconf,
                            )
                            dur = (time.time() * 1000.0) - start_ms
                            if self.gender_metrics is not None:
                                self.gender_metrics.observe_latency(dur)
                            return gender, float(gconf)
                        else:
                            logger.warning(
                                "Gender classifier not available for track_id=%d",
                                track_id_val,
                            )
                            return "Unknown", 0.0

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
        """Get crop for gender/age classification using face_bbox from OpenCV detection."""
        crop = None
        use_face_classifier = False

        # Try to get face_bbox from OpenCV detection (if available)
        face_bbox = detection.get("face_bbox")
        if face_bbox is not None and len(face_bbox) >= 4:
            # face_bbox is [face_x1, face_y1, face_x2, face_y2] in original frame coordinates
            try:
                face_x1, face_y1, face_x2, face_y2 = map(float, face_bbox[:4])
                # Add padding (30% on each side) for better context - improved accuracy
                face_w = face_x2 - face_x1
                face_h = face_y2 - face_y1
                padding_w = int(face_w * 0.3)
                padding_h = int(face_h * 0.3)

                # Expand bbox with padding
                face_x1 = max(0, face_x1 - padding_w)
                face_y1 = max(0, face_y1 - padding_h)
                face_x2 = min(frame.shape[1], face_x2 + padding_w)
                face_y2 = min(frame.shape[0], face_y2 + padding_h)

                # Convert to int after padding
                face_x1, face_y1, face_x2, face_y2 = map(
                    int, [face_x1, face_y1, face_x2, face_y2]
                )

                if face_x2 > face_x1 and face_y2 > face_y1:
                    # Validate minimum size (at least 64x64 for better classification accuracy)
                    if (face_x2 - face_x1) >= 64 and (face_y2 - face_y1) >= 64:
                        crop = frame[face_y1:face_y2, face_x1:face_x2].copy()
                        use_face_classifier = True
                        logger.debug(
                            "Extracted face crop: %dx%d from bbox [%.1f,%.1f,%.1f,%.1f]",
                            face_x2 - face_x1,
                            face_y2 - face_y1,
                            face_x1,
                            face_y1,
                            face_x2,
                            face_y2,
                        )
                    else:
                        logger.debug(
                            "Face crop too small: %dx%d, using upper-body fallback",
                            face_x2 - face_x1,
                            face_y2 - face_y1,
                        )
            except (ValueError, IndexError) as e:
                logger.debug("Failed to extract face from detection.face_bbox: %s", e)

        # Fallback: use upper-body crop if face extraction failed
        if crop is None or crop.size == 0:
            h_box = float(yi2) - float(yi1)
            upper_yi2 = yi1 + int(h_box * 0.6)
            crop = frame[yi1:upper_yi2, xi1:xi2].copy()
            use_face_classifier = False
            logger.debug("Using upper-body crop as fallback")

        return crop, use_face_classifier

    def _store_detections(
        self,
        detections: List[Dict],
        frame_num: int,
        track_id_to_gender: Dict[int, str],
        track_id_to_gender_conf: Dict[int, float],
    ) -> None:
        """Store detections in database buffer (only customers, skip staff)."""
        if self.db_manager is None:
            return

        # Filter out staff detections - only store customers
        customer_detections = [
            d for d in detections if d.get("is_staff") is not True
        ]

        if len(customer_detections) == 0:
            return

        now = datetime.now()
        for d in customer_detections:
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

    def _detect_frame_async(
        self,
        frame: np.ndarray,
        frame_num: int,
        scale_w: float = 1.0,
        scale_h: float = 1.0,
    ) -> Tuple[int, List[Dict]]:
        """Run face detection asynchronously in worker thread.

        Args:
            frame: Frame (may be pre-resized for performance)
            frame_num: Frame number
            scale_w: Scale factor for width (to scale bboxes back)
            scale_h: Scale factor for height (to scale bboxes back)
        """
        try:
            if not self.use_face_detection and self.detector is not None:
                # Use YOLOv8 body detection (more reliable than face detection)
                try:
                    # Run YOLOv8 detection on resized frame
                    # Returns: (List[Dict], Optional[np.ndarray])
                    detections, _ = self.detector.detect(frame, return_image=False)

                    # Detections are already in dict format:
                    # [{"bbox": [x1, y1, x2, y2], "confidence": float, "class_id": int, "class_name": str}, ...]
                    # Filter by confidence (already filtered by detector's conf_threshold, but double-check)
                    detections = [
                        det
                        for det in detections
                        if det.get("confidence", 0.0) >= self.conf_threshold
                        and det.get("class_id", -1) == 0  # Person class
                    ]

                    # Scale bboxes back to original frame size
                    if scale_w != 1.0 or scale_h != 1.0:
                        for det in detections:
                            bbox = det.get("bbox", [])
                            if len(bbox) >= 4:
                                det["bbox"] = [
                                    bbox[0] * scale_w,
                                    bbox[1] * scale_h,
                                    bbox[2] * scale_w,
                                    bbox[3] * scale_h,
                                ]

                    # Log detection result (debugging)
                    if len(detections) > 0:
                        logger.debug(
                            "Async YOLOv8 detection [frame %d]: Found %d persons",
                            frame_num,
                            len(detections),
                        )
                    else:
                        logger.debug(
                            "Async YOLOv8 detection [frame %d]: No persons detected",
                            frame_num,
                        )

                    return frame_num, detections
                except Exception as e:
                    logger.error("YOLOv8 detection error: %s", e, exc_info=True)
                    return frame_num, []
            else:
                logger.warning(
                    "YOLOv8 detector not initialized or face detection enabled"
                )
                return frame_num, []
        except Exception as e:
            logger.error("Async detection error: %s", e, exc_info=True)
        return frame_num, []

    def _store_detections_async(
        self,
        detections: List[Dict],
        frame_num: int,
        track_id_to_gender: Dict[int, str],
        track_id_to_gender_conf: Dict[int, float],
    ) -> None:
        """Store detections asynchronously in worker thread."""
        try:
            self._store_detections(
                detections,
                frame_num,
                track_id_to_gender,
                track_id_to_gender_conf,
            )
        except Exception as e:
            logger.error("Async DB write error: %s", e)

    def release(self) -> None:
        """Release all resources."""
        # Signal shutdown
        with self._shutdown_lock:
            self._shutdown_requested = True

        # Shutdown executors
        if self._detection_executor is not None:
            self._detection_executor.shutdown(wait=True)
        if self._db_executor is not None:
            self._db_executor.shutdown(wait=True)

        # Wait for frame reader thread
        if (
            self._frame_reader_thread is not None
            and self._frame_reader_thread.is_alive()
        ):
            self._frame_reader_thread.join(timeout=2.0)

        if self.gender_worker is not None:
            self.gender_worker.shutdown()
        if self.db_manager is not None:
            self.db_manager.close()
        if self.face_detector_full is not None:
            self.face_detector_full.release()
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
    import fcntl
    import os

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
    parser.add_argument(
        "--gender-enable",
        action="store_true",
        default=False,
        help="Enable gender and age classification (PyTorch-based, no MediaPipe/TensorFlow)",
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

        # Lock file to prevent multiple instances of same channel
        # Each channel has its own lock file (moved here so we have channel_id)
        import fcntl
        import os

        lock_file = Path(f"/tmp/kidsplaza_live_camera_ch{args.channel_id}.lock")
        try:
            # Try to acquire exclusive lock (non-blocking)
            lock_fd = os.open(str(lock_file), os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            # Keep lock file descriptor open
            import atexit

            def release_lock():
                try:
                    fcntl.flock(lock_fd, fcntl.LOCK_UN)
                    os.close(lock_fd)
                    lock_file.unlink(missing_ok=True)
                except Exception:
                    pass

            atexit.register(release_lock)
            signal.signal(signal.SIGINT, lambda s, f: (release_lock(), sys.exit(0)))
            signal.signal(signal.SIGTERM, lambda s, f: (release_lock(), sys.exit(0)))
        except (IOError, OSError):
            logger.error(
                "Another instance of channel %d is already running! Exiting.",
                args.channel_id,
            )
            sys.exit(1)

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

        # If DB DSN available, enable DB writes by default
        if db_dsn:
            processor_args["db_enable"] = True
            processor_args["db_dsn"] = db_dsn

        # Create processor (reuse VideoProcessor args pattern)
        # Initialize with defaults - will be overridden by config
        processor_args = {
            "camera_id": 1,  # TODO: get from config
            "channel_id": args.channel_id,
            "rtsp_url": rtsp_url,
            "model_path": args.model,
            "output_dir": args.output,
            "run_id": args.run_id,
            "max_frames": args.max_frames,
            "display": args.display,
            "display_fps": getattr(args, "display_fps", 12.0),
            "conf_threshold": getattr(args, "conf_threshold", 0.5),
            # Tracker defaults (will be overridden by config)
            "tracker_max_age": 30,
            "tracker_min_hits": 2,
            "tracker_iou_threshold": 0.3,
            "tracker_ema_alpha": 0.5,
        }

        # Apply preset if specified
        if args.preset == "gender_main_v1":
            preset_update = {
                "reid_enable": True,
                "reid_every_k": 20,
                "reid_ttl_seconds": 86400,  # 24 hours = 24 * 60 * 60 seconds (for daily person counting)
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
                preset_update[
                    "conf_threshold"
                ] = 0.75  # Higher threshold for preset to reduce false positives
            processor_args.update(preset_update)

        # Override gender_enable if explicitly set via command line
        if hasattr(args, "gender_enable") and args.gender_enable:
            processor_args["gender_enable"] = True

        # Load feature config from camera config
        try:
            channel_features = camera_config.get_channel_features(args.channel_id)
            
            # Load body detection config
            body_config = channel_features.get("body_detection", {})
            if "conf_threshold" not in processor_args or processor_args.get("conf_threshold") == 0.5:
                # Only override if using default
                processor_args["conf_threshold"] = body_config.get("conf_threshold", 0.5)
            
            # Load detect_every_n from config (per-channel override)
            if "detect_every_n" in body_config:
                processor_args["detect_every_n"] = body_config.get("detect_every_n")
            
            # Load tracking config
            tracking_config = channel_features.get("tracking", {})
            if tracking_config.get("enabled", True):
                processor_args["tracker_max_age"] = tracking_config.get("max_age", 30)
                processor_args["tracker_min_hits"] = tracking_config.get("min_hits", 2)
                processor_args["tracker_iou_threshold"] = tracking_config.get("iou_threshold", 0.3)
                processor_args["tracker_ema_alpha"] = tracking_config.get("ema_alpha", 0.5)
            
            # Load Re-ID config if not in preset
            if args.preset != "gender_main_v1":
                reid_config = channel_features.get("reid", {})
                if reid_config.get("enabled", False):
                    processor_args["reid_enable"] = True
                    processor_args["reid_every_k"] = reid_config.get("every_k_frames", 20)
                    processor_args["reid_ttl_seconds"] = reid_config.get("ttl_seconds", 60)
                    processor_args["reid_similarity_threshold"] = reid_config.get("similarity_threshold", 0.65)
                    processor_args["reid_aggregation_method"] = reid_config.get("aggregation_method", "single")
                    processor_args["reid_append_mode"] = reid_config.get("append_mode", False)
                    processor_args["reid_max_embeddings"] = reid_config.get("max_embeddings", 1)
                    # Prefer ArcFace face-based embeddings (GPU-capable)
                    processor_args["reid_use_face"] = True
            
            # Load gender classification config if not explicitly set
            if not hasattr(args, "gender_enable") or not args.gender_enable:
                gender_config = channel_features.get("gender_classification", {})
                if gender_config.get("enabled", False):
                    processor_args["gender_enable"] = True
                    processor_args["gender_every_k"] = gender_config.get("every_k_frames", 20)
                    processor_args["gender_model_type"] = gender_config.get("model_type", "timm_mobile")
                    processor_args["gender_min_confidence"] = gender_config.get("min_confidence", 0.5)
                    processor_args["gender_female_min_confidence"] = gender_config.get("female_min_confidence")
                    processor_args["gender_male_min_confidence"] = gender_config.get("male_min_confidence")
                    processor_args["gender_voting_window"] = gender_config.get("voting_window", 10)
                    processor_args["gender_max_per_frame"] = gender_config.get("max_per_frame", 4)
                    processor_args["gender_adaptive_enabled"] = gender_config.get("adaptive_enabled", False)
            
            # Load staff detection config
            staff_config = channel_features.get("staff_detection", {})
            if staff_config.get("enabled", False):
                processor_args["staff_detection_enable"] = True
                processor_args["staff_detection_model_path"] = staff_config.get("model_path", "models/kidsplaza/best.pt")
                processor_args["staff_detection_conf_threshold"] = staff_config.get("conf_threshold", 0.5)
                logger.info(
                    "Staff detection enabled for channel %d: model=%s, conf=%.2f",
                    args.channel_id,
                    processor_args["staff_detection_model_path"],
                    processor_args["staff_detection_conf_threshold"],
                )
            
            # Load counter config
            counter_config = channel_features.get("counter", {})
            if counter_config.get("enabled", False):
                counter_zones = counter_config.get("zones", [])
                if counter_zones and len(counter_zones) > 0:
                    processor_args["counter_zones"] = counter_zones
                    logger.info(
                        "Counter enabled for channel %d with %d zones",
                        args.channel_id,
                        len(counter_zones),
                    )
                else:
                    logger.warning(
                        "Counter enabled for channel %d but no zones configured",
                        args.channel_id,
                    )
        except Exception as e:
            logger.warning(
                "Failed to load feature config from camera config: %s", e
            )

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
