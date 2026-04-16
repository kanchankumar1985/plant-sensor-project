# Person Detailed Analysis Feature

## Overview
New VLM prompt template to analyze people in images with detailed clothing and text detection.

## What It Does
Detects and analyzes:
- ✅ **Person presence and position**
- ✅ **Clothing details** (shirt type, color, pants)
- ✅ **Text on clothing** (e.g., "beach", "surf", logos)
- ✅ **Accessories** (glasses, hats, jewelry)
- ✅ **Actions and gestures**
- ✅ **Distance from plant**

## New Prompt Template

### `PERSON_DETAILED_PROMPT`
Located in: `vlm/prompt_templates.py`

**Purpose:** Analyze person appearance and read text on clothing

**Output Format:**
```json
{
  "person_detected": true,
  "person_count": 1,
  "position": "center",
  "clothing": {
    "shirt_type": "t-shirt",
    "shirt_color": "white",
    "shirt_has_text": true,
    "shirt_text": "beach",
    "shirt_has_logo": false,
    "shirt_logo_description": "none",
    "pants_type": "jeans",
    "pants_color": "blue"
  },
  "accessories": ["glasses", "watch"],
  "actions": ["standing", "looking at plant"],
  "distance_from_plant": "close",
  "facing_camera": true,
  "confidence": "high",
  "summary": "Person wearing white t-shirt with 'beach' text..."
}
```

## Usage

### Option 1: Test Script (Recommended)
```bash
cd /Users/kanchan/Plant\ Sensor\ Project/plant-monitor/backend
source /Users/kanchan/Plant\ Sensor\ Project/.venv/bin/activate

# Analyze a specific image
python test_person_analysis.py /Volumes/SD-128GB/PlantMonitor/images/plant_20260410_220257.jpg
```

**Output:**
```
🔍 Analyzing person in image: plant_20260410_220257.jpg

✅ Analysis complete!

============================================================
PERSON DETECTION RESULTS
============================================================

👤 Person Detected: True
👥 Person Count: 1
📍 Position: center
📏 Distance from Plant: close
👁️  Facing Camera: True

============================================================
CLOTHING DETAILS
============================================================

👕 Shirt Type: t-shirt
🎨 Shirt Color: white
📝 Has Text: True
✨ SHIRT TEXT: 'beach' ✨
🏷️  Has Logo: False

👖 Pants Type: jeans
🎨 Pants Color: blue

============================================================
SUMMARY
============================================================

Person wearing white t-shirt with text "beach" standing close to the plant...

🎯 Confidence: high
```

### Option 2: Python Code
```python
from vlm.vlm_analyzer import analyze_image
from vlm.prompt_templates import get_person_details_prompt

# Analyze image with person details
result = analyze_image(
    image_path="/path/to/image.jpg",
    analysis_type="custom",
    custom_prompt=get_person_details_prompt()
)

if result["success"]:
    analysis = result["analysis"]
    
    # Check for text on shirt
    clothing = analysis.get("clothing", {})
    if clothing.get("shirt_has_text"):
        shirt_text = clothing.get("shirt_text")
        print(f"Shirt text detected: {shirt_text}")
        
        # Check for specific text
        if "beach" in shirt_text.lower():
            print("✅ Person is wearing 'beach' shirt!")
```

### Option 3: Integration with Capture Pipeline
```python
from vlm.vlm_analyzer import analyze_image
from vlm.prompt_templates import get_person_details_prompt

# In capture_with_vlm.py or similar
def analyze_person_in_snapshot(image_path):
    """Analyze person details when detected"""
    
    # Run person analysis
    person_result = analyze_image(
        image_path=image_path,
        analysis_type="custom",
        custom_prompt=get_person_details_prompt()
    )
    
    if person_result["success"]:
        analysis = person_result["analysis"]
        
        # Extract clothing text
        clothing = analysis.get("clothing", {})
        shirt_text = clothing.get("shirt_text", "none")
        
        # Log or store results
        print(f"Person analysis: {shirt_text}")
        
        return analysis
    
    return None
```

## Use Cases

### 1. **Clothing Text Detection**
Detect specific text on shirts:
- "beach" - Beach-themed clothing
- "surf" - Surfing apparel
- Brand names or logos
- Event names or slogans

### 2. **Person Identification**
Identify people by clothing:
- Regular visitor wearing specific shirt
- Staff vs. visitor based on uniform
- Track who interacts with plant

### 3. **Activity Logging**
Log person activities:
- Who watered the plant (based on clothing)
- Who touched the plant
- Visitor patterns

