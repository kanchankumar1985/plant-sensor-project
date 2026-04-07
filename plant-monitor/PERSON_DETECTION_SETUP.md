# 🔍 Person Detection Integration Setup

## Overview
This system adds local YOLO-based person detection to your plant monitoring pipeline. Before analyzing plants, it detects people in the frame and can skip plant analysis if someone is present.

## Architecture
```
Webcam → Capture Image → YOLO Person Detection → JSON + Boxed Image → TimescaleDB → FastAPI → React
```

## 🚀 Installation

### 1. Install Python Dependencies
```bash
cd plant-monitor/backend
source ../../.venv/bin/activate
pip install ultralytics
```

This will install:
- YOLOv8 (ultralytics package)
- PyTorch (automatically installed as dependency)
- Additional ML dependencies

### 2. Run Database Migration
```bash
psql -h localhost -p 5433 -U plantuser -d plantdb -f migrations/002_add_person_detection.sql
```

Or manually:
```bash
cd plant-monitor/backend
source ../../.venv/bin/activate
python -c "
import psycopg2
conn = psycopg2.connect(host='localhost', port='5433', database='plantdb', user='plantuser', password='plantpass')
with open('migrations/002_add_person_detection.sql', 'r') as f:
    conn.cursor().execute(f.read())
conn.commit()
print('✅ Migration complete')
"
```

### 3. Download YOLO Model (First Run)
The first time you run detection, YOLOv8n will be automatically downloaded (~6MB).

## 📁 Files Created

### Backend
- `detect_person.py` - YOLO person detection logic
- `capture_with_detection.py` - Integrated capture pipeline
- `migrations/002_add_person_detection.sql` - Database schema updates

### Frontend
- `PersonDetection.jsx` - React component for displaying detection results

## 🔧 Usage

### Manual Capture with Detection
```bash
cd plant-monitor/backend
source ../../.venv/bin/activate
python capture_with_detection.py
```

### Test Detection on Existing Image
```bash
python detect_person.py images/plant_20260407_020000.jpg
```

### Integrate with Temperature-Triggered Capture
Update `serial_reader.py` to use the new detection pipeline:

```python
# Replace this import
from capture_snapshot import capture_snapshot_with_data_and_conn

# With this
from capture_with_detection import capture_and_detect

# Then in trigger_snapshot_if_needed():
success = capture_and_detect(sensor_data, db_conn, sensor_timestamp)
```

## 📊 Database Schema

New columns added to `plant_snapshots`:
- `id` - SERIAL PRIMARY KEY
- `person_detected` - BOOLEAN (true if person found)
- `person_count` - INTEGER (number of people detected)
- `detection_metadata` - JSONB (full detection data)
- `boxed_image_path` - TEXT (filename of image with bounding boxes)

## 🌐 API Endpoints

### Get Latest Detection
```bash
curl http://localhost:8000/api/snapshots/latest-detection
```

Response:
```json
{
  "time": "2026-04-07T02:30:00Z",
  "image_path": "plant_20260407_023000.jpg",
  "boxed_image_path": "plant_20260407_023000_boxed.jpg",
  "image_url": "http://localhost:8000/images/plant_20260407_023000.jpg",
  "boxed_image_url": "http://localhost:8000/images/plant_20260407_023000_boxed.jpg",
  "person_detected": true,
  "person_count": 1,
  "detection_metadata": {
    "person_detected": true,
    "person_count": 1,
    "detections": [
      {
        "class_name": "person",
        "confidence": 0.89,
        "bbox_xyxy": [120, 50, 380, 450]
      }
    ]
  },
  "temperature_c": 23.5,
  "humidity_pct": 57.2,
  "led_state": false,
  "vlm_result": "Skipped: Person detected in frame"
}
```

## 🎨 React Integration

Add to your `App.jsx`:
```jsx
import PersonDetection from './PersonDetection';

function App() {
  return (
    <div>
      {/* Existing components */}
      <PersonDetection />
    </div>
  );
}
```

## 🔮 Future VLM Integration Hook

The system is designed to skip plant analysis when people are detected:

```python
# In capture_with_detection.py
if detection_result['metadata']['person_detected']:
    print("⚠️  Person detected - skipping plant VLM analysis")
    vlm_result = "Skipped: Person detected in frame"
else:
    print("✓ No person detected - ready for plant VLM analysis")
    vlm_result = run_vlm(image_path)  # Your future VLM call here
```

