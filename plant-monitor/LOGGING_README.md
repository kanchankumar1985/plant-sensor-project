# 📝 Plant Monitor Logging System

Complete end-to-end logging infrastructure for the Plant Monitor system.

## 📁 File Organization

```
plant-monitor/
├── backend/
│   ├── logging_config.py          # Centralized logging configuration
│   ├── routes/
│   │   └── logs.py                # Logs API endpoints
│   ├── app.py                     # Updated with logging
│   ├── serial_reader.py           # Updated with logging
│   └── .env.example               # Added LOGS_DIR configuration
├── frontend/
│   └── src/
│       ├── components/
│       │   └── LogsPanel.jsx      # React log viewer component
│       └── App.jsx                # Updated to include LogsPanel
└── LOGGING_README.md              # This file
```

## 🚀 Quick Start

### 1. Configure Logs Directory

Add to your `.env` file (or create it from `.env.example`):

```bash
LOGS_DIR=/Volumes/SD-128GB/PlantMonitor/logs
```

If not set, logs will be stored in `backend/logs/` by default.

### 2. Start the Backend

The logging system initializes automatically when you start the FastAPI server:

```bash
cd plant-monitor/backend
python app.py
```

You'll see:
```
📝 Logging initialized
📁 Logs directory: /Volumes/SD-128GB/PlantMonitor/logs
📊 Log files will be created per component with date suffix
```

### 3. Start the Serial Reader

```bash
cd plant-monitor/backend
python serial_reader.py
```

Logs will be written to both console and file.

### 4. View Logs in UI

Open the frontend dashboard:
```bash
cd plant-monitor/frontend
npm run dev
```

Navigate to `http://localhost:5173` and scroll to the **System Logs** section.

## 📊 Log File Structure

Logs are organized by component with daily rotation:

```
logs/
├── app_20260413.log              # Main FastAPI application
├── serial_reader_20260413.log    # Serial reader component
├── camera_20260413.log           # Camera/capture operations
├── yolo_20260413.log             # YOLO detection
├── vlm_20260413.log              # VLM analysis
├── database_20260413.log         # Database operations
└── api_20260413.log              # API routes
```

### Log Rotation

- **Max file size**: 10MB
- **Backup count**: 5 files
- **Naming**: `component_YYYYMMDD.log`

## 🔧 Using the Logging System

### In Python Code

```python
import logging_config

# Get a logger for your component
logger = logging_config.get_serial_logger()

# Log messages
logger.info("Serial port connected")
logger.warning("Temperature threshold exceeded")
logger.error("Failed to read sensor data", exc_info=True)
logger.debug("Raw data: {data}")
```

### Available Loggers

```python
from logging_config import (
    get_app_logger,        # Main application
    get_serial_logger,     # Serial reader
    get_camera_logger,     # Camera operations
    get_yolo_logger,       # YOLO detection
    get_vlm_logger,        # VLM analysis
    get_db_logger,         # Database operations
    get_api_logger,        # API routes
)
```

### Custom Logger

```python
import logging_config

logger = logging_config.setup_logger(
    name='my_component',
    level=logging.DEBUG,
    log_to_file=True,
    log_to_console=True
)
```

## 🌐 API Endpoints

### Get Latest Logs

```bash
GET /api/logs/latest?limit=100
```

Response:
```json
{
  "success": true,
  "count": 100,
  "lines": [
    "2026-04-13 15:30:45 | INFO     | serial_reader        | Serial port connected",
    "2026-04-13 15:30:46 | INFO     | serial_reader        | Temperature: 27.5°C"
  ],
  "logs_dir": "/Volumes/SD-128GB/PlantMonitor/logs"
}
```

### List Log Files

```bash
GET /api/logs/files
```

Response:
```json
{
  "success": true,
  "count": 5,
  "files": [
    {
      "name": "serial_reader_20260413.log",
      "size": 1024567,
      "modified": "2026-04-13T15:30:45",
      "path": "/Volumes/SD-128GB/PlantMonitor/logs/serial_reader_20260413.log"
    }
  ]
}
```

### Get Specific Log File

```bash
GET /api/logs/file/serial_reader_20260413.log?lines=50
```

Returns the last 50 lines of the specified log file as plain text.

### Get Log Statistics

```bash
GET /api/logs/stats
```

Response:
```json
{
  "success": true,
  "logs_dir": "/Volumes/SD-128GB/PlantMonitor/logs",
  "total_files": 7,
  "total_size_bytes": 5242880,
  "total_size_mb": 5.0,
  "oldest_file": "app_20260410.log",
  "newest_file": "serial_reader_20260413.log"
}
```

