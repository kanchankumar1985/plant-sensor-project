"""
Video frame sampler - Extract representative frames from video clips
"""

import os
import cv2
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

# Frame extraction configuration
FRAMES_DIR = Path(os.getenv('FRAMES_DIR', str(Path(__file__).parent.parent / "frames")))
FRAMES_DIR.mkdir(parents=True, exist_ok=True)


def sample_video_frames(
    video_path: str,
    num_frames: int = 5,
    method: str = "uniform"
) -> List[str]:
    """
    Extract frames from video at uniform intervals
    
    Args:
        video_path: Path to video file
        num_frames: Number of frames to extract
        method: Sampling method ("uniform", "keyframes", "adaptive")
        
    Returns:
        List of paths to extracted frame images
    """
    try:
        video_path = Path(video_path)
        
        if not video_path.exists():
            print(f"❌ Video file not found: {video_path}")
            return []
        
        # Open video
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            print(f"❌ Cannot open video: {video_path}")
            return []
        
        # Get video properties
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps if fps > 0 else 0
        
        print(f"📹 Video: {total_frames} frames, {fps:.1f} FPS, {duration:.1f}s")
        
        if total_frames == 0:
            print(f"❌ Video has no frames")
            cap.release()
            return []
        
        # Calculate frame indices to sample
        if method == "uniform":
            # Uniformly spaced frames
            if num_frames >= total_frames:
                frame_indices = list(range(total_frames))
            else:
                step = total_frames / num_frames
                frame_indices = [int(i * step) for i in range(num_frames)]
        else:
            # Default to uniform for now
            step = total_frames / num_frames
            frame_indices = [int(i * step) for i in range(num_frames)]
        
        # Extract frames
        frame_paths = []
        base_name = video_path.stem
        
        for idx, frame_num in enumerate(frame_indices):
            # Seek to frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            
            if not ret:
                print(f"⚠️  Failed to read frame {frame_num}")
                continue
            
            # Save frame
            timestamp_ms = int(cap.get(cv2.CAP_PROP_POS_MSEC))
            frame_filename = f"{base_name}_frame_{idx:02d}_t{timestamp_ms}ms.jpg"
            frame_path = FRAMES_DIR / frame_filename
            
            cv2.imwrite(str(frame_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            frame_paths.append(str(frame_path))
            
            print(f"   ✓ Extracted frame {idx + 1}/{num_frames} at {timestamp_ms}ms")
        
        cap.release()
        
        print(f"✅ Extracted {len(frame_paths)} frames from video")
        return frame_paths
        
    except Exception as e:
        print(f"❌ Frame extraction failed: {e}")
        return []


def extract_keyframes(video_path: str, threshold: float = 30.0) -> List[str]:
    """
    Extract keyframes based on scene changes
    
    Args:
        video_path: Path to video file
        threshold: Scene change threshold (higher = fewer keyframes)
        
    Returns:
        List of paths to keyframe images
    """
    try:
        video_path = Path(video_path)
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            return []
        
        keyframe_paths = []
        base_name = video_path.stem
        prev_frame = None
        frame_count = 0
        keyframe_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Convert to grayscale for comparison
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Compare with previous frame
            if prev_frame is not None:
                # Calculate frame difference
                diff = cv2.absdiff(prev_frame, gray)
                mean_diff = diff.mean()
                
                # If difference exceeds threshold, save as keyframe
                if mean_diff > threshold:
                    frame_filename = f"{base_name}_keyframe_{keyframe_count:02d}.jpg"
                    frame_path = FRAMES_DIR / frame_filename
                    cv2.imwrite(str(frame_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    keyframe_paths.append(str(frame_path))
                    keyframe_count += 1
                    print(f"   ✓ Keyframe {keyframe_count} at frame {frame_count} (diff: {mean_diff:.1f})")
            
            prev_frame = gray
        
        cap.release()
        
        print(f"✅ Extracted {len(keyframe_paths)} keyframes from {frame_count} frames")
        return keyframe_paths
        
    except Exception as e:
        print(f"❌ Keyframe extraction failed: {e}")
        return []


def cleanup_frames(video_path: str):
    """
    Clean up extracted frames for a specific video
    
    Args:
        video_path: Path to video file
    """
    try:
        video_path = Path(video_path)
        base_name = video_path.stem
        
        # Find and delete all frames for this video
        deleted_count = 0
        for frame_file in FRAMES_DIR.glob(f"{base_name}_*.jpg"):
            frame_file.unlink()
            deleted_count += 1
        
        if deleted_count > 0:
            print(f"🗑️  Cleaned up {deleted_count} frames for {base_name}")
        
    except Exception as e:
        print(f"⚠️  Frame cleanup failed: {e}")


def get_frame_at_timestamp(video_path: str, timestamp_ms: int) -> Optional[str]:
    """
    Extract a single frame at a specific timestamp
    
    Args:
        video_path: Path to video file
        timestamp_ms: Timestamp in milliseconds
        
    Returns:
        Path to extracted frame or None
    """
    try:
        video_path = Path(video_path)
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            return None
        
        # Seek to timestamp
        cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_ms)
        ret, frame = cap.read()
        
        if not ret:
            cap.release()
            return None
        
        # Save frame
        base_name = video_path.stem
        frame_filename = f"{base_name}_t{timestamp_ms}ms.jpg"
        frame_path = FRAMES_DIR / frame_filename
        
        cv2.imwrite(str(frame_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        cap.release()
        
        return str(frame_path)
        
    except Exception as e:
        print(f"❌ Frame extraction at timestamp failed: {e}")
        return None
