# Touch Sensor End-to-End Debugging Guide

Complete debugging checklist for the ESP32 → FastAPI → TimescaleDB → React pipeline.

---

## 🔧 Layer 1: Hardware Testing

### 1.1 Verify Touch Sensor Wiring

```
Touch Sensor → ESP32
VCC → 3.3V
GND → GND
S → GPIO4
```

**Test:**
- Power on ESP32
- Touch sensor LED should light up when powered
- Check continuity with multimeter if available

### 1.2 Test Touch Sensor Output

**Without ESP32:**
- Use multimeter to measure voltage on S pin
- Should be HIGH (~3.3V) when touched
- Should be LOW (~0V) when not touched

**With ESP32 (Serial Monitor):**
```arduino
void setup() {
  Serial.begin(115200);
  pinMode(4, INPUT);
}

void loop() {
  Serial.println(digitalRead(4));
  delay(500);
}
```

Expected output:
- `0` when not touched
- `1` when touched

---

## 🖥️ Layer 2: ESP32 Code Testing

### 2.1 Serial-Only Mode (No WiFi)

**Edit `touch_sensor.ino`:**
```cpp
const bool SERIAL_ONLY_MODE = true;  // Disable WiFi
```

**Upload and Monitor:**
```bash
# Arduino IDE: Tools → Serial Monitor (115200 baud)
```

**Expected Output:**
```
=== Touch Sensor Starting ===
[MODE] Serial-only mode enabled (WiFi disabled)
[READY] Touch sensor initialized
Touch the sensor to test...

[STATE] NOT_TOUCHED
[STATE] TOUCHED
[STATE] NOT_TOUCHED
```

**✅ Pass Criteria:**
- Serial prints state changes
- No crashes or resets
- Debouncing works (no spam)

**❌ Fail Scenarios:**
- No output → Check Serial baud rate (115200)
- Random values → Check wiring
- Constant TOUCHED → Sensor may be faulty
- ESP32 resets → Power supply issue

### 2.2 WiFi Connection Test

**Edit `touch_sensor.ino`:**
```cpp
const bool SERIAL_ONLY_MODE = false;  // Enable WiFi
const char* WIFI_SSID = "YourActualSSID";
const char* WIFI_PASSWORD = "YourActualPassword";
```

**Expected Output:**
```
[WiFi] Connecting to YourSSID..... Connected!
[WiFi] IP Address: 192.168.1.XXX
```

**✅ Pass Criteria:**
- ESP32 gets IP address
- No WiFi disconnects

**❌ Fail Scenarios:**
- `Failed!` → Check SSID/password
- Timeout → Check router settings
- IP but no internet → Check router DHCP

### 2.3 HTTP POST Test (Without Backend)

**Use a test endpoint first:**
```cpp
const char* BACKEND_URL = "https://httpbin.org/post";
```

**Expected Output:**
```
[HTTP] Sending: {"timestamp":"...","state":"TOUCHED"}
[HTTP] Response code: 200
```

**✅ Pass Criteria:**
- HTTP POST succeeds
- Response code 200

**❌ Fail Scenarios:**
- Response code -1 → WiFi disconnected
- Response code 404 → Wrong URL
- Timeout → Network issue

---

## 🌐 Layer 3: Backend API Testing

### 3.1 Verify Database Connection

```bash
cd /Users/kanchan/Plant\ Sensor\ Project/plant-monitor/backend

# Test psycopg2 connection
python3 << 'EOF'
import psycopg2
conn = psycopg2.connect(
    host="localhost",
    port="5433",
    database="plantdb",
    user="plantuser",
    password="plantpass"
)
print("✅ Database connection successful")
conn.close()
EOF
```

**✅ Pass:** Prints success message  
**❌ Fail:** Connection error → Check TimescaleDB is running

### 3.2 Verify Table Schema

```bash
psql -h localhost -p 5433 -U plantuser -d plantdb
```

