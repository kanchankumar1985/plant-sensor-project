# VLM-Controlled Smart Watering System

## Overview

Your ESP32 plant monitor now uses **AI vision (VLM)** to decide when to water the plant!

## How It Works

### 1. Touch Trigger
- You touch the sensor
- ESP32 sends "VLM_ANALYSIS_REQUESTED" to Python

### 2. Camera Capture
- Python captures a photo of the plant
- YOLO detects if a person is in the frame
- Image is queued for VLM analysis

### 3. VLM Analysis
- VLM worker analyzes the image
- Checks for yellow leaves (`yellowing_visible`)
- Stores result in database

### 4. Pump Decision
- Python checks VLM result
- **If yellow leaves detected** → Send "PUMP_ON_YELLOW_LEAVES" to ESP32
- **If no yellow leaves** → Pump stays OFF

### 5. Pump Activation
- ESP32 receives command
- Checks 60-second cooldown
- Runs pump for 2 seconds
- LED lights up while pump runs

## Complete Workflow

```
Touch Sensor
    ↓
ESP32: "TOUCHED"
ESP32: "VLM_ANALYSIS_REQUESTED"
    ↓
Python: Capture image
Python: Run YOLO detection
Python: Queue VLM analysis
    ↓
VLM Worker: Analyze image
VLM Worker: Detect yellow leaves
VLM Worker: Save to database
    ↓
Python: Check VLM result
    ↓
IF yellowing_visible == True:
    Python → ESP32: "PUMP_ON_YELLOW_LEAVES"
    ESP32: Turn ON pump (2 seconds)
    ESP32: Turn ON LED (2 seconds)
ELSE:
    Pump stays OFF
```

## Configuration

### Arduino Settings (ESP32)
```cpp
PUMP_DURATION = 2000ms      // Pump runs for 2 seconds
PUMP_COOLDOWN = 60000ms     // 1 minute cooldown
```

### Python Settings
```python
max_wait = 30               // Wait up to 30 seconds for VLM
wait_interval = 2           // Check every 2 seconds
```

## Testing Steps

### 1. Start VLM Worker
```bash
cd plant-monitor/backend
python3 vlm_worker.py
```

### 2. Start Unified Listener
```bash
cd plant-monitor/backend
./start_unified_listener.sh
```

### 3. Touch the Sensor
- Touch the sensor
- Watch the logs:

**Expected output:**
```
🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️
TOUCH EVENT DETECTED!
🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️

📸 VLM Analysis requested - capturing image...
📸 Image captured: plant_20260420_220428.jpg
🔍 Running YOLO person detection...
✓ Snapshot saved with status 'queued'
⏳ Waiting for VLM worker to complete analysis...
   Still waiting... (2s/30s)
   Still waiting... (4s/30s)
✅ VLM analysis completed (waited 6s)

🔍 VLM Analysis Result:
   Yellowing visible: True
   Summary: Plant shows signs of yellowing leaves

🟡🟡🟡🟡🟡🟡🟡🟡🟡🟡
YELLOW LEAVES DETECTED!
💧 Triggering pump...
🟡🟡🟡🟡🟡🟡🟡🟡🟡🟡

========================================
🚰 Pump ON due to: YELLOW LEAVES DETECTED
========================================
✓ Pump will run for 2 seconds

[Pump runs for 2 seconds]

========================================
🛑 Pump OFF
========================================
```

### 4. If No Yellow Leaves
```
🔍 VLM Analysis Result:
   Yellowing visible: False
   Summary: Plant appears healthy

✅ No yellow leaves detected - pump will not run
```

## Serial Commands

### From ESP32 to Python:
- `TOUCHED` - Touch sensor pressed
- `VLM_ANALYSIS_REQUESTED` - Request VLM analysis
- `{"device_id":"ESP32_PLANT_01",...}` - Sensor data JSON

### From Python to ESP32:
- `PUMP_ON_YELLOW_LEAVES\n` - Turn on pump (yellow leaves detected)

## Database Schema

The VLM analysis stores:
```sql
yellowing_visible BOOLEAN    -- True if yellow leaves detected
vlm_analysis JSONB           -- Full VLM response
vlm_summary TEXT             -- Human-readable summary
analysis_status TEXT         -- 'queued', 'processing', 'completed'
```

## Troubleshooting

### Pump Not Running After Touch
1. Check VLM worker is running: `ps aux | grep vlm_worker`
2. Check database connection
3. Check serial logs for "YELLOW LEAVES DETECTED"
4. Verify cooldown period has passed (60 seconds)

### VLM Analysis Timeout
- Increase `max_wait` in Python (currently 30 seconds)
- Check VLM worker logs
- Verify Ollama is running

### Pump Runs Without Yellow Leaves
- Check database: `SELECT yellowing_visible FROM plant_snapshots ORDER BY time DESC LIMIT 1;`
- Verify VLM prompt is correct
- Check VLM model accuracy

## Advantages

✅ **AI-Powered Decision Making** - VLM analyzes plant health
✅ **Prevents Over-Watering** - Only waters when needed
✅ **Visual Confirmation** - Stores images for review
✅ **Cooldown Protection** - 60-second minimum between waterings
✅ **Complete Logging** - All decisions logged to database
✅ **Manual Override** - Touch sensor provides easy trigger

## Files Modified

1. `touch_sensor_led_pump_unified.ino` - ESP32 code
   - Removed automatic temperature trigger
   - Added serial command listener
   - Increased cooldown to 60 seconds

2. `serial_unified_listener.py` - Python listener
   - Added VLM analysis request handler
   - Added yellow leaves checker
   - Added pump command sender

## Next Steps

- Adjust VLM prompt for better yellow leaf detection
- Add confidence threshold for pump trigger
- Log pump activations to separate table
- Add web dashboard to view VLM decisions
- Train custom model for plant health

## Summary

Your plant now gets watered **only when AI detects yellow leaves**! 🌱🤖💧
