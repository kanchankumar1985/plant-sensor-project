# Touch Sensor Integration - Complete Implementation

End-to-end touch sensor system for ESP32 → FastAPI → TimescaleDB → React.

---

## 📁 File Organization

```
plant-monitor/
├── esp32/
│   └── touch_sensor/
│       └── touch_sensor.ino          # ESP32 Arduino code
│
├── backend/
│   ├── app.py                        # Main FastAPI app (updated)
│   ├── touch_routes.py               # Touch sensor API routes (NEW)
│   └── sql/
│       └── touch_events_schema.sql   # Database schema validation (NEW)
│
├── frontend/
│   └── src/
│       └── TouchStatusCard.jsx       # React status display (updated)
│
├── TOUCH_SENSOR_DEBUG.md             # Complete debugging guide (NEW)
└── TOUCH_SENSOR_README.md            # This file (NEW)
```

---

## 🚀 Quick Start Guide

### Step 1: Database Setup

```bash
# Connect to TimescaleDB
psql -h localhost -p 5433 -U plantuser -d plantdb

# Run schema validation
\i backend/sql/touch_events_schema.sql

# Verify table exists
\d touch_events
```

### Step 2: Backend Setup

```bash
cd backend

# Install dependencies (if not already installed)
pip install fastapi uvicorn psycopg2-binary pydantic

# Start server
python3 -m uvicorn app:app --reload --port 8000
```

**Verify backend is running:**
```bash
curl http://localhost:8000/api/touch/latest
# Should return 404 (no events yet) or latest event
```

### Step 3: ESP32 Setup

**Hardware Connection:**
```
Touch Sensor → ESP32
VCC → 3.3V
GND → GND
S → GPIO4
```

**Configure WiFi:**

Edit `esp32/touch_sensor/touch_sensor.ino`:
```cpp
const char* WIFI_SSID = "YourWiFiName";
const char* WIFI_PASSWORD = "YourWiFiPassword";
```

**Find your laptop's IP:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
# Example output: inet 192.168.1.100
```

**Update backend URL:**
```cpp
const char* BACKEND_URL = "http://192.168.1.100:8000/api/touch-event";
```

**Upload to ESP32:**
1. Open `touch_sensor.ino` in Arduino IDE
2. Select board: ESP32 Dev Module
3. Select port
4. Click Upload
5. Open Serial Monitor (115200 baud)

### Step 4: Frontend Setup

```bash
cd frontend

# Install dependencies (if not already installed)
npm install

# Start dev server
npm run dev
```

**Add component to your app:**

Edit `frontend/src/App.jsx`:
```jsx
import TouchStatusCard from './TouchStatusCard';

function App() {
  return (
    <div className="container mx-auto p-8">
      <h1 className="text-3xl font-bold mb-8">Plant Monitor</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <TouchStatusCard />
        {/* Your other components */}
      </div>
    </div>
  );
}
```

---

## 🧪 Testing the Pipeline

### Test 1: Serial-Only Mode (No WiFi)

**Purpose:** Verify hardware and basic ESP32 code

**Steps:**
1. Edit `touch_sensor.ino`: Set `SERIAL_ONLY_MODE = true`
2. Upload to ESP32
3. Open Serial Monitor
4. Touch sensor

**Expected Output:**
```
[STATE] NOT_TOUCHED
[STATE] TOUCHED
[STATE] NOT_TOUCHED
```

✅ **Pass:** State changes print correctly  
❌ **Fail:** See debugging guide

### Test 2: Backend API Test

**Purpose:** Verify backend receives and stores events

**Steps:**
```bash
# Send test event
curl -X POST http://localhost:8000/api/touch-event \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2026-04-13T12:00:00Z",
    "state": "TOUCHED"
  }'

# Check it was stored
curl http://localhost:8000/api/touch/latest
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Touch event recorded: TOUCHED",
  "event_id": 1
}
```

✅ **Pass:** Event stored and retrieved  
❌ **Fail:** Check backend logs

### Test 3: ESP32 → Backend Integration

**Purpose:** Verify end-to-end communication

**Steps:**
1. Edit `touch_sensor.ino`: Set `SERIAL_ONLY_MODE = false`
2. Configure WiFi credentials
3. Set correct backend URL with your laptop IP
4. Upload to ESP32
5. Touch sensor
6. Watch Serial Monitor

**Expected Serial Output:**
```
[WiFi] Connected!
[WiFi] IP Address: 192.168.1.XXX
[STATE] TOUCHED
[HTTP] Sending: {"timestamp":"...","state":"TOUCHED"}
[HTTP] Response code: 201
[HTTP] Response: {"success":true,...}
```

**Verify in database:**
```sql
SELECT * FROM touch_events ORDER BY timestamp DESC LIMIT 5;
```

✅ **Pass:** Event appears in database  
❌ **Fail:** See debugging guide

### Test 4: Frontend Display

**Purpose:** Verify React UI updates

**Steps:**
1. Open browser to `http://localhost:5173`
2. Touch sensor on ESP32
3. Wait up to 2 seconds
4. Observe UI

**Expected Behavior:**
- Badge turns green
- Text shows "TOUCHED"
- Timestamp updates
- Live indicator pulses

✅ **Pass:** UI updates automatically  
❌ **Fail:** Check browser console

---

## 📊 API Endpoints

### POST /api/touch-event

**Create a new touch event**

