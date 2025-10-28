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
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.detection.detector import Detector

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
        conf_threshold: float = 0.5
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
        
        logger.info(f"Video processor initialized")
        logger.info(f"Device: {self.detector.model_loader.get_device()}")
        logger.info(f"MPS enabled: {self.detector.model_loader.is_mps_enabled()}")
    
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
        
        logger.info(f"Starting frame processing... (max {max_frames} frames)")
        
        while frame_num < max_frames:
            ret, frame = cap.read()
            
            if not ret:
                break
            
            frame_num += 1
            
            # Run detection
            detections, annotated = self.detector.detect(frame, return_image=True)
            
            # Store results
            frame_results.append({
                'frame_number': frame_num,
                'detection_count': len(detections),
                'detections': detections
            })
            
            # Write annotated frame
            if save_annotated and annotated is not None:
                video_writer.write(annotated)
            elif save_annotated:
                video_writer.write(frame)
            
            # Progress logging
            if frame_num % 100 == 0:
                progress = (frame_num / total_frames) * 100
                logger.info(f"Progress: {progress:.1f}% ({frame_num}/{total_frames} frames)")
        
        # Cleanup
        cap.release()
        if video_writer:
            video_writer.release()
        
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
            'frame_results': frame_results
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
        '--no-annotate',
        action='store_true',
        help='Do not save annotated video'
    )
    
    args = parser.parse_args()
    
    try:
        video_path = Path(args.video_path)
        
        if not video_path.exists():
            logger.error(f"Video file not found: {video_path}")
            sys.exit(1)
        
        processor = VideoProcessor(
            model_path=args.model,
            output_dir=args.output,
            conf_threshold=args.conf_threshold
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

