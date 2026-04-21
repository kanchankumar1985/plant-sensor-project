# Touch Workflow Setup Guide

Complete setup instructions for the touch-triggered workflow with laptop speaker feedback.

## System Overview

**Flow:**
```
Touch Sensor → ESP32 → USB → Laptop Serial Reader → TTS Speaker + Background Pipeline
                                                      ↓
                                            Capture + Video + YOLO + VLM
```

## Prerequisites

- ESP32 with touch sensor on GPIO4
- USB cable connecting ESP32 to laptop
- Webcam on laptop
- Python 3.8+ with virtual environment
- Arduino IDE for ESP32

---

## Step 1: Install Python Dependencies

```bash
cd "/Users/kanchan/Plant Sensor Project/plant-monitor/backend"
source "/Users/kanchan/Plant Sensor Project/.venv/bin/activate"

# Install new dependencies
pip install pyttsx3==2.90
pip install fastapi==0.115.0
pip install uvicorn==0.32.0
pip install python-dotenv==1.0.1
pip install psycopg[binary]==3.2.3

# Or install all from requirements.txt
pip install -r requirements.txt
```

---

## Step 2: Upload ESP32 Code

1. Open Arduino IDE
2. Open file: `touch_sensor_trigger/touch_sensor_trigger.ino`
3. Select board: **ESP32 Dev Module**
4. Select port: Your ESP32 USB port
5. Upload code

**Expected Serial Output:**
```
READY
Touch sensor initialized on GPIO4
```

When you touch the sensor:
```
TOUCHED
```

---

## Step 3: Test Text-to-Speech

Test that laptop speaker works:

```bash
cd "/Users/kanchan/Plant Sensor Project/plant-monitor/backend"
python serial_touch_listener.py --test-tts
```

**Expected:** You should hear "Text to speech test successful" from laptop speakers.

**Troubleshooting:**
- **macOS:** TTS should work out of the box
- **Linux:** Install `espeak`: `sudo apt-get install espeak`
- **Windows:** Should work with SAPI5

---

## Step 4: Test Workflow (Without Serial)

Test the complete workflow without ESP32:

```bash
python serial_touch_listener.py --test-workflow
```

**Expected:**
- Hear "Sensor touched"
- See logs for:
  - Capturing snapshot
  - Recording video
  - Running YOLO
  - Queuing VLM

---

## Step 5: Start Serial Listener

### Auto-detect ESP32 port:
```bash
python serial_touch_listener.py
```

### Specify port manually:
```bash
# macOS/Linux
python serial_touch_listener.py --port /dev/cu.usbserial-0001

# Windows
python serial_touch_listener.py --port COM3
```

**Expected Output:**
```
============================================================
🎧 SERIAL TOUCH LISTENER STARTED
============================================================
Waiting for touch events from ESP32...
Press Ctrl+C to stop

✓ Found ESP32 port: /dev/cu.usbserial-0001 (CP2102 USB to UART Bridge)
🔌 Connecting to /dev/cu.usbserial-0001 at 115200 baud...
✓ Connected to /dev/cu.usbserial-0001
```

---

## Step 6: Test Touch Sensor

1. Touch the sensor
2. **Expected behavior:**

```
[12:34:56.789] Serial: TOUCHED

🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️
TOUCH EVENT DETECTED!
🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️

🔊 Speaking: 'Sensor touched'
📸 Step 1: Capturing snapshot...
✓ Snapshot saved: plant_20260416_201234.jpg
🎥 Step 2: Recording video clip...
✓ Video saved: plant_alert_20260416_201234.mp4
🔍 Step 3: Running YOLO detection...
✓ YOLO complete - Person detected: True
🤖 Step 4: Queuing VLM analysis...
💾 Step 5: Saving to database...

============================================================
✅ TOUCH WORKFLOW COMPLETED
============================================================
```

3. **You should hear:** "Sensor touched" from laptop speakers

---

## Step 7: Start Backend API (Optional)

If you want to use the web UI:

```bash
cd "/Users/kanchan/Plant Sensor Project/plant-monitor/backend"

# Add touch workflow routes to app.py
# (See integration section below)

# Start FastAPI
uvicorn app:app --reload --port 8000
```

---

## Step 8: Add UI Component (Optional)

Update your React app to include the touch workflow card:

```jsx
// In App.jsx or Dashboard.jsx
import TouchWorkflowCard from './components/TouchWorkflowCard';

function App() {
  return (
    <div>
      {/* Existing components */}
      <TouchWorkflowCard refreshInterval={2000} />
    </div>
  );
}
```

Start frontend:
```bash
cd "/Users/kanchan/Plant Sensor Project/plant-monitor/frontend"
npm start
```

---

## Integration with Existing Backend

### Option A: Add routes to existing `app.py`

```python
# In app.py
from routes.touch_workflow import router as touch_workflow_router

app.include_router(touch_workflow_router)
```

### Option B: Run as standalone service

Keep `serial_touch_listener.py` running separately from FastAPI.

---

## Running the Complete System

### Terminal 1: Serial Listener
```bash
cd "/Users/kanchan/Plant Sensor Project/plant-monitor/backend"
source "/Users/kanchan/Plant Sensor Project/.venv/bin/activate"
python serial_touch_listener.py
```

