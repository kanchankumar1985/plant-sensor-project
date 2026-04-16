#!/bin/bash

# Start serial reader with logging
# Logs are saved to logs/ directory with timestamps

# Create logs directory if it doesn't exist
LOGS_DIR="/Users/kanchan/Plant Sensor Project/plant-monitor/backend/logs"
mkdir -p "$LOGS_DIR"

# Generate log filename with timestamp
LOG_FILE="$LOGS_DIR/serial_reader_$(date +%Y%m%d_%H%M%S).log"

# Activate virtual environment
source /Users/kanchan/Plant\ Sensor\ Project/.venv/bin/activate

echo "🌱 Starting Plant Sensor Serial Reader..."
echo "📝 Logging to: $LOG_FILE"
echo "🛑 Press Ctrl+C to stop"
echo ""

# Run serial_reader.py with timestamped logging
# Both stdout and stderr are captured
python serial_reader.py 2>&1 | while IFS= read -r line; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $line" | tee -a "$LOG_FILE"
done

echo ""
echo "✅ Serial reader stopped"
echo "📝 Log saved to: $LOG_FILE"
