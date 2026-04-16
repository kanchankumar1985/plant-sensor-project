"""
Intelligent analysis rules engine
Applies logic to determine reliability and usability of VLM analysis
"""

from typing import Dict, Any, Optional


def check_reliability(
    vlm_analysis: Dict[str, Any],
    yolo_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Check reliability of VLM analysis based on conditions
    
    Args:
        vlm_analysis: VLM analysis results
        yolo_metadata: YOLO detection metadata
        
    Returns:
        Dictionary with reliability assessment:
        {
            "reliable": bool,
            "confidence": "high" | "medium" | "low",
            "reasons": [list of reasons],
            "warnings": [list of warnings]
        }
    """
    # Handle None or failed VLM analysis
    if vlm_analysis is None:
        return {
            "reliable": False,
            "confidence": "none",
            "reasons": ["VLM analysis failed or timed out"],
            "warnings": ["No VLM data available"]
        }
    
    reliability = {
        "reliable": True,
        "confidence": "high",
        "reasons": [],
        "warnings": []
    }
    
    # Rule 1: Check image quality
    image_quality = vlm_analysis.get("image_quality", "unknown")
    if image_quality in ["poor", "dark", "blurry"]:
        reliability["reliable"] = False
        reliability["confidence"] = "low"
        reliability["reasons"].append(f"Poor image quality: {image_quality}")
    
    # Rule 2: Check person occlusion
    person_present = vlm_analysis.get("person_present", False)
    plant_occluded = vlm_analysis.get("plant_occluded", False)
    
    if person_present and plant_occluded:
        reliability["reliable"] = False
        reliability["confidence"] = "low"
        reliability["reasons"].append("Plant fully occluded by person")
    
    # Rule 3: Cross-check with YOLO
    if yolo_metadata:
        yolo_person_detected = yolo_metadata.get("person_detected", False)
        vlm_person_present = vlm_analysis.get("person_present", False)
        
        if yolo_person_detected != vlm_person_present:
            reliability["warnings"].append(
                f"YOLO and VLM disagree on person presence "
                f"(YOLO: {yolo_person_detected}, VLM: {vlm_person_present})"
            )
            reliability["confidence"] = "medium"
    
    # Rule 4: Check plant visibility
    plant_visible = vlm_analysis.get("plant_visible", True)
    if not plant_visible:
        reliability["warnings"].append("Plant not visible in frame")
        reliability["confidence"] = "medium"
    
    # Rule 5: Check if analysis is unknown
    plant_health = vlm_analysis.get("plant_health_guess", "unknown")
    if plant_health == "unknown" and plant_visible and not plant_occluded:
        reliability["warnings"].append("VLM could not determine plant health")
        reliability["confidence"] = "medium"
    
    return reliability


def apply_analysis_rules(
    vlm_result: Dict[str, Any],
    yolo_metadata: Optional[Dict[str, Any]] = None,
    sensor_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Apply intelligent rules to VLM analysis
    
    Args:
        vlm_result: Full VLM analysis result
        yolo_metadata: YOLO detection metadata
        sensor_data: Sensor data (temperature, humidity, etc.)
        
    Returns:
        Enhanced analysis with rules applied:
        {
            "vlm_analysis": dict,
            "reliability": dict,
            "recommendations": [list],
            "should_analyze_plant_health": bool,
            "analysis_priority": "high" | "medium" | "low"
        }
    """
    analysis = vlm_result.get("analysis") or {}
    enhanced = {
        "vlm_analysis": analysis,
        "reliability": {},
        "recommendations": [],
        "should_analyze_plant_health": False,
        "analysis_priority": "medium"
    }
    
    # Check reliability
    enhanced["reliability"] = check_reliability(analysis, yolo_metadata)
    
    # Rule: Should we analyze plant health?
    person_present = analysis.get("person_present", False)
    plant_visible = analysis.get("plant_visible", True)
    plant_occluded = analysis.get("plant_occluded", False)
    image_quality = analysis.get("image_quality", "unknown")
    
    if not person_present and plant_visible and not plant_occluded and image_quality == "good":
        enhanced["should_analyze_plant_health"] = True
        enhanced["analysis_priority"] = "high"
        enhanced["recommendations"].append("Good conditions for detailed plant health analysis")
    elif person_present and not plant_occluded:
        enhanced["should_analyze_plant_health"] = True
        enhanced["analysis_priority"] = "medium"
        enhanced["recommendations"].append("Person present but plant visible - analyze with caution")
    else:
        enhanced["should_analyze_plant_health"] = False
        enhanced["analysis_priority"] = "low"
        enhanced["recommendations"].append("Skip plant health analysis - conditions not suitable")
    
    # Rule: Temperature-based recommendations
    if sensor_data:
        temp = sensor_data.get("temperature_c", 0)
        humidity = sensor_data.get("humidity_pct", 0)
        
        if temp >= 25.0:
            enhanced["recommendations"].append(f"High temperature alert: {temp}°C")
            enhanced["analysis_priority"] = "high"
        
        if humidity < 30:
            enhanced["recommendations"].append(f"Low humidity: {humidity}% - plant may need water")
        elif humidity > 70:
            enhanced["recommendations"].append(f"High humidity: {humidity}% - check for overwatering")
    
    # Rule: Plant health warnings
    yellowing = analysis.get("yellowing_visible", False)
    drooping = analysis.get("drooping_visible", False)
    wilting = analysis.get("wilting_visible", False)
    
    if yellowing:
        enhanced["recommendations"].append("⚠️ Yellowing detected - check watering and light")
        enhanced["analysis_priority"] = "high"
    
    if drooping:
        enhanced["recommendations"].append("⚠️ Drooping detected - may need water")
        enhanced["analysis_priority"] = "high"
    
    if wilting:
        enhanced["recommendations"].append("🚨 Wilting detected - urgent attention needed")
        enhanced["analysis_priority"] = "high"
    
    return enhanced


def should_skip_analysis(
    yolo_metadata: Optional[Dict[str, Any]] = None,
    previous_analysis: Optional[Dict[str, Any]] = None,
    time_since_last: Optional[int] = None
) -> Dict[str, Any]:
    """
    Determine if VLM analysis should be skipped
    
    Args:
        yolo_metadata: YOLO detection results
        previous_analysis: Previous VLM analysis
        time_since_last: Seconds since last analysis
        
    Returns:
        Dictionary with skip decision:
        {
            "should_skip": bool,
            "reason": str,
            "suggestion": str
        }
    """
    decision = {
        "should_skip": False,
        "reason": None,
        "suggestion": None
    }
    
    # Rule: Skip if person fully occludes plant
    if yolo_metadata:
        person_count = yolo_metadata.get("person_count", 0)
        
        # If multiple people detected, likely too crowded
        if person_count >= 3:
            decision["should_skip"] = True
            decision["reason"] = f"Too many people in frame ({person_count})"
            decision["suggestion"] = "Wait for clearer view"
            return decision
    
    # Rule: Skip if analyzed very recently (< 30 seconds)
    if time_since_last is not None and time_since_last < 30:
        decision["should_skip"] = True
        decision["reason"] = f"Analyzed {time_since_last}s ago"
        decision["suggestion"] = "Use cached analysis"
        return decision
    
    # Rule: Don't skip if significant time has passed
    if time_since_last is not None and time_since_last > 180:  # 3 minutes
        decision["should_skip"] = False
        decision["suggestion"] = "Re-analyze - significant time elapsed"
        return decision
    
    return decision


def get_analysis_summary(enhanced_analysis: Dict[str, Any]) -> str:
    """
    Generate human-readable summary of analysis
    
    Args:
        enhanced_analysis: Enhanced analysis with rules applied
        
    Returns:
        Summary string
    """
    analysis = enhanced_analysis.get("vlm_analysis", {})
    reliability = enhanced_analysis.get("reliability", {})
    recommendations = enhanced_analysis.get("recommendations", [])
    
    # Start with VLM summary
    summary = analysis.get("summary", "No summary available")
    
    # Add reliability note
    confidence = reliability.get("confidence", "unknown")
    if confidence == "low":
        summary += f" [Low confidence analysis]"
    elif confidence == "medium":
        summary += f" [Medium confidence]"
    
    # Add warnings
    warnings = reliability.get("warnings", [])
    if warnings:
        summary += f" Warnings: {'; '.join(warnings[:2])}"
    
    # Add top recommendation
    if recommendations:
        summary += f" → {recommendations[0]}"
    
    return summary
