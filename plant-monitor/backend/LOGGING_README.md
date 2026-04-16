# Serial Reader Logging System

## Overview
The serial reader now automatically saves all output to timestamped log files for future reference.

## Log File Location
```
plant-monitor/backend/logs/serial_reader_YYYYMMDD_HHMMSS.log
```

## Features
- ✅ **Automatic timestamping**: Every log entry includes `[YYYY-MM-DD HH:MM:SS]` timestamp
- ✅ **File rotation**: Logs rotate at 10MB, keeps last 10 files
- ✅ **Dual output**: Logs appear both in console and file
- ✅ **Persistent storage**: All sensor data, snapshots, and errors are saved

## Usage

### Option 1: Run with built-in logging (Recommended)
```bash
cd /Users/kanchan/Plant\ Sensor\ Project/plant-monitor/backend
source /Users/kanchan/Plant\ Sensor\ Project/.venv/bin/activate
python serial_reader.py
```

The script will announce the log file location at startup:
```
🌱 Plant Sensor Serial Reader Starting...
📝 Logging to: /Users/kanchan/Plant Sensor Project/plant-monitor/backend/logs/serial_reader_20260410_220500.log
```

### Option 2: Run with shell script wrapper
```bash
cd /Users/kanchan/Plant\ Sensor\ Project/plant-monitor/backend
./start_serial_reader.sh
```

## Log Format

### Console Output
```
✓ Inserted: plant-esp32-01 - 27.75°C, 52.78%, LED: ON
🔥 TEMPERATURE ALERT: 27.75°C > 25.0°C
📸 Triggering automatic snapshot with VLM analysis...
```

### Log File Output
```
[2026-04-10 22:05:00] INFO - ✓ Inserted: plant-esp32-01 - 27.75°C, 52.78%, LED: ON
[2026-04-10 22:05:30] INFO - 🔥 TEMPERATURE ALERT: 27.75°C > 25.0°C
[2026-04-10 22:05:31] INFO - 📸 Triggering automatic snapshot with VLM analysis...
```

## Log Rotation
- **Max file size**: 10MB
- **Backup count**: 10 files
- **Naming**: `serial_reader_YYYYMMDD_HHMMSS.log`
- **Old logs**: Automatically renamed to `.log.1`, `.log.2`, etc.

## Viewing Logs

### View latest log
```bash
tail -f logs/serial_reader_*.log | tail -1
```

### View all logs from today
```bash
ls -lt logs/ | grep $(date +%Y%m%d)
```

### Search logs for errors
```bash
grep -r "ERROR" logs/
```

### Search for specific temperature alerts
```bash
grep "TEMPERATURE ALERT" logs/*.log
```

## Log Cleanup

### Remove logs older than 30 days
```bash
find logs/ -name "serial_reader_*.log*" -mtime +30 -delete
```

### Keep only last 20 log files
```bash
cd logs/
ls -t serial_reader_*.log* | tail -n +21 | xargs rm -f
```

## What Gets Logged

✅ **Sensor readings**: Every temperature/humidity reading
✅ **Snapshots**: Image captures with YOLO detection
✅ **VLM analysis**: AI vision-language model results
✅ **Video recordings**: Temperature alert videos
✅ **Database operations**: Insert confirmations and errors
✅ **System events**: Startup, shutdown, errors
✅ **Touch events**: Plant touch sensor triggers

## Troubleshooting

### Log file not created
- Check permissions: `ls -la logs/`
- Ensure directory exists: `mkdir -p logs/`

### Logs too large
- Reduce `maxBytes` in `serial_reader.py` (currently 10MB)
- Increase rotation frequency

### Missing timestamps
- Logs use Python's logging module with automatic timestamps
- Format: `[YYYY-MM-DD HH:MM:SS] LEVEL - message`

## Integration with VLM Pipeline

All VLM analysis steps are logged:
```
[2026-04-10 22:05:31] INFO - 🤖 Running VLM image analysis...
[2026-04-10 22:05:32] INFO - 🤖 Analyzing image with llava:7b...
[2026-04-10 22:05:45] INFO - ✅ VLM analysis complete
[2026-04-10 22:05:45] INFO - 📊 Plant health: healthy
[2026-04-10 22:05:45] INFO - 🔍 Reliability: high
```

## Best Practices

1. **Monitor disk space**: Logs can grow large over time
2. **Regular cleanup**: Remove old logs monthly
3. **Backup important logs**: Copy critical logs before cleanup
4. **Check for errors**: Regularly grep for ERROR/WARNING
5. **Correlate with database**: Use timestamps to match DB entries
