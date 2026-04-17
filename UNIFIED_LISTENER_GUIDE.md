# Unified Serial Listener Guide

## Overview

The **Unified Serial Listener** (`serial_unified_listener.py`) combines all serial communication functionality into a single script. You only need to run this one script instead of multiple listeners.

## What It Does

This single script handles:

1. **Temperature & Humidity Monitoring**
   - Reads sensor data from ESP32
   - Saves readings to TimescaleDB
   - Logs all data points

2. **Touch Event Detection**
   - Detects when touch sensor is triggered
   - Speaks "Sensor touched" via laptop speakers (TTS)
   - Triggers complete workflow pipeline

3. **Auto-Snapshot on Temperature**
   - Captures snapshot when temperature exceeds threshold (25°C)
   - Includes cooldown period (30 seconds)

4. **Complete Workflow Pipeline**
   - Captures snapshot image
   - Records video clip
   - Runs YOLO object detection
   - Queues VLM analysis
   - Saves all metadata to database

## Quick Start

### Option 1: Using the startup script (Recommended)
```bash
cd /Users/kanchan/Plant\ Sensor\ Project/plant-monitor/backend
./start_unified_listener.sh
```

### Option 2: Direct Python command
```bash
cd /Users/kanchan/Plant\ Sensor\ Project/plant-monitor/backend
source venv/bin/activate  # if using virtual environment
python serial_unified_listener.py
```

## What You'll See

When started successfully, you'll see:
```
============================================================
🌱 UNIFIED SERIAL LISTENER STARTED
============================================================
Features:
  • Temperature/Humidity monitoring
  • Touch event detection with TTS
  • Auto-snapshot on temperature threshold
  • Complete workflow triggering
============================================================
Press Ctrl+C to stop

✓ Database connected
✓ Found ESP32 port: /dev/cu.usbserial-0001
🔌 Connecting to /dev/cu.usbserial-0001 at 115200 baud...
✓ Connected to /dev/cu.usbserial-0001
📊 Temp: 26.28°C, Humidity: 53.35%, LED: 1
```

## Events Handled

### 1. Regular Sensor Data
```
📊 Temp: 26.28°C, Humidity: 53.35%, LED: 1
```
- Automatically saved to database
- Logged for monitoring

### 2. Touch Event
```
👆 TOUCH EVENT DETECTED!
🔊 Speaking: "Sensor touched"
📸 Starting touch workflow...
```
- Laptop speaks "Sensor touched"
- Captures snapshot
- Records video
- Runs YOLO detection
- Queues VLM analysis

### 3. Temperature Threshold
```
🌡️ Temperature threshold exceeded: 26.28°C > 25.0°C
📸 Capturing snapshot...
✓ Snapshot saved: plant_20260416_204036.jpg
```
- Auto-captures snapshot
- 30-second cooldown between snapshots

## Old Scripts (No Longer Needed)

You can **ignore** these files:
- ❌ `serial_reader.py` - functionality now in unified listener
- ❌ `serial_touch_listener.py` - functionality now in unified listener
- ❌ `start_touch_listener.sh` - use `start_unified_listener.sh` instead

## Stopping the Listener

Press `Ctrl+C` to gracefully stop the listener.

## Troubleshooting

### Serial Port Busy
If you see "Resource busy" error:
```bash
# Kill any existing serial monitors
pkill -f "arduino-cli monitor"
pkill -f "serial_reader"
pkill -f "serial_touch_listener"
pkill -f "serial_unified_listener"
```

### Missing Dependencies
```bash
cd /Users/kanchan/Plant\ Sensor\ Project/plant-monitor/backend
source venv/bin/activate
pip install -r requirements.txt
```

### No Sound (TTS Not Working)
- Check system volume is not muted
- Verify `pyttsx3` is installed: `pip list | grep pyttsx3`
- Test TTS: `python -c "import pyttsx3; engine = pyttsx3.init(); engine.say('Test'); engine.runAndWait()"`

### Database Connection Failed
- Ensure PostgreSQL/TimescaleDB is running
- Check connection string in `.env` file
- Verify database exists: `psql -U plantuser -d plantdb -h localhost -p 5433`

## Integration with Other Services

The unified listener works alongside:
- **FastAPI Backend** (`main.py`) - Provides web API
- **VLM Worker** (`vlm_worker.py`) - Processes VLM analysis jobs
- **React Frontend** - Displays data and workflow status

All services can run simultaneously without conflicts.

## Logs

Logs are written to:
- `/Users/kanchan/Plant Sensor Project/plant-monitor/backend/logs/serial_reader.log`
- Rotates automatically when file reaches 10MB
- Keeps last 5 log files

## Summary

**Run only ONE command:**
```bash
./start_unified_listener.sh
```

This replaces the need for:
- ~~`python serial_reader.py`~~
- ~~`python serial_touch_listener.py`~~
- ~~Running multiple terminals~~

Everything is now unified in one simple script! 🎉