**Request:**
```json
{
  "timestamp": "2026-04-13T12:00:00Z",
  "state": "TOUCHED"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Touch event recorded: TOUCHED",
  "event_id": 1
}
```

**Validation:**
- `state` must be "TOUCHED" or "NOT_TOUCHED"
- `timestamp` should be ISO 8601 format

### GET /api/touch/latest

**Get most recent touch event**

**Response (200 OK):**
```json
{
  "id": 1,
  "timestamp": "2026-04-13T12:00:00Z",
  "state": "TOUCHED",
  "seconds_ago": 5.2
}
```

**Response (404 Not Found):**
```json
{
  "detail": "No touch events found"
}
```

### GET /api/touch/history?limit=50

**Get recent touch event history**

**Response (200 OK):**
```json
{
  "success": true,
  "count": 10,
  "events": [
    {
      "id": 10,
      "timestamp": "2026-04-13T12:05:00Z",
      "state": "TOUCHED"
    },
    ...
  ]
}
```

---

## 🗄️ Database Schema

```sql
CREATE TABLE touch_events (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    state VARCHAR(20) NOT NULL CHECK (state IN ('TOUCHED', 'NOT_TOUCHED'))
);

CREATE INDEX idx_touch_events_timestamp ON touch_events (timestamp DESC);
```

**TimescaleDB Hypertable:**
```sql
SELECT create_hypertable('touch_events', 'timestamp', if_not_exists => TRUE);
```

---

## 🔧 Configuration

### ESP32 Configuration

**File:** `esp32/touch_sensor/touch_sensor.ino`

```cpp
// WiFi credentials
const char* WIFI_SSID = "YourWiFiName";
const char* WIFI_PASSWORD = "YourWiFiPassword";

// Backend URL (use your laptop's local IP)
const char* BACKEND_URL = "http://192.168.1.XXX:8000/api/touch-event";

// Hardware pin
const int TOUCH_PIN = 4;  // GPIO4

// Timing
const int DEBOUNCE_MS = 50;  // Debounce delay
const int WIFI_RETRY_DELAY = 5000;  // WiFi retry interval

// Testing mode
const bool SERIAL_ONLY_MODE = false;  // Set true to disable WiFi
```

### Backend Configuration

**File:** `backend/touch_routes.py`

```python
DB_CONFIG = {
    "host": "localhost",
    "port": "5433",
    "database": "plantdb",
    "user": "plantuser",
    "password": "plantpass"
}
```

### Frontend Configuration

**File:** `frontend/src/TouchStatusCard.jsx`

```javascript
// API endpoint
const response = await fetch('http://localhost:8000/api/touch/latest');

// Polling interval
const interval = setInterval(fetchTouchStatus, 2000);  // 2 seconds
```

---

## 🐛 Troubleshooting

See **[TOUCH_SENSOR_DEBUG.md](./TOUCH_SENSOR_DEBUG.md)** for complete debugging guide.

**Quick fixes:**

| Problem | Solution |
|---------|----------|
| ESP32 won't connect to WiFi | Check SSID/password, verify 2.4GHz network |
| Backend returns 404 | Verify routes registered in `app.py` |
| Database connection fails | Check TimescaleDB is running on port 5433 |
| React shows CORS error | Add CORS middleware to FastAPI |
| Touch sensor always HIGH | Check wiring, try different sensor |
| Events not saving | Check database credentials and table exists |

---

## 📈 Future Enhancements

- [ ] Add NTP time sync to ESP32 for accurate timestamps
- [ ] Implement event aggregation (touches per hour/day)
- [ ] Add touch duration tracking
- [ ] Create historical chart in React
- [ ] Add push notifications on touch events
- [ ] Implement ESP32 OTA updates
- [ ] Add multiple touch sensor support
- [ ] Create mobile app version

---

## 📝 Notes

- **WiFi Security:** Store credentials in separate config file (not committed to git)
- **Power Supply:** ESP32 may need external 5V supply for stable WiFi
- **Debouncing:** Adjust `DEBOUNCE_MS` if sensor is too sensitive
- **Polling:** 2-second interval balances responsiveness and server load
- **Database:** TimescaleDB hypertable optimizes time-series queries
- **Error Handling:** All layers include retry logic and graceful degradation

---

## ✅ Success Criteria

Your system is working correctly when:

1. ✅ ESP32 connects to WiFi and gets IP address
2. ✅ Serial Monitor shows state changes when touching sensor
3. ✅ HTTP POST returns 201 status code
4. ✅ Database contains touch events
5. ✅ `/api/touch/latest` returns correct JSON
6. ✅ React UI shows green badge when touched
7. ✅ React UI updates within 2 seconds
8. ✅ No errors in any logs (ESP32, backend, browser)

---

## 📚 Dependencies

**ESP32:**
- ArduinoJson (install via Library Manager)
- WiFi (built-in)
- HTTPClient (built-in)

**Backend:**
- fastapi
- uvicorn
- psycopg2-binary
- pydantic

**Frontend:**
- React
- (No additional dependencies needed)

**Database:**
- TimescaleDB (PostgreSQL extension)

---

## 🤝 Support

If you encounter issues:

1. Check **[TOUCH_SENSOR_DEBUG.md](./TOUCH_SENSOR_DEBUG.md)**
2. Verify all configuration values
3. Test each layer independently
4. Check logs at each layer
5. Ensure all services are running

---

**Last Updated:** April 13, 2026  
**Version:** 1.0.0