### 4. **Security & Monitoring**
Enhanced monitoring:
- Detect unauthorized access
- Track plant care activities
- Identify who moved the plant

## API Function

### `get_person_details_prompt()`
Returns the person analysis prompt template.

**Location:** `vlm/prompt_templates.py`

**Usage:**
```python
from vlm.prompt_templates import get_person_details_prompt

prompt = get_person_details_prompt()
# Use with VLM analyzer
```

## Example Scenarios

### Scenario 1: Detect "beach" shirt
```python
result = analyze_image(
    image_path="snapshot.jpg",
    analysis_type="custom",
    custom_prompt=get_person_details_prompt()
)

clothing = result["analysis"]["clothing"]
if clothing["shirt_has_text"] and "beach" in clothing["shirt_text"].lower():
    print("✅ Beach shirt detected!")
```

### Scenario 2: Track plant care by clothing
```python
# Store person analysis with snapshot
snapshot_data = {
    "timestamp": datetime.now(),
    "person_clothing": clothing["shirt_text"],
    "person_action": analysis["actions"],
    "plant_touched": analysis["distance_from_plant"] == "very_close"
}

# Later: Query who watered the plant
# SELECT * FROM snapshots WHERE person_clothing LIKE '%gardener%'
```

### Scenario 3: Alert on specific text
```python
# Alert if specific text detected
forbidden_texts = ["private", "restricted", "staff only"]

shirt_text = clothing["shirt_text"].lower()
for forbidden in forbidden_texts:
    if forbidden in shirt_text:
        send_alert(f"Restricted area access: {shirt_text}")
```

## Performance Notes

### VLM Model Requirements
- **Model:** llava:7b (or similar vision-language model)
- **Timeout:** 300 seconds (configurable via OLLAMA_TIMEOUT)
- **Memory:** ~5GB RAM for model
- **Processing time:** 30-120 seconds per image

### Text Detection Accuracy
- ✅ **High accuracy:** Large, clear text (>2cm height)
- ⚠️ **Medium accuracy:** Small text, cursive fonts
- ❌ **Low accuracy:** Blurry images, poor lighting, text at angles

### Optimization Tips
1. **Good lighting** - Ensure well-lit images
2. **Clear view** - Person facing camera
3. **Close distance** - Person within 2-3 meters
4. **High resolution** - 640x480 minimum

## Troubleshooting

### Text not detected
- Check image quality (lighting, focus)
- Verify text is visible and readable
- Try with larger, clearer text
- Increase OLLAMA_TIMEOUT if analysis cuts off

### Wrong text detected
- VLM may misread similar letters (0/O, 1/I)
- Partial occlusion can cause errors
- Verify with multiple images

### Analysis too slow
- Reduce image size before analysis
- Use faster model (smaller parameter count)
- Increase timeout in .env

## Integration with Database

### Store Person Analysis
```sql
-- Add columns to plant_snapshots table
ALTER TABLE plant_snapshots ADD COLUMN person_clothing_text TEXT;
ALTER TABLE plant_snapshots ADD COLUMN person_clothing_details JSONB;

-- Store analysis results
INSERT INTO plant_snapshots (
    time, image_path, person_detected, 
    person_clothing_text, person_clothing_details
) VALUES (
    NOW(), 'snapshot.jpg', true,
    'beach', 
    '{"shirt_type": "t-shirt", "shirt_color": "white", ...}'::jsonb
);
```

### Query Examples
```sql
-- Find all snapshots with "beach" text
SELECT * FROM plant_snapshots 
WHERE person_clothing_text ILIKE '%beach%';

-- Find people wearing specific colors
SELECT * FROM plant_snapshots 
WHERE person_clothing_details->>'shirt_color' = 'blue';

-- Track who touched the plant
SELECT person_clothing_text, COUNT(*) 
FROM plant_snapshots 
WHERE person_clothing_details->>'distance_from_plant' = 'very_close'
GROUP BY person_clothing_text;
```

## Next Steps

1. **Test with real images** - Run test_person_analysis.py
2. **Integrate with pipeline** - Add to capture_with_vlm.py
3. **Store in database** - Add columns and save results
4. **Create alerts** - Trigger on specific text detection
5. **Build UI** - Display person analysis in frontend

## Files Modified

- ✅ `vlm/prompt_templates.py` - Added PERSON_DETAILED_PROMPT
- ✅ `test_person_analysis.py` - Test script created
- ✅ `PERSON_ANALYSIS_README.md` - Documentation created

## Related Documentation

- `LOGGING_README.md` - Logging system
- `OLLAMA_TIMEOUT_FIX.md` - Timeout configuration
- `vlm/README.md` - VLM system overview
