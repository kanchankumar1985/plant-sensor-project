#!/usr/bin/env python3
"""
Video capture for temperature alerts
Records short video clips when temperature threshold is exceeded
"""
import os
import cv2
import time
import subprocess
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Use centralized logging
import logging_config
logger = logging_config.get_camera_logger()

# Video storage configuration
VIDEOS_DIR = Path(os.getenv('VIDEOS_DIR', str(Path(__file__).parent / "videos")))
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

# Video settings (configurable via environment variables)
VIDEO_ALERT_ENABLED = os.getenv('VIDEO_ALERT_ENABLED', 'true').lower() == 'true'
VIDEO_ALERT_DURATION = int(os.getenv('VIDEO_ALERT_DURATION', '5'))  # seconds
VIDEO_ALERT_FPS = int(os.getenv('VIDEO_ALERT_FPS', '25'))  # frames per second

# Camera settings (same as capture_snapshot.py)
CAMERA_AUTO_EXPOSURE = int(os.getenv('CAMERA_AUTO_EXPOSURE', '1'))
CAMERA_EXPOSURE = int(os.getenv('CAMERA_EXPOSURE', '-6'))
CAMERA_BRIGHTNESS = int(os.getenv('CAMERA_BRIGHTNESS', '128'))
CAMERA_CONTRAST = int(os.getenv('CAMERA_CONTRAST', '32'))

def record_video_alert(duration=None, fps=None):
    """
    Record a short video clip from webcam
    
    Args:
        duration: Video duration in seconds (uses VIDEO_ALERT_DURATION if None)
        fps: Frames per second (uses VIDEO_ALERT_FPS if None)
        
    Returns:
        str: Filename of recorded video, or None if failed
    """
    if not VIDEO_ALERT_ENABLED:
        logger.info("📹 Video alerts disabled in config")
        return None
    
    duration = duration or VIDEO_ALERT_DURATION
    fps = fps or VIDEO_ALERT_FPS
    
    try:
        logger.info(f"🎥 Starting video recording ({duration}s at {fps} FPS)...")
        
        # Initialize webcam
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            logger.info("❌ Cannot open webcam for video recording")
            return None
        
        # Set camera properties
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, CAMERA_AUTO_EXPOSURE)
        cap.set(cv2.CAP_PROP_EXPOSURE, CAMERA_EXPOSURE)
        cap.set(cv2.CAP_PROP_BRIGHTNESS, CAMERA_BRIGHTNESS)
        cap.set(cv2.CAP_PROP_CONTRAST, CAMERA_CONTRAST)
        cap.set(cv2.CAP_PROP_FPS, fps)
        
        # Get frame dimensions
        ret, frame = cap.read()
        if not ret:
            logger.info("❌ Failed to read frame from webcam")
            cap.release()
            return None
        
        height, width, _ = frame.shape
        
        # Generate timestamp-based filename (temporary AVI, will convert to MP4)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_filename = f"alert_{timestamp}_temp.avi"
        final_filename = f"alert_{timestamp}.mp4"
        temp_filepath = VIDEOS_DIR / temp_filename
        final_filepath = VIDEOS_DIR / final_filename
        
        # Use MJPG codec for temporary file (always works)
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        out = cv2.VideoWriter(str(temp_filepath), fourcc, fps, (width, height))
        
        if not out.isOpened():
            logger.info(f"❌ Failed to create video writer")
            cap.release()
            return None
        
        # Record video with consistent timing
        start_time = time.time()
        frame_count = 0
        frame_interval = 1.0 / fps  # Time between frames
        
        while (time.time() - start_time) < duration:
            frame_start = time.time()
            
            ret, frame = cap.read()
            if ret:
                out.write(frame)
                frame_count += 1
                
                # Maintain consistent FPS by sleeping if needed
                elapsed = time.time() - frame_start
                if elapsed < frame_interval:
                    time.sleep(frame_interval - elapsed)
            else:
                logger.info("⚠️  Failed to capture frame, continuing...")
        
        # Release resources
        cap.release()
        out.release()
        
        # Convert AVI to MP4 using ffmpeg for browser compatibility
        logger.info(f"🔄 Converting to MP4 format...")
        try:
            subprocess.run([
                'ffmpeg', '-i', str(temp_filepath),
                '-c:v', 'libx264',  # H.264 codec (widely supported)
                '-preset', 'fast',   # Fast encoding
                '-crf', '23',        # Quality (lower = better, 23 is default)
                '-y',                # Overwrite output file
                str(final_filepath)
            ], check=True, capture_output=True)
            
            # Remove temporary AVI file
            temp_filepath.unlink()
            
            # Verify MP4 file was created
            if final_filepath.exists() and final_filepath.stat().st_size > 0:
                file_size_kb = final_filepath.stat().st_size / 1024
                logger.info(f"✅ Video recorded: {final_filename}")
                logger.info(f"   📹 Duration: {duration}s")
                logger.info(f"   🎞️  Frames: {frame_count}")
                logger.info(f"   📦 Size: {file_size_kb:.1f} KB")
                return final_filename
            else:
                logger.info(f"❌ MP4 file not created or empty")
                return None
                
        except subprocess.CalledProcessError as e:
            logger.info(f"❌ FFmpeg conversion failed: {e}")
            # If conversion fails, try to use the AVI file
            if temp_filepath.exists():
                temp_filepath.rename(final_filepath.with_suffix('.avi'))
                return final_filename.replace('.mp4', '.avi')
            return None
        except Exception as e:
            logger.info(f"❌ Video conversion error: {e}")
            return None
        
    except Exception as e:
        logger.info(f"❌ Video recording failed: {e}")
        if 'cap' in locals():
            cap.release()
        if 'out' in locals():
            out.release()
        return None

if __name__ == "__main__":
    # Test video recording
    logger.info("🧪 Testing video recording...")
    video_file = record_video_alert()
    if video_file:
        logger.info(f"✅ Test successful! Video saved: {video_file}")
    else:
        logger.info("❌ Test failed")
