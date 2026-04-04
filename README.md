# 🌱 Plant Sensor Project

A comprehensive IoT plant monitoring system using ESP32, TimescaleDB, and React for real-time environmental data collection and visualization.

## 🏗️ System Architecture

```
ESP32 (HDC302x) → USB Serial → Python → Docker (TimescaleDB) → FastAPI → React Dashboard
```

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
Upload `usb_sensor/usb_sensor.ino` to your ESP32 using Arduino IDE.

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
├── usb_sensor/           # ESP32 Arduino code
├── plant-monitor/
│   ├── backend/          # Python FastAPI server
│   └── frontend/         # React dashboard
├── PROJECT_DOCUMENTATION.html  # Complete documentation
└── README.md
```

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

- `GET /api/readings/latest` - Latest sensor reading
- `GET /api/readings/recent?limit=10` - Recent readings
- `GET /api/readings/range?start=...&end=...` - Time range query

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