```sql
-- Check if table exists
\dt touch_events

-- Check schema
\d touch_events

-- Expected columns:
-- id (serial)
-- timestamp (timestamptz)
-- state (varchar)
```

**If table missing:**
```bash
psql -h localhost -p 5433 -U plantuser -d plantdb -f sql/touch_events_schema.sql
```

### 3.3 Test Backend Endpoint with curl

**Start FastAPI:**
```bash
cd backend
python3 -m uvicorn app:app --reload --port 8000
```

**Test POST endpoint:**
```bash
curl -X POST http://localhost:8000/api/touch-event \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2026-04-13T12:00:00Z",
    "state": "TOUCHED"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Touch event recorded: TOUCHED",
  "event_id": 1
}
```

**✅ Pass Criteria:**
- Status code 201
- Returns event_id
- No errors in FastAPI logs

**❌ Fail Scenarios:**
- 404 → Routes not registered
- 500 → Database error (check logs)
- 422 → Invalid JSON payload

**Test GET endpoint:**
```bash
curl http://localhost:8000/api/touch/latest
```

**Expected Response:**
```json
{
  "id": 1,
  "timestamp": "2026-04-13T12:00:00Z",
  "state": "TOUCHED",
  "seconds_ago": 5.2
}
```

### 3.4 Verify Database Insert

```sql
-- Check latest event
SELECT * FROM touch_events ORDER BY timestamp DESC LIMIT 5;

-- Expected:
-- id | timestamp | state
-- 1  | 2026-04-13 12:00:00+00 | TOUCHED
```

**✅ Pass:** Event appears in table  
**❌ Fail:** No rows → Backend not inserting

---

## 🔗 Layer 4: End-to-End Integration

### 4.1 ESP32 → Backend Test

**Update ESP32 code:**
```cpp
const char* BACKEND_URL = "http://192.168.1.XXX:8000/api/touch-event";
// Replace XXX with your laptop's local IP
```

**Find your laptop IP:**
```bash
# macOS
ifconfig | grep "inet " | grep -v 127.0.0.1

# Expected: inet 192.168.1.XXX
```

**Test Flow:**
1. Start FastAPI backend
2. Upload ESP32 code
3. Touch sensor
4. Check Serial Monitor
5. Check FastAPI logs
6. Check database

**Expected Serial Output:**
```
[STATE] TOUCHED
[HTTP] Sending: {"timestamp":"...","state":"TOUCHED"}
[HTTP] Response code: 201
[HTTP] Response: {"success":true,...}
```

**Expected FastAPI Log:**
```
INFO: Received touch event: state=TOUCHED, timestamp=...
INFO: Touch event inserted: id=1, state=TOUCHED
```

**✅ Pass Criteria:**
- ESP32 sends HTTP POST
- Backend receives and logs event
- Database has new row
- No errors in either system

**❌ Fail Scenarios:**

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| ESP32: Response code -1 | WiFi disconnected | Check WiFi signal |
| ESP32: Response code 404 | Wrong URL | Verify laptop IP |
| Backend: No request received | Firewall blocking | Disable firewall temporarily |
| Backend: 500 error | Database down | Restart TimescaleDB |
| Database: No insert | Backend error | Check FastAPI logs |

---

## 🎨 Layer 5: Frontend Testing

### 5.1 Test API Endpoint in Browser

**Open browser:**
```
http://localhost:8000/api/touch/latest
```

**Expected JSON:**
```json
{
  "id": 1,
  "timestamp": "2026-04-13T12:00:00Z",
  "state": "TOUCHED",
  "seconds_ago": 10.5
}
```

**✅ Pass:** JSON displays  
**❌ Fail:** 404 → Backend not running

### 5.2 Test React Component

**Start React dev server:**
```bash
cd frontend
npm run dev
```

**Add component to App.jsx:**
```jsx
import TouchStatusCard from './TouchStatusCard';

function App() {
  return (
    <div className="p-8">
      <TouchStatusCard />
    </div>
  );
}
```

