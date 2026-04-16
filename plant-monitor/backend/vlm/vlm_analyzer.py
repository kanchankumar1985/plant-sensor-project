"""
VLM Analyzer - Core interface for vision-language model analysis
Provides high-level functions for image and video analysis
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import time
import os
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

from .ollama_client import get_ollama_client
from .prompt_templates import (
    get_image_analysis_prompt,
    get_video_analysis_prompt,
    get_plant_health_prompt,
    get_person_details_json_prompt,
    get_person_details_prompt,
)
from .video_frame_sampler import sample_video_frames

# Resize configuration
MAX_VLM_IMAGE_WIDTH = int(os.getenv('VLM_MAX_IMAGE_WIDTH', '640'))
MAX_VLM_IMAGE_HEIGHT = int(os.getenv('VLM_MAX_IMAGE_HEIGHT', '360'))
QUALITY = int(os.getenv('VLM_IMAGE_QUALITY', '75'))


def parse_json_from_response(response_text: str) -> Optional[Dict[str, Any]]:
    """
    Extract and parse JSON from VLM response
    Handles cases where model includes extra text around JSON
    
    Args:
        response_text: Raw response from VLM
        
    Returns:
        Parsed JSON dict or None if parsing fails
    """
    try:
        # Try direct JSON parse first
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON block in response
    # Look for content between { and }
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    # Try to find JSON in code block
    code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1))
        except json.JSONDecodeError:
            pass
    
    return None


def _prepare_image_for_analysis(image_path: str) -> str:
    """
    Create a resized/compressed copy of the input image for faster VLM analysis.
    Returns the path to the resized image. If resizing is not needed, returns the original path.
    """
    try:
        p = Path(image_path)
        out_dir = p.parent / "analysis_tmp"
        out_dir.mkdir(exist_ok=True)
        quality = QUALITY
        with Image.open(image_path) as im:
            im = im.convert("RGB")
            w, h = im.size
            if w <= MAX_VLM_IMAGE_WIDTH and h <= MAX_VLM_IMAGE_HEIGHT:
                # Still save a compressed copy to control quality/format
                out_path = out_dir / f"{p.stem}_analysis.jpg"
                im.save(out_path, format="JPEG", quality=quality, optimize=True)
                return str(out_path)
            scale = min(MAX_VLM_IMAGE_WIDTH / float(w), MAX_VLM_IMAGE_HEIGHT / float(h))
            new_w = int(w * scale)
            new_h = int(h * scale)
            im_resized = im.resize((new_w, new_h))
            out_path = out_dir / f"{p.stem}_analysis.jpg"
            im_resized.save(out_path, format="JPEG", quality=quality, optimize=True)
            print(f"🗜️ Resized image for VLM: {w}x{h} -> {new_w}x{new_h} ({out_path.name}) target={MAX_VLM_IMAGE_WIDTH}x{MAX_VLM_IMAGE_HEIGHT}")
            return str(out_path)
    except Exception:
        # On any failure, fall back to original image
        return image_path


def analyze_image_with_vlm(
    image_path: str,
    analysis_type: str = "standard",
    yolo_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Analyze an image using local VLM
    
    Args:
        image_path: Path to image file
        analysis_type: Type of analysis ("standard", "plant_health", "custom")
        yolo_metadata: Optional YOLO detection metadata to inform analysis
        
    Returns:
        Dictionary with analysis results:
        {
            "success": bool,
            "analysis": dict,  # Structured JSON from VLM
            "raw_response": str,  # Raw VLM output
            "error": str,  # Error message if failed
            "timestamp": str,
            "model": str,
            "analysis_type": str
        }
    """
    result = {
        "success": False,
        "analysis": None,
        "raw_response": None,
        "error": None,
        "timestamp": datetime.utcnow().isoformat(),
        "model": None,
        "analysis_type": analysis_type,
        "prompt_name": None,
        "prompt_preview": None
    }
    
    try:
        # Get Ollama client
        client = get_ollama_client()
        result["model"] = client.model
        
        # Check if Ollama is healthy
        if not client.check_health():
            result["error"] = "Ollama is not running or model not available"
            return result
        
        # Select prompt based on analysis type
        if analysis_type == "plant_health":
            prompt = get_plant_health_prompt()
            result["prompt_name"] = "plant_health"
        elif analysis_type in ("person", "person_detailed"):
            prompt = get_person_details_json_prompt()
            result["prompt_name"] = "person_detailed"
        else:
            prompt = get_image_analysis_prompt()
            result["prompt_name"] = "standard_image"
        
        # Add YOLO context if available
        if yolo_metadata and yolo_metadata.get('person_detected'):
            person_count = yolo_metadata.get('person_count', 0)
            prompt += f"\n\nNote: YOLO detection found {person_count} person(s) in this image."
        result["prompt_preview"] = (prompt[:200] + "...") if len(prompt) > 200 else prompt
        print(f"[VLM][PROMPT] analysis_type={analysis_type} name={result['prompt_name']}")
        print(f"[VLM][PROMPT] preview: {result['prompt_preview']}")
        
        # Generate response
        print(f"🤖 Analyzing image with {client.model}...")
        start_ts = datetime.utcnow()
        t0 = time.perf_counter()
        analysis_image = _prepare_image_for_analysis(image_path)
        response = client.generate(prompt, analysis_image)
        elapsed = time.perf_counter() - t0
        print(f"⏱️ VLM image analysis took {elapsed:.2f}s (started {start_ts.isoformat()} UTC)")
        
        # Extract response text
        raw_response = response.get('response', '')
        result["raw_response"] = raw_response
        raw_preview = raw_response if len(raw_response) <= 600 else (raw_response[:600] + "...")
        print(f"[VLM][RAW] {raw_preview}")
        
        # Parse JSON from response
        analysis_json = parse_json_from_response(raw_response)
        
        if analysis_json:
            result["success"] = True
            result["analysis"] = analysis_json
            try:
                parsed_preview = json.dumps(analysis_json)[:800]
            except Exception:
                parsed_preview = str(analysis_json)[:800]
            print(f"[VLM][JSON] {parsed_preview}")
            print(f"✅ Image analysis complete")
        else:
            if analysis_type in ("person", "person_detailed") and prompt == get_person_details_json_prompt():
                print("[VLM][FALLBACK] compact prompt failed – retrying with full prompt")
                prompt = get_person_details_prompt()
                result["prompt_preview"] = (prompt[:200] + "...") if len(prompt) > 200 else prompt
                response = client.generate(prompt, analysis_image)
                raw_response = response.get('response', '')
                if not raw_response:
                    raw_response = response.get('thinking', '')
                result["raw_response"] = raw_response
                print(f"[VLM][RESPONSE_DUMP] {response}")
                raw_preview = raw_response if len(raw_response) <= 600 else (raw_response[:600] + "...")
                print(f"[VLM][RAW] {raw_preview}")
                analysis_json = parse_json_from_response(raw_response)
                if analysis_json:
                    result["success"] = True
                    result["analysis"] = analysis_json
                    try:
                        parsed_preview = json.dumps(analysis_json)[:800]
                    except Exception:
                        parsed_preview = str(analysis_json)[:800]
                    print(f"[VLM][JSON] {parsed_preview}")
                    print(f"✅ Image analysis complete (fallback)")
                else:
                    result["error"] = "Failed to parse JSON from VLM response (even after fallback)"
                    print(f"⚠️  Could not parse JSON after fallback")
                    print(f"   Raw response: {raw_response[:200]}...")
            else:
                result["error"] = "Failed to parse JSON from VLM response"
                print(f"⚠️  Could not parse JSON from response")
                print(f"   Raw response: {raw_response[:200]}...")
        
        return result
        
    except Exception as e:
        result["error"] = str(e)
        print(f"❌ Image analysis failed: {e}")
        return result


