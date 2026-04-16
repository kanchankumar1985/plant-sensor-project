# 🌱 Plant Sensor Project

A comprehensive IoT plant monitoring system using ESP32, TimescaleDB, and React for real-time environmental data collection and visualization.

## 🏗️ System Architecture

```
ESP32 (HDC302x + Touch) → USB Serial → serial_reader.py → TimescaleDB → FastAPI (routes + Logs API) → React Dashboard (LogsPanel)
                                           └─ SD Card storage: /Volumes/SD-128GB/PlantMonitor/{logs,images,videos}
```

- ESP32 publishes JSON over USB serial: temperature, humidity, touch state, LEDs.
- serial_reader.py parses JSON, inserts into TimescaleDB, triggers snapshots/video, and logs to SD card.
- FastAPI serves REST endpoints (sensor/touch) and exposes a Logs API for the UI.
- React dashboard shows live data, historical charts, and the LogsPanel with 1s auto-refresh.

## 🚀 Quick Start

### Prerequisites
- Docker installed
- Python 3.8+
- Node.js 16+
- ESP32 with HDC302x sensor

### 1. Start Database
```bash
docker run -d \
  --name timescaledb \
  -p 5433:5432 \
  -e POSTGRES_PASSWORD=plantpass \
  timescale/timescaledb:latest-pg14
```

### 2. Setup Backend
```bash
cd plant-monitor/backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Configure logging destination on SD card (required)
export LOGS_DIR=/Volumes/SD-128GB/PlantMonitor/logs
# Optional: create folders up-front
mkdir -p /Volumes/SD-128GB/PlantMonitor/{logs,images,videos}

# Start serial reader
python serial_reader.py

# Start API server (new terminal)
uvicorn app:app --reload --port 8000
```

### 3. Setup Frontend
```bash
cd plant-monitor/frontend
npm install
npm run dev
```

### 4. Upload ESP32 Code
Upload `touch_sensor/touch_sensor.ino` to your ESP32 using Arduino IDE.

Wiring (ESP32):
- HDC302x: SDA → GPIO21, SCL → GPIO22, VCC → 3.3V, GND → GND
- Touch sensor: S → GPIO4, VCC → 3.3V, GND → GND
- LEDs: Touch LED → GPIO23, Temp LED → GPIO18

Firmware improvements:
- Tries HDC302x addresses 0x44/0x45 with retries, I2C scan on failure, 100 kHz I2C clock
- Auto-reinitializes sensor after repeated read failures; emits touch-only JSON while offline

## 📊 Features

- **Real-time Data Collection**: USB serial communication from ESP32
- **Time-series Database**: TimescaleDB for optimized sensor data storage
- **Live Dashboard**: React-based visualization with charts
- **Historical Data**: Date/time range filtering with presets
- **REST API**: FastAPI backend with multiple endpoints
- **Docker Integration**: Containerized database for easy deployment

## 🔌 Hardware Setup

- **ESP32**: Main microcontroller
- **HDC302x**: Temperature & humidity sensor
- **Connections**: 
  - VCC → 3.3V
  - GND → GND  
  - SDA → GPIO 21
  - SCL → GPIO 22

## 📁 Project Structure

```
├── touch_sensor/                          # ESP32 main firmware (HDC302x + touch)
├── touch_led_control/                     # ESP32 test firmware (LED only)
├── touch_sensor_test/                     # ESP32 test firmware (touch debug)
├── plant-monitor/
│   ├── backend/
│   │   ├── app.py                         # FastAPI app; initializes centralized logging
│   │   ├── logging_config.py              # Central logging to SD card with rotation
│   │   ├── serial_reader.py               # Serial → DB, snapshots/video, full logging
│   │   ├── routes/
│   │   │   └── logs.py                    # Logs API (/api/logs/*)
│   │   ├── vlm/                           # VLM + YOLO analysis pipeline
│   │   └── sql/touch_events_schema.sql    # Touch events table (TimescaleDB)
│   └── frontend/
│       └── src/
│           ├── components/LogsPanel.jsx   # 1s auto-refresh, live indicator, auto-scroll
│           ├── AIStatusCard.jsx, AIAnalysisCard.jsx, VideoAnalysisCard.jsx, PlantHealthCard.jsx
│           └── App.jsx                    # Integrates LogsPanel (currently commented per user)
└── README.md
```

## 🧩 Modules Overview

