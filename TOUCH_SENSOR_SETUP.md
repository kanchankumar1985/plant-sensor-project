# Touch Sensor Integration Guide

Complete integration of TTP223 capacitive touch sensor with ESP32 plant monitoring system.

## Hardware Setup

### Components
- ESP32 board
- TTP223 / Keyes Touch Module
- Jumper wires

### Wiring
```
Touch Sensor → ESP32
VCC         → 3.3V
GND         → GND
S (Signal)  → GPIO4 (D4)
```

## Software Components

### 1. ESP32 Firmware (`touch_sensor.ino`)

**Features:**
- Reads digital input from GPIO4
- 50ms debounce to prevent noise
- Outputs `TOUCH_EVENT:TOUCHED` or `TOUCH_EVENT:NOT_TOUCHED` over serial
- Integrates with HDC302x sensor (optional)
- Includes touch state in sensor JSON data

**Upload:**
```bash
cd "/Users/kanchan/Plant Sensor Project"
arduino-cli compile --fqbn esp32:esp32:esp32 touch_sensor
arduino-cli upload --fqbn esp32:esp32:esp32 --port /dev/cu.usbserial-0001 touch_sensor
```

### 2. Database Schema (`003_create_touch_events.sql`)

**Tables:**
- `touch_events` - Hypertable partitioned by time
- `latest_touch_state` - View showing current state per device

**Features:**
- Time-series optimized storage
- 90-day retention policy
- Indexes on timestamp, device_id, and state

**Run Migration:**
```bash
cd plant-monitor/backend
psql -h localhost -p 5433 -U plantuser -d plantdb -f migrations/003_create_touch_events.sql
```

### 3. Backend API (FastAPI)

**New Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/touch-event` | Record touch event |
| GET | `/api/touch-event/latest` | Get most recent event |
| GET | `/api/touch-event/recent` | Get recent events (limit=100) |
| GET | `/api/touch-event/status` | Get current touch status (LIVE) |

**Request Example:**
```bash
curl -X POST http://localhost:8000/api/touch-event \
  -H "Content-Type: application/json" \
  -d '{"state": "TOUCHED"}'
```

**Response Example:**
```json
{
  "id": 123,
  "timestamp": "2026-04-08T23:45:00Z",
  "device_id": "plant-esp32-01",
  "state": "TOUCHED"
}
```

### 4. Serial Reader (`serial_reader.py`)

**Enhanced Features:**
- Parses `TOUCH_EVENT:` lines from ESP32
- Inserts touch events into database
- Displays touch status with emojis (👆/🖐️)

**Run:**
```bash
cd plant-monitor/backend
python serial_reader.py
```

### 5. Frontend Component (`TouchStatusCard.jsx`)

**Features:**
- Live status indicator (green when touched, gray when not)
- Animated pulse effect on touch
- Auto-refresh every 2 seconds
- Shows last updated timestamp
- Responsive design

**Integration:**
Add to `App.jsx`:
```jsx
import TouchStatusCard from './TouchStatusCard';

// In your component:
<TouchStatusCard />
```

## System Flow

```
Touch Sensor (GPIO4)
    ↓
ESP32 Firmware (debounce + detect)
    ↓
Serial: "TOUCH_EVENT:TOUCHED"
    ↓
serial_reader.py (parse)
    ↓
TimescaleDB (touch_events table)
    ↓
FastAPI (/api/touch-event/status)
    ↓
React (TouchStatusCard - polls every 2s)
    ↓
User sees LIVE status
```

## Testing

### 1. Test ESP32 Firmware
```bash
# Monitor serial output
python3 << 'EOF'
import serial
ser = serial.Serial('/dev/cu.usbserial-0001', 115200)
while True:
    line = ser.readline().decode('utf-8', errors='ignore').strip()
    if line:
        print(line)
EOF
```

**Expected Output:**
```
READY: Plant sensor with touch detection initialized
INFO: Touch sensor on GPIO4
TOUCH_EVENT:NOT_TOUCHED
{"device_id":"plant-esp32-01","temperature_c":25.30,...,"touch_state":"NOT_TOUCHED"}
TOUCH_EVENT:TOUCHED
{"device_id":"plant-esp32-01","temperature_c":25.30,...,"touch_state":"TOUCHED"}
```

### 2. Test Database
```sql
-- Check recent touch events
SELECT * FROM touch_events ORDER BY timestamp DESC LIMIT 10;

-- Check current status
SELECT * FROM latest_touch_state;
```

### 3. Test API
```bash
# Get current status
curl http://localhost:8000/api/touch-event/status

# Get recent events
curl http://localhost:8000/api/touch-event/recent?limit=10
```

### 4. Test Frontend
1. Start backend: `cd plant-monitor/backend && ./start_backend.sh`
2. Start frontend: `cd plant-monitor/frontend && npm run dev`
3. Open browser: `http://localhost:5173`
4. Touch sensor and watch card update in real-time

## Troubleshooting

### Touch sensor not responding
- Check wiring (VCC, GND, Signal)
- Verify GPIO4 is not used by another component
- Test with multimeter: Signal should be HIGH (3.3V) when touched

### No data in database
- Check serial_reader.py is running
- Verify database connection
- Check ESP32 serial output for TOUCH_EVENT lines

### Frontend not updating
- Verify backend is running on port 8000
- Check browser console for errors
- Confirm API endpoint returns data: `/api/touch-event/status`

### Rapid toggling (bouncing)
- Increase DEBOUNCE_DELAY in touch_sensor.ino (default: 50ms)
- Try 100ms or 200ms for more stability

## Optional Enhancements

### 1. WiFi HTTP POST
Add to `touch_sensor.ino`:
```cpp
#include <WiFi.h>
#include <HTTPClient.h>

void sendTouchEventHTTP(String state) {
  HTTPClient http;
  http.begin("http://192.168.1.71:8000/api/touch-event");
  http.addHeader("Content-Type", "application/json");
  
  String payload = "{\"state\":\"" + state + "\"}";
  int httpCode = http.POST(payload);
  
  http.end();
}
```

### 2. Camera Trigger on Touch
Add to `serial_reader.py`:
```python
def insert_touch_event(conn, state, device_id='plant-esp32-01'):
    # ... existing code ...
    
    # Trigger camera on touch
    if state == "TOUCHED":
        from capture_with_detection import capture_and_detect
        sensor_data = {'temperature_c': 0, 'humidity_pct': 0}
        capture_and_detect(sensor_data, conn, datetime.now())
```

### 3. WebSocket for Real-time Updates
Replace polling with WebSocket for instant updates without delay.

## File Locations

```
Plant Sensor Project/
├── touch_sensor/
│   └── touch_sensor.ino          # ESP32 firmware
├── plant-monitor/
│   ├── backend/
│   │   ├── migrations/
│   │   │   └── 003_create_touch_events.sql
│   │   ├── app.py                # Updated with touch endpoints
│   │   └── serial_reader.py      # Updated with touch parsing
│   └── frontend/
│       └── src/
│           └── TouchStatusCard.jsx
└── TOUCH_SENSOR_SETUP.md         # This file
```

## Summary

✅ Hardware: TTP223 connected to GPIO4  
✅ Firmware: Debounced touch detection with serial output  
✅ Database: Hypertable with time-series optimization  
✅ Backend: 4 REST endpoints for touch events  
✅ Frontend: Live status card with 2s polling  
✅ Integration: Full pipeline from hardware to UI  

**System is production-ready for local deployment!**
