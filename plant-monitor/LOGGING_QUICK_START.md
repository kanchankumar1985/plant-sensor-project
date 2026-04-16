# 🚀 Logging System - Quick Start Guide

## ⚡ 3-Minute Setup

### 1. Add to `.env` file

```bash
LOGS_DIR=/Volumes/SD-128GB/PlantMonitor/logs
```

### 2. Start Backend

```bash
cd plant-monitor/backend
python app.py
```

### 3. View Logs in Browser

```bash
cd plant-monitor/frontend
npm run dev
```

Open `http://localhost:5173` → Scroll to **System Logs** section

## 📝 Add Logging to Your Code

```python
import logging_config

# Get logger
logger = logging_config.get_serial_logger()

# Log messages
logger.info("Operation started")
logger.warning("Temperature high")
logger.error("Failed to connect", exc_info=True)
```

## 🌐 Quick API Test

```bash
# Get latest logs
curl http://localhost:8000/api/logs/latest?limit=10

# List log files
curl http://localhost:8000/api/logs/files

# Get stats
curl http://localhost:8000/api/logs/stats
```

## 📊 Available Loggers

```python
from logging_config import (
    get_app_logger,        # Main app
    get_serial_logger,     # Serial reader
    get_camera_logger,     # Camera ops
    get_yolo_logger,       # YOLO detection
    get_vlm_logger,        # VLM analysis
    get_db_logger,         # Database
    get_api_logger,        # API routes
)
```

## 🎨 Log Levels

```python
logger.debug("Detailed info")      # Gray in UI
logger.info("General info")        # Green in UI
logger.warning("Warning message")  # Yellow in UI
logger.error("Error occurred")     # Red in UI
```

## 📁 Where Are Logs?

Default: `backend/logs/`  
Custom: Set `LOGS_DIR` in `.env`

Files: `component_YYYYMMDD.log`

## ✅ Verify It Works

1. ✅ Check logs directory exists
2. ✅ See log files created
3. ✅ Console shows messages
4. ✅ API returns logs: `curl http://localhost:8000/api/logs/latest`
5. ✅ UI shows logs (auto-refreshes every 5s)

## 🐛 Quick Troubleshooting

**No logs appearing?**
```bash
# Check directory
ls -la /Volumes/SD-128GB/PlantMonitor/logs

# Check permissions
chmod 755 /Volumes/SD-128GB/PlantMonitor/logs
```

**UI not showing logs?**
```bash
# Test API
curl http://localhost:8000/api/logs/latest

# Check browser console (F12)
```

## 📚 Full Documentation

See `LOGGING_README.md` for complete guide.

---

**That's it!** Your logging system is ready to use. 🎉