- Backend
  - logging_config.py: File/console loggers, daily rotation, SD-path via LOGS_DIR.
  - app.py: Initializes logging, mounts routes, serves /images, /videos.
  - routes/logs.py: Logs API to fetch latest lines, list/read files, stats.
  - serial_reader.py: Serial parsing, DB inserts, snapshot/video triggers, health checks, comprehensive logging.
  - capture_with_vlm.py / capture_video.py: Use centralized logger for camera and processing.
- Firmware
  - touch_sensor.ino: Robust HDC302x init (I2C scan, 0x44/0x45, retries), auto-recovery, emits touch-only JSON on sensor outage.
- Frontend
  - LogsPanel.jsx: 1s auto-refresh, color-coded levels, live indicator, auto-scroll to latest logs.

## 💾 SD-Card Logging (Required)

- All runtime logs write to: `/Volumes/SD-128GB/PlantMonitor/logs`
- Set environment: `export LOGS_DIR=/Volumes/SD-128GB/PlantMonitor/logs`
- Loggers: app, api, serial_reader, camera, vlm
- Typical files: `app_YYYYMMDD.log`, `api_YYYYMMDD.log`, `serial_reader_YYYYMMDD.log`, `camera_YYYYMMDD.log`

## 🗄️ Database Changes

- Touch events table (TimescaleDB)
  - Columns: id, timestamp (timestamptz), device_id (text), state (TOUCHED/NOT_TOUCHED)
  - Index on timestamp DESC; optional hypertable conversion
- Sensor readings unchanged (time, device_id, temperature_c, humidity_pct, led_state)
- plant_snapshots table linked with optional video_path updates (from background capture)

## 🖥️ UI Changes

- New LogsPanel with:
  - Auto-refresh every 1s
  - Live status indicator (pulsing)
  - Auto-scroll to show newest lines
  - Level-based coloring (INFO/WARNING/ERROR/DEBUG)
  - Manual refresh + pause/resume

## 🐳 Docker Commands

```bash
# Check container status
docker ps

# View logs
docker logs timescaledb

# Stop/start container
docker stop timescaledb
docker start timescaledb
```

## 🔧 API Endpoints

- Sensor readings
  - `GET /api/readings/latest` - Latest sensor reading
  - `GET /api/readings/recent?limit=10` - Recent readings
  - `GET /api/readings/range?start=...&end=...` - Time range query
- Touch events
  - `POST /api/touch-event` - Insert touch state with timestamp/device_id
  - `GET /api/touch/latest` - Latest touch status with seconds_ago
  - `GET /api/touch/history?limit=50` - Recent touch events
- Logs API
  - `GET /api/logs/latest?limit=100` - Latest N log lines
  - `GET /api/logs/files` - List available log files
  - `GET /api/logs/file/{filename}?lines=N` - Read a specific log file
  - `GET /api/logs/stats` - Aggregate log stats

## 📖 Documentation

Open `PROJECT_DOCUMENTATION.html` in your browser for comprehensive system documentation including:
- Detailed architecture diagrams
- Setup instructions
- Troubleshooting guide
- Docker explanations
- Next-level upgrades

## 🛠️ Troubleshooting

### Serial Connection Issues
```bash
# Check USB serial ports
ls /dev/cu* | grep usbserial

# Verify serial reader process
ps aux | grep serial_reader
```

### Database Connection
```bash
# Test database connection
psql -h localhost -p 5433 -U plantuser -d plantdb -c "SELECT COUNT(*) FROM sensor_readings;"
```

### Logging not written to SD card
- Ensure `LOGS_DIR=/Volumes/SD-128GB/PlantMonitor/logs` is set in environment (or `.env`)
- Verify path exists and SD card is mounted with write permission
- Check FastAPI/serial_reader logs for path confirmation on startup

### Temperature inserts stop intermittently
- If you see periodic only-DEBUG touch logs and no “✓ Inserted … °C … %”: sensor likely offline
- Firmware auto-recovery will retry I2C (scan 0x44/0x45) and resume when available
- Backend will warn: “No valid temperature readings inserted in the last Ns…”
- Check wiring: SDA=21, SCL=22; keep I2C short; confirm pull-ups; power stability

### API Testing
```bash
# Test API endpoints
curl http://localhost:8000/api/readings/latest
curl http://localhost:8000/api/readings/recent?limit=5
```

## 🚀 Next Steps

- Add WiFi connectivity for remote monitoring
- Implement alerting system for threshold breaches
- Add soil moisture sensors
- Deploy to cloud platforms
- Mobile app development

## 📄 License

MIT License - Feel free to use and modify for your projects!

---

**Built with ❤️ for plant enthusiasts and IoT developers**