**Expected Behavior:**
- Component loads
- Shows "NOT_TOUCHED" initially (gray badge)
- Updates every 2 seconds
- Shows green badge when TOUCHED
- Displays timestamp

**✅ Pass Criteria:**
- No console errors
- Live indicator pulses
- Status updates automatically

**❌ Fail Scenarios:**
- CORS error → Add CORS middleware to FastAPI
- 404 error → Backend not running
- Stale data → Check polling interval

### 5.3 End-to-End Live Test

**Full Flow:**
1. Start TimescaleDB
2. Start FastAPI backend
3. Start React frontend
4. Upload ESP32 code
5. Touch sensor
6. Watch React UI update

**Expected Timeline:**
```
T+0s:  Touch sensor
T+0s:  ESP32 Serial: [STATE] TOUCHED
T+0.5s: ESP32 Serial: [HTTP] Response code: 201
T+0.5s: Backend log: Touch event inserted
T+2s:   React UI: Badge turns green
```

---

## 🐛 Common Issues & Solutions

### Issue: ESP32 keeps resetting

**Symptoms:**
- Serial Monitor shows boot messages repeatedly
- ESP32 LED blinks constantly

**Causes:**
- Insufficient power supply
- Faulty USB cable
- Code crash (infinite loop, memory leak)

**Solutions:**
1. Use different USB cable/port
2. Add `delay(10)` in loop
3. Check for null pointer dereferences
4. Use Serial-only mode to isolate WiFi issues

### Issue: Backend receives duplicate events

**Symptoms:**
- Database has multiple identical timestamps
- ESP32 sends same event twice

**Causes:**
- Debounce delay too short
- HTTP retry logic

**Solutions:**
1. Increase `DEBOUNCE_MS` to 100
2. Add server-side deduplication
3. Check ESP32 doesn't retry on success

### Issue: React shows stale data

**Symptoms:**
- Touch sensor changes but UI doesn't update
- Timestamp doesn't refresh

**Causes:**
- Polling stopped
- Backend not returning latest data
- CORS blocking requests

**Solutions:**
1. Check browser console for errors
2. Verify `/api/touch/latest` returns correct data
3. Add CORS middleware to FastAPI:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: Database connection fails

**Symptoms:**
- Backend: `Database connection failed`
- psycopg2 error

**Causes:**
- TimescaleDB not running
- Wrong credentials
- Port conflict

**Solutions:**
```bash
# Check if TimescaleDB is running
docker ps | grep timescale

# Restart TimescaleDB
docker restart timescaledb

# Verify port
lsof -i :5433
```

---

## 📋 Quick Diagnostic Commands

```bash
# Check ESP32 Serial output
# Arduino IDE → Tools → Serial Monitor (115200 baud)

# Check backend logs
cd backend && python3 -m uvicorn app:app --reload --log-level debug

# Check database
psql -h localhost -p 5433 -U plantuser -d plantdb -c "SELECT * FROM touch_events ORDER BY timestamp DESC LIMIT 5;"

# Check frontend console
# Browser → F12 → Console tab

# Test full pipeline
curl -X POST http://localhost:8000/api/touch-event \
  -H "Content-Type: application/json" \
  -d '{"timestamp":"2026-04-13T12:00:00Z","state":"TOUCHED"}' && \
curl http://localhost:8000/api/touch/latest
```

---

## ✅ Success Checklist

- [ ] Touch sensor outputs correct voltage
- [ ] ESP32 prints state changes to Serial
- [ ] ESP32 connects to WiFi
- [ ] ESP32 sends HTTP POST successfully
- [ ] Backend receives and logs events
- [ ] Database contains event rows
- [ ] `/api/touch/latest` returns correct JSON
- [ ] React component displays status
- [ ] React component updates every 2 seconds
- [ ] Green badge appears when touched
- [ ] Gray badge appears when not touched
- [ ] No errors in any logs

**If all checked: 🎉 System is working end-to-end!**
