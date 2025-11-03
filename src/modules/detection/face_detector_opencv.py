#!/usr/bin/env python3
"""
OpenCV DNN Face Detection for full-frame person detection.

Replaces MediaPipe to avoid TensorFlow/protobuf conflicts.
Uses OpenCV's FaceDetectorYN (YuNet) for fast, accurate face detection.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class FaceDetectorOpenCV:
    """
    Full-frame face detector using OpenCV DNN (YuNet).

    Detects faces directly from full frame, then expands to estimate full body.
    """

    def __init__(
        self,
        min_detection_confidence: float = 0.5,
        model_selection: int = 1,  # 0=short range, 1=full range
        body_expand_ratio: float = 2.5,  # Expand face bbox by this ratio for full body
        body_expand_vertical: float = 0.4,  # Expand downward more
        model_path: Optional[str] = None,
        input_size: tuple[int, int] = (320, 320),
        detect_resize: Optional[tuple[int, int]] = None,  # Resize frame for faster detection
    ) -> None:
        """
        Initialize OpenCV DNN face detector.

        Args:
            min_detection_confidence: Minimum confidence for face detection
            model_selection: 0 for close faces (<2m), 1 for far faces (2-5m)
            body_expand_ratio: Ratio to expand face bbox for full body estimate
            body_expand_vertical: Additional vertical expansion ratio
            model_path: Path to ONNX model file (None = auto-download)
            input_size: Input size for detector (width, height)
        """
        self.min_detection_confidence = min_detection_confidence
        self.model_selection = model_selection
        self.body_expand_ratio = body_expand_ratio
        self.body_expand_vertical = body_expand_vertical
        self.input_size = input_size
        
        # Resize frame for faster detection (default: 640x480 for balance of speed/accuracy)
        if detect_resize is None:
            # Use smaller size for faster detection while maintaining accuracy
            detect_resize = (640, 480)  # Faster than full 1920x1080
        self.detect_resize = detect_resize
        self._last_input_size = None  # Cache for input size

        # Determine model path
        if model_path is None:
            model_path = self._get_default_model_path()

        # Try to enable OpenCL backend for GPU acceleration
        self._use_opencl = False
        try:
            if cv2.ocl.haveOpenCL():
                cv2.ocl.setUseOpenCL(True)
                self._use_opencl = True
                logger.info("OpenCL backend enabled for GPU acceleration")
        except Exception as e:
            logger.debug("OpenCL not available or failed to enable: %s", e)

        # Initialize OpenCV Face Detector
        try:
            self.face_detector = cv2.FaceDetectorYN.create(
                model=model_path,
                config="",
                input_size=input_size,
                score_threshold=min_detection_confidence,
                nms_threshold=0.3,
                top_k=5000,
            )
            backend_info = " (OpenCL GPU)" if self._use_opencl else " (CPU)"
            logger.info(
                "FaceDetectorOpenCV initialized: confidence=%.2f, model=%s, input_size=%s%s",
                min_detection_confidence,
                Path(model_path).name,
                input_size,
                backend_info,
            )
        except Exception as e:
            logger.error("Failed to initialize OpenCV face detector: %s", e)
            # Try to download model if missing
            if not Path(model_path).exists():
                logger.info("Attempting to download model...")
                model_path = self._download_model()
                try:
                    self.face_detector = cv2.FaceDetectorYN.create(
                        model=model_path,
                        config="",
                        input_size=input_size,
                        score_threshold=min_detection_confidence,
                        nms_threshold=0.3,
                        top_k=5000,
                    )
                    logger.info("Successfully initialized with downloaded model")
                except Exception as e2:
                    logger.error("Failed after download attempt: %s", e2)
                    raise ImportError(
                        "OpenCV face detector initialization failed. "
                        "Please download model manually."
                    ) from e2
            else:
                raise

    def _get_default_model_path(self) -> str:
        """Get default model path, create directory if needed."""
        model_dir = Path("models/face_detection")
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Use full-range model for CCTV (model_selection=1)
        model_name = "face_detection_yunet_2023mar.onnx"
        model_path = model_dir / model_name
        
        return str(model_path)

    def _download_model(self) -> str:
        """Download YuNet model from OpenCV Zoo."""
        import urllib.request
        
        model_dir = Path("models/face_detection")
        model_dir.mkdir(parents=True, exist_ok=True)
        
        model_name = "face_detection_yunet_2023mar.onnx"
        model_path = model_dir / model_name
        
        if model_path.exists():
            return str(model_path)
        
        url = (
            "https://github.com/opencv/opencv_zoo/raw/main/models/"
            "face_detection_yunet/face_detection_yunet_2023mar.onnx"
        )
        
        logger.info("Downloading YuNet model from %s", url)
        try:
            urllib.request.urlretrieve(url, str(model_path))
            logger.info("Model downloaded successfully to %s", model_path)
            return str(model_path)
        except Exception as e:
            logger.error("Failed to download model: %s", e)
            raise ImportError(
                f"Failed to download face detection model. "
                f"Please download manually from: {url}"
            ) from e

    def detect_persons_from_faces(
        self, frame: np.ndarray
    ) -> List[Dict[str, Any]]:
        """
        Detect persons by detecting faces first, then expanding to full body.

        Args:
            frame: Full frame from camera (BGR format)

        Returns:
            List of person detections in format:
            {
                "bbox": [x1, y1, x2, y2],
                "confidence": float,
                "class_id": 0,
                "class_name": "person",
                "face_bbox": [x1, y1, x2, y2],  # Original face bbox
            }
        """
        if self.face_detector is None:
            return []

        try:
            h, w = frame.shape[:2]
            
            # Resize frame for faster detection if needed
            if self.detect_resize is not None:
                detect_w, detect_h = self.detect_resize
                # Only resize if frame is larger than detect size
                if w > detect_w or h > detect_h:
                    scale_w = detect_w / w
                    scale_h = detect_h / h
                    scale = min(scale_w, scale_h)
                    new_w = int(w * scale)
                    new_h = int(h * scale)
                    detect_frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
                    input_size = (new_w, new_h)
                    scale_factor_x = w / new_w
                    scale_factor_y = h / new_h
                else:
                    detect_frame = frame
                    input_size = (w, h)
                    scale_factor_x = 1.0
                    scale_factor_y = 1.0
            else:
                detect_frame = frame
                input_size = (w, h)
                scale_factor_x = 1.0
                scale_factor_y = 1.0
            
            # Set input size (cache to avoid repeated calls)
            if self._last_input_size != input_size:
                self.face_detector.setInputSize(input_size)
                self._last_input_size = input_size

            # Run face detection on (possibly resized) frame
            _, faces = self.face_detector.detect(detect_frame)

            # Log detection result for debugging
            logger.debug(
                "FaceDetectorOpenCV.detect: input_size=%s, faces=%s",
                input_size,
                "None" if faces is None else f"{len(faces)} faces"
            )

            person_detections = []
            rejected_by_confidence = 0

            if faces is not None and len(faces) > 0:
                logger.info("Found %d raw faces from YuNet detector", len(faces))
                
                # Apply NMS (Non-Maximum Suppression) to merge overlapping face detections
                # This prevents duplicate detections from the same person
                filtered_faces = self._nms_faces(faces)
                logger.info(
                    "After NMS: %d faces (removed %d duplicates)",
                    len(filtered_faces),
                    len(faces) - len(filtered_faces)
                )
                
                for face in filtered_faces:
                    # face format: [x, y, w, h, x_re, y_re, x_le, y_le, x_nt, y_nt, x_rcm, y_rcm, x_lcm, y_lcm]
                    # x, y, w, h: bounding box
                    # x_re, y_re: right eye
                    # x_le, y_le: left eye
                    # x_nt, y_nt: nose tip
                    # x_rcm, y_rcm: right corner of mouth
                    # x_lcm, y_lcm: left corner of mouth
                    
                    confidence = float(face[14])  # Confidence score
                    
                    # Log confidence for debugging
                    logger.debug("Face confidence: %.3f, threshold: %.3f", confidence, self.min_detection_confidence)
                    
                    # Skip if confidence too low
                    if confidence < self.min_detection_confidence:
                        rejected_by_confidence += 1
                        logger.info("Rejected face: confidence %.3f < threshold %.3f", confidence, self.min_detection_confidence)
                        continue
                    
                    # Get face bbox from detection (on resized frame) FIRST
                    # Need face_x, face_y, face_w, face_h for landmark validation
                    face_x = float(face[0])
                    face_y = float(face[1])
                    face_w = float(face[2])
                    face_h = float(face[3])
                    
                    # Extract landmarks for validation
                    # face format: [x, y, w, h, x_re, y_re, x_le, y_le, x_nt, y_nt, x_rcm, y_rcm, x_lcm, y_lcm, confidence]
                    right_eye_x = float(face[4])
                    right_eye_y = float(face[5])
                    left_eye_x = float(face[6])
                    left_eye_y = float(face[7])
                    nose_tip_x = float(face[8])
                    nose_tip_y = float(face[9])
                    mouth_right_x = float(face[10])
                    mouth_right_y = float(face[11])
                    mouth_left_x = float(face[12])
                    mouth_left_y = float(face[13])
                    
                    # Smart landmark validation: Only validate suspicious detections
                    # Channel 1: Always validate (known false positive issue)
                    # Other channels: Only validate confidence 0.60-0.80 (suspicious range)
                    # Real faces usually have confidence > 0.80, motorcycles often 0.60-0.75
                    landmark_valid = True  # Default: allow face
                    
                    # Apply landmark validation based on channel and confidence
                    if channel_id == 1:
                        # Channel 1: Always validate (known motorcycle false positives)
                        landmark_valid = self._validate_face_landmarks(
                            right_eye_x, right_eye_y,
                            left_eye_x, left_eye_y,
                            nose_tip_x, nose_tip_y,
                            mouth_right_x, mouth_right_y,
                            mouth_left_x, mouth_left_y,
                            face_x, face_y, face_w, face_h
                        )
                    elif 0.60 <= confidence < 0.80:
                        # Other channels: Only validate suspicious confidence range
                        logger.debug(
                            "Applying landmark validation: confidence %.3f in suspicious range",
                            confidence
                        )
                        landmark_valid = self._validate_face_landmarks(
                            right_eye_x, right_eye_y,
                            left_eye_x, left_eye_y,
                            nose_tip_x, nose_tip_y,
                            mouth_right_x, mouth_right_y,
                            mouth_left_x, mouth_left_y,
                            face_x, face_y, face_w, face_h
                        )
                    
                    if not landmark_valid:
                        logger.info(
                            "Rejected face: invalid landmark geometry (confidence=%.3f, likely false positive)",
                            confidence
                        )
                        continue
                    
                    # Scale coordinates back to original frame size
                    face_x = face_x * scale_factor_x
                    face_y = face_y * scale_factor_y
                    face_w = face_w * scale_factor_x
                    face_h = face_h * scale_factor_y
                    
                    face_x2 = face_x + face_w
                    face_y2 = face_y + face_h

                    # Convert to int and clamp to original frame boundaries
                    face_x = int(max(0, min(face_x, w - 1)))
                    face_y = int(max(0, min(face_y, h - 1)))
                    face_x2 = int(max(0, min(face_x2, w)))
                    face_y2 = int(max(0, min(face_y2, h)))

                    if face_x2 <= face_x or face_y2 <= face_y:
                        continue

                    # Validate face size - must be reasonable for a real face
                    face_w_actual = face_x2 - face_x
                    face_h_actual = face_y2 - face_y
                    
                    # Channel-specific minimum face size
                    # Indoor cameras (3,4): faces closer → can use higher minimum
                    # Outdoor cameras (1,2): faces further → need lower minimum
                    # But after scaling, faces may become smaller → use lower threshold
                    if channel_id in [3, 4]:
                        min_face_size = 16  # Indoor: faces close but may be small after scaling
                    else:
                        min_face_size = 12  # Outdoor: faces far away, accept smaller after scaling
                    
                    if face_w_actual < min_face_size or face_h_actual < min_face_size:
                        logger.debug(
                            "Rejected face: too small (%dx%d < %dx%d, channel=%s)",
                            face_w_actual, face_h_actual, min_face_size, min_face_size, channel_id
                        )
                        continue
                    
                    # Validate face aspect ratio (should be roughly square)
                    # Nới lỏng hơn cho outdoor cameras (0.5-1.5) vì góc nhìn khác nhau
                    # Outdoor cameras có góc nhìn rộng → faces có thể bị dẹp hơn
                    face_aspect_ratio = face_w_actual / face_h_actual if face_h_actual > 0 else 0
                    min_aspect = 0.5  # Further reduced from 0.6 for outdoor cameras
                    max_aspect = 1.5  # Increased from 1.4 for wider angle views
                    # Use <= instead of < to avoid floating point precision issues
                    if face_aspect_ratio <= min_aspect or face_aspect_ratio >= max_aspect:
                        logger.info(
                            "Rejected face: invalid aspect ratio (%.3f, expected %.2f-%.2f)",
                            face_aspect_ratio, min_aspect, max_aspect
                        )
                        continue
                    
                    # Estimate full body bounding box from face position
                    # Strategy: Face is typically in upper-middle of body
                    # Expand downward and slightly outward
                    face_center_x = (face_x + face_x2) / 2
                    face_center_y = (face_y + face_y2) / 2

                    # Estimate body width (wider than face)
                    body_width = face_w_actual * self.body_expand_ratio
                    body_height = face_h_actual * self.body_expand_ratio * (
                        1 + self.body_expand_vertical
                    )

                    # Center body bbox on face, but shift downward
                    # Face is typically at top 1/3 of body
                    body_x1 = int(face_center_x - body_width / 2)
                    body_y1 = int(face_center_y - face_h_actual * 0.5)  # Face at top
                    body_x2 = int(body_x1 + body_width)
                    body_y2 = int(body_y1 + body_height)

                    # Clamp to frame boundaries
                    body_x1 = max(0, min(body_x1, w - 1))
                    body_y1 = max(0, min(body_y1, h - 1))
                    body_x2 = max(0, min(body_x2, w))
                    body_y2 = max(0, min(body_y2, h))

                    if body_x2 > body_x1 and body_y2 > body_y1:
                        person_detections.append(
                            {
                                "bbox": [body_x1, body_y1, body_x2, body_y2],
                                "confidence": confidence,
                                "class_id": 0,
                                "class_name": "person",
                                "face_bbox": [face_x, face_y, face_x2, face_y2],
                            }
                        )
                
                # Log summary
                if rejected_by_confidence > 0:
                    logger.debug(
                        "Rejected %d faces due to low confidence (threshold=%.2f)",
                        rejected_by_confidence,
                        self.min_detection_confidence
                    )
            elif faces is not None:
                logger.debug("YuNet returned empty faces array")
            else:
                logger.debug("YuNet returned None (no faces detected)")

            return person_detections

        except Exception as e:
            logger.error("Face detection error: %s", e)
            return []
    
    def _validate_face_landmarks(
        self,
        right_eye_x: float, right_eye_y: float,
        left_eye_x: float, left_eye_y: float,
        nose_tip_x: float, nose_tip_y: float,
        mouth_right_x: float, mouth_right_y: float,
        mouth_left_x: float, mouth_left_y: float,
        face_x: float, face_y: float, face_w: float, face_h: float
    ) -> bool:
        """
        Validate face landmarks to reject false positives (motorcycles, objects).
        
        Real faces have landmarks in specific geometric relationships:
        - Eyes are roughly at same height (y coordinate)
        - Nose is below eyes, above mouth
        - Mouth is below nose
        - Landmarks are roughly symmetric
        - All landmarks are within face bbox
        
        Args:
            right_eye_x, right_eye_y: Right eye coordinates
            left_eye_x, left_eye_y: Left eye coordinates
            nose_tip_x, nose_tip_y: Nose tip coordinates
            mouth_right_x, mouth_right_y: Right mouth corner
            mouth_left_x, mouth_left_y: Left mouth corner
            face_x, face_y, face_w, face_h: Face bounding box
            
        Returns:
            True if landmarks are valid (likely real face), False otherwise
        """
        # Check if landmarks are within face bbox (with some tolerance)
        tolerance = 0.2  # 20% tolerance for landmark positions
        face_x1, face_y1 = face_x, face_y
        face_x2, face_y2 = face_x + face_w, face_y + face_h
        
        landmarks = [
            (right_eye_x, right_eye_y),
            (left_eye_x, left_eye_y),
            (nose_tip_x, nose_tip_y),
            (mouth_right_x, mouth_right_y),
            (mouth_left_x, mouth_left_y),
        ]
        
        # Count valid landmarks (non-zero)
        valid_landmarks = 0
        for x, y in landmarks:
            # Skip if landmark is invalid (0 or negative usually means not detected)
            if x > 0 and y > 0:
                valid_landmarks += 1
        
        # If too few landmarks are valid, likely false positive
        # But allow some flexibility - at least 3 out of 5 landmarks should be valid
        if valid_landmarks < 3:
            logger.debug("Landmark validation failed: too few valid landmarks (%d < 3)", valid_landmarks)
            return False
        
        # Re-check landmarks within bbox with validated landmarks only
        for x, y in landmarks:
            if x <= 0 or y <= 0:
                continue
            
            # Check if landmark is within face bbox (with tolerance)
            if (x < face_x1 - face_w * tolerance or x > face_x2 + face_w * tolerance or
                y < face_y1 - face_h * tolerance or y > face_y2 + face_h * tolerance):
                # Landmark outside face bbox → likely false positive
                return False
        
        # Validate geometric relationships
        # 1. Eyes should be roughly at same height (difference < 30% of face height)
        # Increased tolerance from 20% to 30% to allow for angle variations
        eye_height_diff = abs(right_eye_y - left_eye_y)
        if eye_height_diff > face_h * 0.3:
            logger.debug("Landmark validation failed: eyes not aligned (diff=%.1f > %.1f)", eye_height_diff, face_h * 0.3)
            return False  # Eyes not aligned → not a real face
        
        # 2. Nose should be between eyes (horizontally) and below them (vertically)
        eye_center_x = (right_eye_x + left_eye_x) / 2
        eye_center_y = (right_eye_y + left_eye_y) / 2
        
        # Nose should be below eyes
        if nose_tip_y <= eye_center_y:
            return False  # Nose above eyes → invalid
        
        # Nose should be roughly centered horizontally (within 40% of face width)
        # Increased tolerance from 30% to 40% for side profiles
        nose_horizontal_offset = abs(nose_tip_x - eye_center_x)
        if nose_horizontal_offset > face_w * 0.4:
            logger.debug("Landmark validation failed: nose too far from center (offset=%.1f > %.1f)", nose_horizontal_offset, face_w * 0.4)
            return False  # Nose too far from center → invalid
        
        # 3. Mouth should be below nose
        mouth_center_y = (mouth_right_y + mouth_left_y) / 2
        if mouth_center_y <= nose_tip_y:
            return False  # Mouth above nose → invalid
        
        # 4. Vertical ordering: eyes > nose > mouth
        # Allow some tolerance for detection inaccuracies
        if not (eye_center_y < nose_tip_y < mouth_center_y):
            logger.debug("Landmark validation failed: invalid vertical ordering (eyes=%.1f, nose=%.1f, mouth=%.1f)", 
                        eye_center_y, nose_tip_y, mouth_center_y)
            return False
        
        # 5. Eyes should be roughly symmetric (similar distance from face center)
        # Increased tolerance from 25% to 35% for side profiles and angles
        face_center_x = face_x + face_w / 2
        right_eye_offset = abs(right_eye_x - face_center_x)
        left_eye_offset = abs(left_eye_x - face_center_x)
        eye_symmetry_diff = abs(right_eye_offset - left_eye_offset)
        if eye_symmetry_diff > face_w * 0.35:
            logger.debug("Landmark validation failed: eyes too asymmetric (diff=%.1f > %.1f)", eye_symmetry_diff, face_w * 0.35)
            return False  # Eyes too asymmetric → invalid
        
        # All validations passed → likely real face
        return True
    
    def _nms_faces(self, faces: np.ndarray, iou_threshold: float = 0.3) -> np.ndarray:
        """
        Apply Non-Maximum Suppression (NMS) to merge overlapping face detections.
        
        This prevents duplicate detections from the same person when face detector
        detects multiple faces (e.g., profile + front view, reflections).
        
        Args:
            faces: Array of face detections from YuNet
            iou_threshold: IoU threshold for merging (default 0.3)
            
        Returns:
            Filtered faces array with duplicates removed
        """
        if faces is None or len(faces) == 0:
            return faces
        
        if len(faces) == 1:
            return faces
        
        # Extract bboxes and confidences
        bboxes = []
        confidences = []
        for face in faces:
            x, y, w, h = float(face[0]), float(face[1]), float(face[2]), float(face[3])
            confidence = float(face[14])
            bboxes.append([x, y, x + w, y + h])
            confidences.append(confidence)
        
        # Convert to numpy for NMS
        bboxes_np = np.array(bboxes, dtype=np.float32)
        confidences_np = np.array(confidences, dtype=np.float32)
        
        # Use OpenCV NMS
        try:
            indices = cv2.dnn.NMSBoxes(
                bboxes_np.tolist(),
                confidences_np.tolist(),
                score_threshold=self.min_detection_confidence,
                nms_threshold=iou_threshold
            )
            
            if indices is None or len(indices) == 0:
                return faces
            
            # Flatten indices (OpenCV returns nested array)
            indices = indices.flatten() if len(indices.shape) > 1 else indices
            
            # Return filtered faces
            return faces[indices]
        except Exception as e:
            logger.warning("NMS failed, returning all faces: %s", e)
            return faces

    def release(self) -> None:
        """Release resources."""
        self.face_detector = None
        logger.info("Face detector resources released")

