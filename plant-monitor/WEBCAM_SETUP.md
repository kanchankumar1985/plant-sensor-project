# 📸 Webcam Integration Setup Guide

## Overview
This system captures plant images using your laptop's webcam, links them with sensor data, and stores everything in TimescaleDB for display in the React dashboard.

## Architecture
```
Webcam → capture_snapshot.py → TimescaleDB (plant_snapshots) → FastAPI → React Dashboard
                ↓
         Fetch latest sensor data
         (temperature, humidity, LED state)
```

## Prerequisites
✅ ESP32 sensor system running
✅ TimescaleDB container running
✅ Python virtual environment activated
✅ OpenCV installed (`pip install opencv-python`)

## 🔐 macOS Camera Permissions

**IMPORTANT:** macOS requires explicit camera permission.

### Grant Camera Access:
1. Open **System Settings** → **Privacy & Security** → **Camera**
2. Enable camera access for:
   - **Terminal** (if running from terminal)
   - **Your IDE** (if running from Windsurf/VSCode)
3. Restart your terminal/IDE after granting permission

## 📁 File Structure

```
plant-monitor/backend/
├── capture_snapshot.py    # Single snapshot capture
├── capture_loop.py         # Automated 60-second loop
├── app.py                  # FastAPI with snapshot endpoints
├── images/                 # Stored webcam images
└── requirements.txt        # Updated with opencv-python
```

## 🚀 Usage

### 1. Test Single Snapshot Capture
```bash
cd plant-monitor/backend
source .venv/bin/activate
python capture_snapshot.py
```

**Expected Output:**
```
🌱 Starting plant snapshot capture...
📸 Image captured: plant_20260406_223000.jpg
✓ Snapshot saved to database: 2026-04-06 22:30:00
✅ Snapshot complete!
   📸 Image: plant_20260406_223000.jpg
   🌡️  Temp: 23.48°C
   💧 Humidity: 57.8%
   💡 LED: OFF
   🤖 VLM: Not analyzed yet
```

### 2. Run Automated Capture Loop
```bash
python capture_loop.py
```

Captures images every 60 seconds automatically.

### 3. Start FastAPI Server
```bash
uvicorn app:app --reload --port 8000
```

### 4. Test API Endpoints

**Get Latest Snapshot:**
```bash
curl http://localhost:8000/api/snapshots/latest
```

**Get Recent Snapshots:**
```bash
curl http://localhost:8000/api/snapshots/recent?limit=10
```

**View Image:**
```
http://localhost:8000/images/plant_20260406_223000.jpg
```

## 📊 Database Schema

### Table: `plant_snapshots`
```sql
CREATE TABLE plant_snapshots (
    time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    image_path TEXT NOT NULL,
    temperature_c DOUBLE PRECISION NOT NULL,
    humidity_pct DOUBLE PRECISION NOT NULL,
    led_state BOOLEAN NOT NULL,
    vlm_result TEXT
);
```

## 🎨 React Integration

### Import Component:
```jsx
import PlantSnapshot from './PlantSnapshot';
```

### Use in App:
```jsx
function App() {
  return (
    <div>
      <PlantSnapshot />
    </div>
  );
}
```

The component:
- Fetches latest snapshot every 60 seconds
- Displays plant image
- Shows temperature, humidity, LED state
- Shows AI analysis result (placeholder for now)
- Has manual refresh button

## 🤖 Future VLM Integration

The system includes a placeholder function for AI vision analysis:

```python
def run_vlm(image_path):
    """
    Placeholder for future VLM (Vision Language Model) integration
    This will be used to analyze plant health using AI
    """
    return "Not analyzed yet"
```

**To integrate AI later:**
1. Install vision model library (e.g., OpenAI Vision, Google Gemini)
2. Update `run_vlm()` function in `capture_snapshot.py`
3. Pass image to model for analysis
4. Store result in `vlm_result` column

Example future implementation:
```python
def run_vlm(image_path):
    # Load image
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    # Call vision model
    response = vision_model.analyze(
        image=image_data,
        prompt="Analyze this plant's health. Check for wilting, discoloration, or pests."
    )
    
    return response.text
```

## 🔧 Troubleshooting

### Camera Not Opening
- **Error:** `Cannot open webcam`
- **Solution:** Grant camera permissions in System Settings
- **Check:** Run `ls /dev/video*` to verify camera device

### No Sensor Data
- **Error:** `No sensor data found`
- **Solution:** Ensure `serial_reader.py` is running and ingesting data
- **Check:** Query database: `SELECT * FROM sensor_readings ORDER BY time DESC LIMIT 1;`

### Images Not Displaying
- **Error:** 404 on image URL
- **Solution:** Verify FastAPI is serving static files from `/images`
- **Check:** Visit `http://localhost:8000/images/` in browser

### Database Connection Failed
- **Error:** `Database connection failed`
- **Solution:** Ensure TimescaleDB Docker container is running
- **Check:** `docker ps | grep plant-timescaledb`

## 📝 API Endpoints Reference

### Sensor Readings (Existing)
- `GET /api/readings/latest` - Latest sensor reading
- `GET /api/readings/recent?limit=50` - Recent readings
- `GET /api/readings/range?start_time=...&end_time=...` - Time range

### Snapshots (New)
- `GET /api/snapshots/latest` - Latest plant snapshot with metadata
- `GET /api/snapshots/recent?limit=10` - Recent snapshots
- `GET /images/{filename}` - Static image file

## 🎯 Complete System Startup

```bash
# Terminal 1: Start TimescaleDB (if not running)
cd plant-monitor/backend
docker-compose up -d

# Terminal 2: Start Serial Reader
source .venv/bin/activate
python serial_reader.py

# Terminal 3: Start FastAPI
source .venv/bin/activate
uvicorn app:app --reload --port 8000

# Terminal 4: Start Snapshot Capture Loop
source .venv/bin/activate
python capture_loop.py

# Terminal 5: Start React Dashboard
cd ../frontend
npm run dev
```

## 📈 System Status Check

```bash
# Check Docker container
docker ps | grep plant-timescaledb

# Check database tables
psql -h localhost -p 5433 -U plantuser -d plantdb -c "\dt"

# Check recent snapshots
psql -h localhost -p 5433 -U plantuser -d plantdb -c "SELECT time, image_path, temperature_c FROM plant_snapshots ORDER BY time DESC LIMIT 5;"

# Check images folder
ls -lh plant-monitor/backend/images/
```

## 🎉 Success Indicators

✅ Webcam captures images successfully
✅ Images saved to `backend/images/` folder
✅ Metadata stored in `plant_snapshots` table
✅ FastAPI serves images at `/images/` endpoint
✅ React component displays latest snapshot
✅ Temperature, humidity, LED state linked correctly
✅ System ready for future VLM integration

## 📚 Next Steps

1. **Test single capture** - Verify camera permissions work
2. **Run capture loop** - Let it collect a few snapshots
3. **Start FastAPI** - Test API endpoints
4. **View in React** - See images in dashboard
5. **Plan VLM integration** - Research vision models for plant health analysis
