"""
Structured prompt templates for VLM analysis
Designed to produce predictable, parseable JSON responses
"""

IMAGE_ANALYSIS_PROMPT = """You are analyzing an image from a plant monitoring camera system.

Analyze this image and provide a structured assessment in JSON format.

Focus on:
1. Person presence and count
2. Plant visibility and occlusion
3. Plant health indicators (yellowing, drooping, wilting)
4. Image quality and usability

Respond ONLY with valid JSON in this exact format:
{
  "person_present": true or false,
  "person_count": integer (0 if no person),
  "plant_visible": true or false,
  "plant_occluded": true or false (true if person blocks plant view),
  "plant_health_guess": "healthy" or "yellowing" or "drooping" or "wilting" or "unknown",
  "yellowing_visible": true or false,
  "drooping_visible": true or false,
  "wilting_visible": true or false,
  "image_quality": "good" or "poor" or "dark" or "blurry",
  "summary": "A brief 1-2 sentence description of what you see"
}

Be precise and factual. If you cannot determine something, use "unknown" or false.
"""

VIDEO_ANALYSIS_PROMPT = """You are analyzing frames from a 5-second video clip captured by a plant monitoring system.

I will show you {frame_count} frames sampled from the video at different timestamps.

Analyze the sequence and provide a structured event summary in JSON format.

Focus on:
1. Person movement (entering, leaving, staying)
2. Plant interaction (touching, blocking, moving near)
3. Plant visibility throughout the clip
4. Any significant motion or events

Respond ONLY with valid JSON in this exact format:
{{
  "person_entered": true or false,
  "person_left": true or false,
  "person_stayed": true or false,
  "plant_touched": true or false,
  "plant_blocked": true or false,
  "plant_visible_throughout": true or false,
  "significant_motion": true or false,
  "motion_description": "brief description of motion",
  "event_type": "person_interaction" or "no_activity" or "plant_check" or "unknown",
  "summary": "A brief 2-3 sentence description of what happened in this video clip"
}}

Be precise and factual. Focus on what actually changed between frames.
"""

PLANT_HEALTH_DETAILED_PROMPT = """You are a plant health expert analyzing an image of a potted plant.

The image shows a plant in an indoor environment. Analyze the plant's health in detail.

Focus on:
1. Leaf color and condition
2. Stem posture and strength
3. Signs of stress or disease
4. Watering needs
5. Overall vitality

Respond ONLY with valid JSON in this exact format:
{
  "overall_health": "excellent" or "good" or "fair" or "poor" or "critical",
  "leaf_color": "green" or "light_green" or "yellow" or "brown" or "mixed",
  "leaf_condition": "healthy" or "drooping" or "wilting" or "crispy" or "spotted",
  "stem_posture": "upright" or "leaning" or "drooping" or "weak",
  "stress_signs": ["list", "of", "visible", "stress", "indicators"],
  "watering_assessment": "adequate" or "overwatered" or "underwatered" or "unknown",
  "disease_signs": true or false,
  "pest_signs": true or false,
  "recommendations": ["list", "of", "care", "recommendations"],
  "confidence": "high" or "medium" or "low",
  "summary": "A detailed 2-3 sentence assessment of the plant's current health status"
}

Be thorough and specific. If you cannot determine something with confidence, note it in the confidence field.
"""

PERSON_DETAILED_PROMPT = """You are analyzing an image to detect and describe a person in detail.

The image may contain a person near a plant monitoring setup. Analyze the person's appearance and clothing.

Focus on:
1. Person presence and position
2. Clothing details (shirt, pants, accessories)
3. Text or logos on clothing
4. Colors and patterns
5. Actions or gestures

Respond ONLY with valid JSON in this exact format:
{
  "person_detected": true or false,
  "person_count": integer (0 if no person),
  "position": "left" or "center" or "right" or "unknown",
  "clothing": {
    "shirt_type": "t-shirt" or "long-sleeve" or "hoodie" or "jacket" or "other" or "unknown",
    "shirt_color": "color description",
    "shirt_has_text": true or false,
    "shirt_text": "exact text visible on shirt" or "none" or "unreadable",
    "shirt_has_logo": true or false,
    "shirt_logo_description": "description of logo" or "none",
    "pants_type": "jeans" or "shorts" or "pants" or "other" or "unknown",
    "pants_color": "color description"
  },
  "accessories": ["list", "of", "visible", "accessories"],
  "actions": ["list", "of", "actions", "or", "gestures"],
  "distance_from_plant": "very_close" or "close" or "medium" or "far" or "unknown",
  "facing_camera": true or false,
  "confidence": "high" or "medium" or "low",
  "summary": "A detailed 2-3 sentence description of the person and what they are doing"
}

Be very precise about text on clothing. If you see text like "beach", "surf", "ocean", or any other words, include them exactly as they appear in the shirt_text field. If text is partially visible or unclear, describe what you can see.
"""

PERSON_DETAILED_JSON_PROMPT = """RReturn ONLY valid JSON. Do not include any text.

{
  "person_detected": true or false,
  "facing_camera": true or false
}

Rules:
- Output must be valid JSON
- Do not use markdown
- Do not add explanation
- Use lowercase true/false
- If no person is visible, return:
{
  "person_detected": false,
  "facing_camera": false
}

If the image is too dark or blank to describe confidently, respond with person_detected: false and explain the uncertainty.”
"""

def get_image_analysis_prompt() -> str:
    """Get the standard image analysis prompt"""
    return IMAGE_ANALYSIS_PROMPT

def get_video_analysis_prompt(frame_count: int = 5) -> str:
    """Get the video analysis prompt with frame count"""
    return VIDEO_ANALYSIS_PROMPT.format(frame_count=frame_count)

def get_plant_health_prompt() -> str:
    """Get the detailed plant health analysis prompt"""
    return PLANT_HEALTH_DETAILED_PROMPT

def get_person_details_prompt() -> str:
    """Get the detailed person analysis prompt"""
    return PERSON_DETAILED_PROMPT


def get_person_details_json_prompt() -> str:
    """Get the compact person analysis prompt that strictly returns JSON"""
    return PERSON_DETAILED_JSON_PROMPT

def get_custom_prompt(focus_areas: list[str]) -> str:
    """
    Generate a custom prompt based on specific focus areas
    
    Args:
        focus_areas: List of areas to focus on (e.g., ['person', 'plant_health', 'lighting'])
    
    Returns:
        Custom prompt string
    """
    base = "You are analyzing an image from a plant monitoring system.\n\n"
    
    if 'person' in focus_areas:
        base += "Focus on detecting people and their proximity to the plant.\n"
    
    if 'plant_health' in focus_areas:
        base += "Focus on plant health indicators like leaf color, drooping, and wilting.\n"
    
    if 'lighting' in focus_areas:
        base += "Focus on lighting conditions and image quality.\n"
    
    if 'occlusion' in focus_areas:
        base += "Focus on whether the plant is visible or blocked from view.\n"
    
    base += "\nProvide a structured JSON response with your observations."
    
    return base