To add real plant analysis:
1. Replace `run_vlm()` placeholder with actual VLM API call
2. The logic already checks `person_detected` before running
3. VLM only runs when no person is in frame

## 🧪 Testing

### Test Person Detection
```bash
# Capture an image with you in frame
cd plant-monitor/backend
source ../../.venv/bin/activate
python capture_with_detection.py
```

Expected output:
```
🌱 Starting capture with person detection...
📸 Image captured: plant_20260407_023000.jpg

🔍 Running person detection on: plant_20260407_023000.jpg
👤 Person detected: True
👥 Person count: 1
✓ Detection metadata saved: plant_20260407_023000_detection.json
✓ Boxed image saved: plant_20260407_023000_boxed.jpg
⚠️  Person detected - skipping plant VLM analysis
✓ Snapshot with detection saved to database

✅ Capture with detection complete!
   📸 Image: plant_20260407_023000.jpg
   🖼️  Boxed: plant_20260407_023000_boxed.jpg
   👤 Person detected: True
   👥 Person count: 1
```

### Test API Endpoint
```bash
curl http://localhost:8000/api/snapshots/latest-detection | jq
```

### Test React Component
1. Start FastAPI: `uvicorn app:app --reload --port 8000`
2. Start React: `npm run dev`
3. Navigate to `http://localhost:5174/`
4. Scroll to Person Detection section

## 📈 Performance

- **YOLOv8n** (nano): ~6MB model, fast inference on CPU
- **Inference time**: ~200-500ms on laptop CPU
- **Memory usage**: ~200MB additional RAM
- **Disk usage**: ~6MB for model + images + JSON files

## 🔧 Configuration

### Change YOLO Model
Edit `detect_person.py`:
```python
# Lightweight (default)
MODEL = YOLO('yolov8n.pt')  # Nano - fastest

# More accurate (slower)
MODEL = YOLO('yolov8s.pt')  # Small
MODEL = YOLO('yolov8m.pt')  # Medium
MODEL = YOLO('yolov8l.pt')  # Large
```

### Adjust Confidence Threshold
Add confidence filtering in `detect_people()`:
```python
if class_id == 0 and confidence > 0.5:  # Only detections > 50%
    person_detections.append(...)
```

## 🐛 Troubleshooting

### YOLO Model Download Fails
```bash
# Manually download
cd ~/.cache/ultralytics
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
```

### Database Migration Errors
```bash
# Check if columns exist
psql -h localhost -p 5433 -U plantuser -d plantdb -c "\d plant_snapshots"

# Drop and recreate if needed
psql -h localhost -p 5433 -U plantuser -d plantdb -c "
ALTER TABLE plant_snapshots DROP COLUMN IF EXISTS person_detected;
ALTER TABLE plant_snapshots DROP COLUMN IF EXISTS person_count;
ALTER TABLE plant_snapshots DROP COLUMN IF EXISTS detection_metadata;
ALTER TABLE plant_snapshots DROP COLUMN IF EXISTS boxed_image_path;
"
# Then re-run migration
```

### Images Not Displaying
- Verify FastAPI is serving `/images` directory
- Check file permissions on `backend/images/`
- Ensure boxed images are being created

## 📝 File Outputs

For each capture, the system creates:
1. **Original image**: `plant_YYYYMMDD_HHMMSS.jpg`
2. **Boxed image**: `plant_YYYYMMDD_HHMMSS_boxed.jpg` (with green rectangles)
3. **JSON metadata**: `plant_YYYYMMDD_HHMMSS_detection.json`
4. **Database record**: In `plant_snapshots` table

## 🎯 Complete System Flow

```
1. Temperature ≥ 25°C triggers capture
   ↓
2. Webcam captures image
   ↓
3. YOLO detects people
   ↓
4. If person detected:
   - Draw bounding boxes
   - Skip plant VLM analysis
   - Mark as "Skipped: Person detected"
   ↓
5. Save to database with detection metadata
   ↓
6. FastAPI serves detection data
   ↓
7. React displays boxed image + metadata
```

## 🚀 Next Steps

1. Install dependencies: `pip install ultralytics`
2. Run migration: `psql ... -f migrations/002_add_person_detection.sql`
3. Test capture: `python capture_with_detection.py`
4. Update serial reader to use new pipeline
5. Add PersonDetection component to React app
6. Test end-to-end with temperature trigger

Your plant monitoring system now has intelligent person detection! 🌱👤