## 🎨 Frontend Log Viewer

The `LogsPanel` component provides:

- ✅ Auto-refresh every 5 seconds
- ✅ Pause/resume auto-refresh
- ✅ Manual refresh button
- ✅ Color-coded log levels (ERROR=red, WARNING=yellow, INFO=green, DEBUG=gray)
- ✅ Scrollable container (max 400px height)
- ✅ Monospace font for readability
- ✅ Last refresh timestamp
- ✅ Loading and error states

## 📝 Log Format

```
YYYY-MM-DD HH:MM:SS | LEVEL    | COMPONENT_NAME       | MESSAGE
```

Example:
```
2026-04-13 15:30:45 | INFO     | serial_reader        | Serial port connected
2026-04-13 15:30:46 | WARNING  | camera               | Low light detected
2026-04-13 15:30:47 | ERROR    | yolo                 | Model not found
```

## 🔍 What Gets Logged

### Serial Reader
- Serial port connection/disconnection
- Each incoming line from ESP32
- Parsed sensor data
- Touch events
- Database insert success/failure
- Snapshot triggers
- Video recording events
- Exceptions with full traceback

### FastAPI App
- Application startup
- Route registration
- API request received
- Request payload
- Database operations
- Response status
- Errors and exceptions

### Camera Operations
- Camera initialization
- Image capture
- Image save location
- Brightness/exposure settings
- Capture failures

### YOLO Detection
- Detection started
- Person detected (count)
- Bounding boxes saved
- Detection metadata
- Processing time
- Errors

### VLM Analysis
- Analysis started
- Model used
- Prompt sent
- Response received
- JSON parsing
- Analysis results
- Reliability scores
- Errors

## 🛠️ Troubleshooting

### Logs not appearing

1. Check logs directory exists:
```bash
ls -la /Volumes/SD-128GB/PlantMonitor/logs
```

2. Check permissions:
```bash
chmod 755 /Volumes/SD-128GB/PlantMonitor/logs
```

3. Verify environment variable:
```bash
echo $LOGS_DIR
```

### Frontend not showing logs

1. Check API is running:
```bash
curl http://localhost:8000/api/logs/latest
```

2. Check browser console for errors

3. Verify CORS is enabled in `app.py`

### Log files too large

Logs automatically rotate at 10MB. To manually clean up:

```bash
# Keep only last 7 days
find /Volumes/SD-128GB/PlantMonitor/logs -name "*.log*" -mtime +7 -delete
```

## 📈 Performance Impact

- **File I/O**: Minimal (buffered writes)
- **Memory**: ~1MB per logger
- **CPU**: Negligible (<1%)
- **Disk**: ~10-50MB per day (depends on activity)

## 🔐 Security

- Path traversal protection in file reading
- Logs directory validation
- Safe filename sanitization
- No sensitive data logged (passwords, tokens)

## 🎯 Best Practices

1. **Use appropriate log levels**:
   - DEBUG: Detailed diagnostic info
   - INFO: General informational messages
   - WARNING: Warning messages
   - ERROR: Error messages
   - CRITICAL: Critical errors

2. **Include context**:
   ```python
   logger.info(f"Sensor reading: {device_id} - {temp}°C")
   ```

3. **Log exceptions with traceback**:
   ```python
   try:
       # code
   except Exception as e:
       logger.error(f"Operation failed: {e}", exc_info=True)
   ```

4. **Don't log in tight loops**:
   ```python
   # Bad
   for i in range(1000):
       logger.debug(f"Processing {i}")
   
   # Good
   logger.info(f"Processing {len(items)} items")
   ```

## 📚 Additional Resources

- [Python logging documentation](https://docs.python.org/3/library/logging.html)
- [FastAPI logging](https://fastapi.tiangolo.com/tutorial/logging/)
- [React useEffect hook](https://react.dev/reference/react/useEffect)

## ✅ Verification Steps

After implementation, verify:

1. ✅ Logs directory created automatically
2. ✅ Log files appear with correct naming
3. ✅ Console shows log messages
4. ✅ Files contain formatted log entries
5. ✅ API endpoints return log data
6. ✅ Frontend displays logs
7. ✅ Auto-refresh works (every 5 seconds)
8. ✅ Color coding works (ERROR=red, etc.)
9. ✅ Manual refresh button works
10. ✅ Pause/resume works

## 🎉 Done!

Your Plant Monitor system now has comprehensive logging from ESP32 → Backend → Frontend!