### Terminal 2: VLM Worker (Optional)
```bash
cd "/Users/kanchan/Plant Sensor Project/plant-monitor/backend"
source "/Users/kanchan/Plant Sensor Project/.venv/bin/activate"
python vlm_worker.py
```

### Terminal 3: Backend API (Optional)
```bash
cd "/Users/kanchan/Plant Sensor Project/plant-monitor/backend"
source "/Users/kanchan/Plant Sensor Project/.venv/bin/activate"
uvicorn app:app --reload --port 8000
```

### Terminal 4: Frontend (Optional)
```bash
cd "/Users/kanchan/Plant Sensor Project/plant-monitor/frontend"
npm start
```

---

## Verification Checklist

- [ ] ESP32 sends "TOUCHED" when sensor is touched
- [ ] Laptop speaks "Sensor touched" through speakers
- [ ] Snapshot is captured and saved
- [ ] Video clip is recorded and saved
- [ ] YOLO detection runs on image
- [ ] VLM analysis is queued
- [ ] Logs are written to logs directory
- [ ] UI shows workflow status (if using web UI)

---

## Troubleshooting

### No sound from laptop speakers

**macOS:**
```bash
# Test system TTS
say "Hello"
```

**Linux:**
```bash
# Install espeak
sudo apt-get install espeak

# Test
espeak "Hello"
```

**Python test:**
```python
import pyttsx3
engine = pyttsx3.init()
engine.say("Test")
engine.runAndWait()
```

### Serial port not found

List available ports:
```bash
python -m serial.tools.list_ports
```

### Touch sensor not responding

1. Check wiring:
   - Touch sensor S → GPIO4
   - Touch sensor VCC → 3.3V
   - Touch sensor GND → GND

2. Test with Arduino Serial Monitor:
   - Upload code
   - Open Serial Monitor (115200 baud)
   - Touch sensor
   - Should see "TOUCHED"

### Workflow not triggering

Check logs:
```bash
tail -f logs/camera_*.log
```

Enable debug logging in `serial_touch_listener.py`:
```python
logging.basicConfig(level=logging.DEBUG)
```

---

## File Locations

### Code Files
- ESP32: `touch_sensor_trigger/touch_sensor_trigger.ino`
- Serial Listener: `plant-monitor/backend/serial_touch_listener.py`
- TTS Service: `plant-monitor/backend/services/tts_service.py`
- Workflow: `plant-monitor/backend/services/touch_workflow.py`
- API Routes: `plant-monitor/backend/routes/touch_workflow.py`
- UI Component: `plant-monitor/frontend/src/components/TouchWorkflowCard.jsx`

### Output Files
- Images: `/Volumes/SD-128GB/PlantMonitor/images/`
- Videos: `/Volumes/SD-128GB/PlantMonitor/videos/`
- Logs: `plant-monitor/backend/logs/`

---

## API Endpoints

### Trigger workflow manually
```bash
curl -X POST http://localhost:8000/api/touch-workflow/trigger
```

### Get workflow status
```bash
curl http://localhost:8000/api/touch-workflow/status
```

### Test TTS
```bash
curl -X POST http://localhost:8000/api/touch-workflow/test-tts
```

---

## Advanced Configuration

### Adjust TTS voice speed

Edit `services/tts_service.py`:
```python
self.engine.setProperty('rate', 150)  # Default: 150 words/min
self.engine.setProperty('volume', 0.9)  # Default: 0.9 (0.0-1.0)
```

### Change spoken message

Edit `services/tts_service.py`:
```python
def speak_touch_event(self):
    self.speak("Custom message here", blocking=False)
```

### Disable video recording

Edit `services/touch_workflow.py`:
```python
def _record_video(self):
    logger.info("Video recording disabled")
    return
```

---

## Next Steps

1. ✅ Test basic touch → sound workflow
2. ✅ Verify snapshot capture works
3. ✅ Verify video recording works
4. ✅ Verify YOLO detection works
5. ✅ Verify VLM queuing works
6. 🔄 Add custom spoken messages for different events
7. 🔄 Add database logging of touch events
8. 🔄 Add web UI dashboard
9. 🔄 Add email/SMS notifications

---

## Support

If you encounter issues:

1. Check logs: `tail -f logs/camera_*.log`
2. Test components individually using `--test-tts` and `--test-workflow`
3. Verify ESP32 serial output in Arduino Serial Monitor
4. Check that all dependencies are installed
5. Verify webcam is accessible: `ls /dev/video*` (Linux) or check System Preferences (macOS)

---

## Summary

**What happens when you touch the sensor:**

1. ESP32 detects touch on GPIO4
2. ESP32 sends "TOUCHED" via USB serial
3. Laptop serial listener receives message
4. Laptop immediately speaks "Sensor touched" through speakers
5. Background workflow starts:
   - Capture snapshot
   - Record 5-second video
   - Run YOLO person detection
   - Queue VLM analysis
   - Save to database
6. Logs are written
7. UI updates (if running)

**All processing happens locally on your laptop - no cloud required!**
