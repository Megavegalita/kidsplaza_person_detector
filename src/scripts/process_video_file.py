#!/usr/bin/env python3
"""
Process video file with person detection pipeline.

Tests offline video files before live camera integration.
Optimized for Apple M4 Pro with MPS acceleration.
"""

import logging
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Optional
import cv2
import json
import time
import numpy as np
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.detection.detector import Detector
from modules.tracking.tracker import Tracker
from modules.reid import (
    ReIDEmbedder,
    ReIDCache,
    integrate_reid_for_tracks,
)
from modules.demographics import GenderClassifier
from modules.demographics.async_worker import AsyncGenderWorker
from modules.demographics.metrics import GenderMetrics
from modules.demographics.face_detector import FaceDetector
from modules.demographics.resnet50_gender_classifier import ResNet50GenderClassifier
from modules.demographics.keras_tf_gender_classifier import KerasTFGenderClassifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VideoProcessor:
    """Process video files with detection pipeline."""
    
    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        output_dir: str = "output/videos",
        conf_threshold: float = 0.5,
        tracker_max_age: int = 30,
        tracker_min_hits: int = 3,
        tracker_iou_threshold: float = 0.3,
        tracker_ema_alpha: float = 0.5,
        reid_enable: bool = False,
        reid_every_k: int = 10,
        reid_ttl_seconds: int = 60,
        gender_enable: bool = False,
        gender_every_k: int = 20,
        gender_model_type: str = 'timm_mobile',
        gender_max_per_frame: int = 4,
        gender_timeout_ms: int = 50,
        gender_queue_size: int = 256,
        gender_workers: int = 2,
        gender_min_confidence: float = 0.5,
        gender_voting_window: int = 10,
        gender_enable_face_detection: bool = False,
    ) -> None:
        """
        Initialize video processor.
        
        Args:
            model_path: Path to YOLOv8 model
            output_dir: Output directory for results
            conf_threshold: Detection confidence threshold
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.conf_threshold = conf_threshold
        
        # Initialize detector
        self.detector = Detector(
            model_path=model_path,
            conf_threshold=conf_threshold
        )
        
        # Initialize tracker
        self.tracker = Tracker(
            max_age=tracker_max_age,
            min_hits=tracker_min_hits,
            iou_threshold=tracker_iou_threshold,
            ema_alpha=tracker_ema_alpha
        )
        
        # Initialize Re-ID components (optional)
        self.reid_enable = reid_enable
        self.reid_every_k = reid_every_k
        self.reid_cache = ReIDCache(ttl_seconds=reid_ttl_seconds) if reid_enable else None
        self.reid_embedder = ReIDEmbedder() if reid_enable else None

        # Initialize Gender components (optional)
        self.gender_enable = gender_enable
        self.gender_every_k = gender_every_k
        self.gender_enable_face_detection = gender_enable_face_detection
        self.gender_classifier = (
            GenderClassifier(model_type=gender_model_type, min_confidence=gender_min_confidence, voting_window=gender_voting_window) if gender_enable else None
        )
        self.face_detector = (
            FaceDetector(min_detection_confidence=0.5) if (gender_enable and gender_enable_face_detection) else None
        )
        # Use your trained Keras model for best accuracy
        self.face_gender_classifier = (
            KerasTFGenderClassifier(min_confidence=gender_min_confidence) if (gender_enable and gender_enable_face_detection) else None
        )
        self.gender_worker = (
            AsyncGenderWorker(max_workers=gender_workers, queue_size=gender_queue_size, task_timeout_ms=gender_timeout_ms)
            if gender_enable
            else None
        )
        self.gender_metrics = GenderMetrics() if gender_enable else None
        self.gender_max_per_frame = gender_max_per_frame
        self._pending_gender_tasks = []  # list of task_ids for polling results
        
        logger.info(f"Video processor initialized")
        logger.info(f"Device: {self.detector.model_loader.get_device()}")
        logger.info(f"MPS enabled: {self.detector.model_loader.is_mps_enabled()}")
    
    def _add_overlay(
        self,
        frame: np.ndarray,
        frame_num: int,
        detection_count: int,
        tracked_count: int,
        unique_count: int,
        gender_counts: Optional[Dict[str, int]],
        elapsed_time: float,
        device: str,
        mps_enabled: bool
    ) -> np.ndarray:
        """
        Add information overlay to frame.
        
        Args:
            frame: Input frame
            frame_num: Current frame number
            detection_count: Number of detections
            elapsed_time: Elapsed time in seconds
            device: Device used (mps/cpu)
            mps_enabled: Whether MPS is enabled
            
        Returns:
            Frame with overlay
        """
        overlay = frame.copy()
        
        # Calculate FPS
        fps = frame_num / elapsed_time if elapsed_time > 0 else 0
        
        # Info box background (top-left)
        h, w = frame.shape[:2]
        box_height = 210
        box_width = 300
        overlay = cv2.rectangle(overlay, (0, 0), (box_width, box_height), 
                                (0, 0, 0), -1)
        
        # Add semi-transparent background
        alpha = 0.5
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        
        # Draw info text
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        font_thickness = 1
        text_color = (0, 255, 0)
        y_offset = 20
        
        cv2.putText(frame, f"Frame: {frame_num}", (10, y_offset), 
                   font, font_scale, text_color, font_thickness)
        y_offset += 25
        
        cv2.putText(frame, f"Detections: {detection_count}", (10, y_offset), 
                   font, font_scale, text_color, font_thickness)
        y_offset += 25
        
        cv2.putText(frame, f"Tracks: {tracked_count}", (10, y_offset), 
                   font, font_scale, text_color, font_thickness)
        y_offset += 25
        
        cv2.putText(frame, f"Unique: {unique_count}", (10, y_offset), 
                   font, font_scale, text_color, font_thickness)
        y_offset += 25

        if gender_counts is not None:
            m_cnt = gender_counts.get('M', 0)
            f_cnt = gender_counts.get('F', 0)
            u_cnt = gender_counts.get('Unknown', 0)
            cv2.putText(frame, f"Gender M/F/U: {m_cnt}/{f_cnt}/{u_cnt}", (10, y_offset),
                       font, font_scale, text_color, font_thickness)
            y_offset += 25
        
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, y_offset), 
                   font, font_scale, text_color, font_thickness)
        y_offset += 25
        
        device_str = f"Device: {device.upper()}"
        if mps_enabled and device == 'mps':
            device_str += " (GPU)"
        cv2.putText(frame, device_str, (10, y_offset), 
                   font, font_scale, text_color, font_thickness)
        y_offset += 25
        
        elapsed_str = f"Time: {elapsed_time:.1f}s"
        cv2.putText(frame, elapsed_str, (10, y_offset), 
                   font, font_scale, text_color, font_thickness)
        
        return frame
    
    def process_video(
        self,
        video_path: Path,
        output_name: Optional[str] = None,
        save_annotated: bool = True
    ) -> Dict:
        """
        Process video file through detection pipeline.
        
        Args:
            video_path: Path to input video
            output_name: Output video name (optional)
            save_annotated: Whether to save annotated video
            
        Returns:
            Dictionary with processing results
        """
        logger.info(f"Processing video: {video_path}")
        
        # Open video
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {video_path}")
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        logger.info(f"Video properties: {width}x{height} @ {fps} FPS, {total_frames} frames")
        
        # Setup output video if needed
        video_writer = None
        if save_annotated:
            output_name = output_name or f"annotated_{video_path.stem}.mp4"
            output_path = self.output_dir / output_name
            
            # Use H.264 codec for better compatibility
            # Try 'avc1' first (H.264), fallback to 'mp4v' if not available
            fourcc = cv2.VideoWriter_fourcc(*'avc1')
            logger.info(f"Using codec: H.264 (avc1)")
            
            video_writer = cv2.VideoWriter(
                str(output_path),
                fourcc,
                fps,
                (width, height)
            )
            
            if not video_writer.isOpened():
                logger.warning("H.264 codec not available, trying mp4v")
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                video_writer = cv2.VideoWriter(
                    str(output_path),
                    fourcc,
                    fps,
                    (width, height)
                )
            
            logger.info(f"Output video: {output_path}")
        
        # Process frames (limit to first 3 minutes for testing)
        frame_results = []
        frame_num = 0
        max_frames = min(total_frames, fps * 60 * 3)  # 3 minutes max
        start_time = time.time()
        session_id = video_path.stem
        unique_track_ids = set()
        # Maintain stable gender per track for cumulative stats
        track_id_to_gender: Dict[int, str] = {}
        track_id_to_gender_conf: Dict[int, float] = {}
        gender_counts = {'M': 0, 'F': 0, 'Unknown': 0}
        
        logger.info(f"Starting frame processing... (max {max_frames} frames)")
        
        def _parse_bbox_xyxy(bbox_obj):
            x1 = y1 = x2 = y2 = None
            try:
                if isinstance(bbox_obj, (list, tuple)) and len(bbox_obj) == 4:
                    x1, y1, x2, y2 = bbox_obj
                else:
                    import numpy as _np  # local import to avoid top clutter
                    if isinstance(bbox_obj, _np.ndarray) and bbox_obj.size >= 4:
                        x1, y1, x2, y2 = [float(b) for b in bbox_obj[:4].tolist()]
                    elif isinstance(bbox_obj, str):
                        vals = bbox_obj.strip('[]').replace(',', ' ').split()
                        if len(vals) >= 4:
                            x1, y1, x2, y2 = map(float, vals[:4])
            except Exception:
                x1 = None
            return x1, y1, x2, y2

        while frame_num < max_frames:
            ret, frame = cap.read()
            
            if not ret:
                break
            
            frame_num += 1
            
            # Run detection
            detections, annotated = self.detector.detect(frame, return_image=True)
            
            # Run tracking - tracker now returns detections with track_id attached
            tracked_detections = self.tracker.update(detections)
            
            # Use tracked_detections which already have track_id attached
            detections = tracked_detections

            # Integrate Re-ID (optional, every K frames)
            if self.reid_enable and self.reid_embedder is not None and self.reid_cache is not None:
                try:
                    integrate_reid_for_tracks(
                        frame,
                        detections,
                        self.reid_embedder,
                        self.reid_cache,
                        session_id=session_id,
                        every_k_frames=self.reid_every_k,
                        frame_index=frame_num,
                    )
                except Exception as e:
                    logger.warning(f"Re-ID integration error: {e}")
            
            # Update unique track id set
            for d in detections:
                t_id = d.get('track_id')
                if t_id is not None:
                    unique_track_ids.add(int(t_id))

            # Gender classification (optional, async, every K frames, budgeted per frame)
            if (
                self.gender_enable
                and self.gender_classifier is not None
                and self.gender_worker is not None
            ):
                # Poll previously enqueued tasks to harvest results
                new_pending = []
                for task_id in self._pending_gender_tasks:
                    res = self.gender_worker.try_get_result(task_id)
                    if res is None:
                        new_pending.append(task_id)
                        continue
                    gender_label, gconf, done_ts = res
                    # Parse track_id from task_id format: session:track:frame
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

                # Only enqueue every K frames
                if frame_num % self.gender_every_k == 0:
                    enqueued_this_frame = 0
                    for d in detections:
                        if enqueued_this_frame >= self.gender_max_per_frame:
                            break
                        if d.get('track_id') is None:
                            continue
                        bbox = d.get('bbox')
                        x1, y1, x2, y2 = _parse_bbox_xyxy(bbox)
                        if x1 is None:
                            continue
                        # Clamp and convert to int
                        xi1 = max(0, min(width - 1, int(x1)))
                        yi1 = max(0, min(height - 1, int(y1)))
                        xi2 = max(0, min(width - 1, int(x2)))
                        yi2 = max(0, min(height - 1, int(y2)))
                        if xi2 <= xi1 or yi2 <= yi1:
                            continue
                        
                        # Crop strategy: face detection or upper-body fallback
                        person_crop = frame[yi1:yi2, xi1:xi2].copy()
                        
                        # Try face detection if enabled
                        crop = None
                        use_face_classifier = False
                        if self.gender_enable_face_detection and self.face_detector is not None:
                            face_result = self.face_detector.detect_face(person_crop)
                            if face_result is not None:
                                face_bbox_rel, face_conf = face_result
                                crop = self.face_detector.crop_face(person_crop, face_bbox_rel)
                                use_face_classifier = True
                        
                        # Fallback to upper-body crop
                        if crop is None or crop.size == 0:
                            h_box = yi2 - yi1
                            upper_yi2 = yi1 + int(h_box * 0.6)
                            crop = frame[yi1:upper_yi2, xi1:xi2].copy()
                            use_face_classifier = False
                        if crop.size == 0:
                            continue
                        t_id_int = int(d['track_id'])
                        session_prefix = session_id
                        task_id = f"{session_prefix}:{t_id_int}:{frame_num}"

                        def _make_func(c=crop, track_id_val=t_id_int, use_face=use_face_classifier):
                            def _run():
                                start_ms = time.time() * 1000.0
                                if use_face and self.face_gender_classifier is not None:
                                    gender, gconf = self.face_gender_classifier.classify(c)
                                else:
                                    gender, gconf = self.gender_classifier.classify(c, track_id=track_id_val)
                                dur = (time.time() * 1000.0) - start_ms
                                if self.gender_metrics is not None:
                                    self.gender_metrics.observe_latency(dur)
                                return gender, float(gconf)

                            return _run

                        ok = self.gender_worker.enqueue(task_id=task_id, priority=1, func=_make_func())
                        if ok:
                            self._pending_gender_tasks.append(task_id)
                            enqueued_this_frame += 1
                            if self.gender_metrics is not None:
                                self.gender_metrics.inc_call()
                        else:
                            if self.gender_metrics is not None:
                                self.gender_metrics.inc_dropped()

                # Update metrics snapshot periodically
                if self.gender_metrics is not None and frame_num % 100 == 0:
                    snap = self.gender_metrics.snapshot()
                    logger.info(
                        "Gender metrics @frame %d: qlen=%d calls=%d res=%d p50=%.1fms p95=%.1fms",
                        frame_num,
                        len(self._pending_gender_tasks),
                        int(snap["calls_total"]),
                        int(snap["results_total"]),
                        snap["latency_ms_p50"],
                        snap["latency_ms_p95"],
                    )

                # Attach latest gender info to current frame detections for rendering
                for d in detections:
                    t_id = d.get('track_id')
                    if t_id is None:
                        continue
                    t_id_int2 = int(t_id)
                    if t_id_int2 in track_id_to_gender:
                        d['gender'] = track_id_to_gender[t_id_int2]
                        if t_id_int2 in track_id_to_gender_conf:
                            d['gender_confidence'] = track_id_to_gender_conf[t_id_int2]

                # Recompute gender counts from current stable map
                gender_counts = {'M': 0, 'F': 0, 'Unknown': 0}
                for g in track_id_to_gender.values():
                    if g in gender_counts:
                        gender_counts[g] += 1

            # Store results
            frame_results.append({
                'frame_number': frame_num,
                'detection_count': len(detections),
                'tracked_count': len([d for d in detections if d.get('track_id') is not None]),
                'unique_count': len(unique_track_ids),
                'gender_counts': gender_counts,
                'detections': detections,
                'tracks': [d for d in detections if d.get('track_id') is not None]
            })
            
            # Redraw annotations with track IDs if needed
            if annotated is None and len(detections) > 0:
                annotated = self.detector.processor.draw_detections(frame, detections)
            elif annotated is not None:
                # Redraw to include track IDs
                annotated = self.detector.processor.draw_detections(annotated, detections)
            
            # Add overlay with info
            if save_annotated:
                tracked_count = len([d for d in detections if d.get('track_id') is not None])
                unique_count = len(unique_track_ids)
                if annotated is not None:
                    annotated = self._add_overlay(
                        annotated, frame_num, len(detections), tracked_count, unique_count,
                        gender_counts,
                        time.time() - start_time,
                        self.detector.model_loader.get_device(),
                        self.detector.model_loader.is_mps_enabled()
                    )
                else:
                    annotated = self._add_overlay(
                        frame, frame_num, len(detections), tracked_count, unique_count,
                        gender_counts,
                        time.time() - start_time,
                        self.detector.model_loader.get_device(),
                        self.detector.model_loader.is_mps_enabled()
                    )
                
                video_writer.write(annotated)
            
            # Progress logging
            if frame_num % 100 == 0:
                progress = (frame_num / total_frames) * 100
                logger.info(f"Progress: {progress:.1f}% ({frame_num}/{total_frames} frames)")
        
        # Cleanup
        cap.release()
        if video_writer:
            video_writer.release()
        # Shutdown async worker
        if self.gender_worker is not None:
            self.gender_worker.shutdown()
        # Release face detector and classifier
        if self.face_detector is not None:
            self.face_detector.release()
        if self.face_gender_classifier is not None:
            self.face_gender_classifier.release()
        
        processing_time = time.time() - start_time
        
        # Generate report
        report = {
            'video_file': str(video_path),
            'timestamp': datetime.now().isoformat(),
            'video_properties': {
                'width': width,
                'height': height,
                'fps': fps,
                'total_frames': total_frames
            },
            'processing': {
                'time_seconds': processing_time,
                'avg_time_per_frame_ms': (processing_time / frame_num) * 1000 if frame_num > 0 else 0
            },
            'detector_stats': self.detector.get_statistics(),
            'frame_results': frame_results,
            'summary': {
                'unique_tracks_total': len(unique_track_ids),
                'gender_counts_total': gender_counts
            }
        }
        
        # Save report
        report_path = self.output_dir / f"report_{video_path.stem}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Processing complete in {processing_time:.2f}s")
        logger.info(f"Report saved: {report_path}")
        
        return report
    
    def release(self) -> None:
        """Release resources."""
        self.detector.release()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Process video file with person detection'
    )
    
    parser.add_argument(
        'video_path',
        type=str,
        help='Path to input video file'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        default='yolov8n.pt',
        help='Path to YOLOv8 model (default: yolov8n.pt)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='output/videos',
        help='Output directory (default: output/videos)'
    )
    
    parser.add_argument(
        '--conf-threshold',
        type=float,
        default=0.5,
        help='Confidence threshold (default: 0.5)'
    )
    
    parser.add_argument(
        '--tracker-max-age',
        type=int,
        default=30,
        help='Tracker max_age frames before deletion (default: 30)'
    )
    
    parser.add_argument(
        '--tracker-min-hits',
        type=int,
        default=3,
        help='Tracker min_hits before confirmation (default: 3)'
    )
    
    parser.add_argument(
        '--tracker-iou-threshold',
        type=float,
        default=0.3,
        help='Tracker IoU threshold for matching (default: 0.3)'
    )
    
    parser.add_argument(
        '--tracker-ema-alpha',
        type=float,
        default=0.5,
        help='Tracker EMA alpha for bbox smoothing (0-1, default: 0.5)'
    )
    
    parser.add_argument(
        '--no-annotate',
        action='store_true',
        help='Do not save annotated video'
    )

    parser.add_argument(
        '--reid-enable',
        action='store_true',
        help='Enable Re-ID embedding and caching (default: disabled)'
    )

    parser.add_argument(
        '--reid-every-k',
        type=int,
        default=10,
        help='Compute embeddings every K frames when Re-ID is enabled (default: 10)'
    )

    parser.add_argument(
        '--reid-ttl-seconds',
        type=int,
        default=60,
        help='TTL seconds for Re-ID cache entries (default: 60)'
    )

    parser.add_argument(
        '--gender-enable',
        action='store_true',
        help='Enable gender classification on tracked persons'
    )

    parser.add_argument(
        '--gender-every-k',
        type=int,
        default=20,
        help='Classify gender every K frames (default: 20)'
    )

    parser.add_argument(
        '--gender-model-type',
        type=str,
        default='timm_mobile',
        choices=['simple', 'timm_mobile'],
        help='Gender classification model type (default: timm_mobile). Recommended: timm_mobile (MobileNetV3-Small)'
    )
    parser.add_argument(
        '--gender-max-per-frame',
        type=int,
        default=4,
        help='Max gender tasks per frame (default: 4)'
    )
    parser.add_argument(
        '--gender-timeout-ms',
        type=int,
        default=50,
        help='Soft timeout per gender task in ms (default: 50)'
    )
    parser.add_argument(
        '--gender-queue-size',
        type=int,
        default=256,
        help='Max queue size for async gender worker (default: 256)'
    )
    parser.add_argument(
        '--gender-workers',
        type=int,
        default=2,
        help='Number of worker threads for async gender (default: 2)'
    )
    parser.add_argument(
        '--gender-min-confidence',
        type=float,
        default=0.4,
        help='Minimum confidence threshold for gender classification (default: 0.4)'
    )
    parser.add_argument(
        '--gender-voting-window',
        type=int,
        default=25,
        help='Voting window size for gender stability (default: 25)'
    )
    parser.add_argument(
        '--gender-enable-face-detection',
        action='store_true',
        help='Use face detection for improved gender accuracy (default: disabled, uses upper-body)'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG','INFO','WARNING','ERROR','CRITICAL'],
        help='Logging level (default: INFO)'
    )
    
    args = parser.parse_args()
    
    try:
        # Configure logging level dynamically
        try:
            level = getattr(logging, args.log_level.upper(), logging.INFO)
        except Exception:
            level = logging.INFO
        logging.getLogger().setLevel(level)
        logging.getLogger('modules.demographics.gender_classifier').setLevel(level)
        logging.getLogger('modules.demographics.async_worker').setLevel(level)
        logging.getLogger('modules.demographics.metrics').setLevel(level)
        logging.getLogger('modules.detection.detector').setLevel(level)
        logging.getLogger('modules.detection.image_processor').setLevel(level)

        video_path = Path(args.video_path)
        
        if not video_path.exists():
            logger.error(f"Video file not found: {video_path}")
            sys.exit(1)
        
        processor = VideoProcessor(
            model_path=args.model,
            output_dir=args.output,
            conf_threshold=args.conf_threshold,
            tracker_max_age=args.tracker_max_age,
            tracker_min_hits=args.tracker_min_hits,
            tracker_iou_threshold=args.tracker_iou_threshold,
            tracker_ema_alpha=args.tracker_ema_alpha,
            reid_enable=bool(args.reid_enable),
            reid_every_k=args.reid_every_k,
            reid_ttl_seconds=args.reid_ttl_seconds,
            gender_enable=bool(args.gender_enable),
            gender_every_k=args.gender_every_k,
                gender_model_type=args.gender_model_type,
                gender_max_per_frame=args.gender_max_per_frame,
                gender_timeout_ms=args.gender_timeout_ms,
                gender_queue_size=args.gender_queue_size,
                gender_workers=args.gender_workers,
                gender_min_confidence=args.gender_min_confidence,
                gender_voting_window=args.gender_voting_window,
                gender_enable_face_detection=args.gender_enable_face_detection,
        )
        
        try:
            report = processor.process_video(
                video_path,
                save_annotated=not args.no_annotate
            )
            
            # Print summary
            print("\n" + "="*60)
            print("PROCESSING SUMMARY")
            print("="*60)
            print(f"Video: {report['video_file']}")
            print(f"Frames: {report['video_properties']['total_frames']}")
            print(f"Processing time: {report['processing']['time_seconds']:.2f}s")
            print(f"Avg time per frame: {report['processing']['avg_time_per_frame_ms']:.2f}ms")
            print(f"Device: {report['detector_stats']['device']}")
            print(f"MPS enabled: {report['detector_stats']['mps_enabled']}")
            print("="*60)
            
        finally:
            processor.release()
        
        logger.info("Video processing completed successfully")
        
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Error processing video: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