def analyze_video_with_vlm(
    video_path: str,
    frame_count: int = 5,
    yolo_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Analyze a video by sampling frames and using VLM
    
    Args:
        video_path: Path to video file
        frame_count: Number of frames to sample
        yolo_metadata: Optional YOLO detection metadata
        
    Returns:
        Dictionary with analysis results:
        {
            "success": bool,
            "analysis": dict,  # Structured JSON from VLM
            "raw_response": str,
            "error": str,
            "timestamp": str,
            "model": str,
            "frames_analyzed": int,
            "frame_paths": list
        }
    """
    result = {
        "success": False,
        "analysis": None,
        "raw_response": None,
        "error": None,
        "timestamp": datetime.utcnow().isoformat(),
        "model": None,
        "frames_analyzed": 0,
        "frame_paths": []
    }
    
    try:
        # Sample frames from video
        print(f"🎬 Sampling {frame_count} frames from video...")
        frame_paths = sample_video_frames(video_path, frame_count)
        
        if not frame_paths:
            result["error"] = "Failed to sample frames from video"
            return result
        
        result["frame_paths"] = frame_paths
        result["frames_analyzed"] = len(frame_paths)
        
        # Get Ollama client
        client = get_ollama_client()
        result["model"] = client.model
        
        # Check health
        if not client.check_health():
            result["error"] = "Ollama is not running or model not available"
            return result
        
        # Get prompt
        prompt = get_video_analysis_prompt(len(frame_paths))
        
        # Add YOLO context if available
        if yolo_metadata and yolo_metadata.get('person_detected'):
            person_count = yolo_metadata.get('person_count', 0)
            prompt += f"\n\nNote: YOLO detected {person_count} person(s) in the initial frame."
        
        # For now, analyze the middle frame as representative
        # TODO: Implement multi-frame analysis when Ollama supports it
        middle_frame = frame_paths[len(frame_paths) // 2]
        
        print(f"🤖 Analyzing video frames with {client.model}...")
        start_ts = datetime.utcnow()
        t0 = time.perf_counter()
        analysis_frame = _prepare_image_for_analysis(middle_frame)
        response = client.generate(prompt, analysis_frame)
        elapsed = time.perf_counter() - t0
        print(f"⏱️ VLM video analysis took {elapsed:.2f}s (started {start_ts.isoformat()} UTC)")
        
        # Extract response
        raw_response = response.get('response', '')
        result["raw_response"] = raw_response
        
        # Parse JSON
        analysis_json = parse_json_from_response(raw_response)
        
        if analysis_json:
            result["success"] = True
            result["analysis"] = analysis_json
            print(f"✅ Video analysis complete")
        else:
            result["error"] = "Failed to parse JSON from VLM response"
            print(f"⚠️  Could not parse JSON from response")
        
        return result
        
    except Exception as e:
        result["error"] = str(e)
        print(f"❌ Video analysis failed: {e}")
        return result


def get_default_analysis() -> Dict[str, Any]:
    """
    Get default analysis structure when VLM is unavailable
    
    Returns:
        Default analysis dictionary
    """
    return {
        "person_present": False,
        "person_count": 0,
        "plant_visible": True,
        "plant_occluded": False,
        "plant_health_guess": "unknown",
        "yellowing_visible": False,
        "drooping_visible": False,
        "wilting_visible": False,
        "image_quality": "unknown",
        "summary": "Analysis not available - VLM offline"
    }


def test_vlm_connection() -> bool:
    """
    Test if VLM is available and working
    
    Returns:
        True if VLM is ready, False otherwise
    """
    try:
        client = get_ollama_client()
        return client.check_health()
    except Exception as e:
        print(f"❌ VLM connection test failed: {e}")
        return False
