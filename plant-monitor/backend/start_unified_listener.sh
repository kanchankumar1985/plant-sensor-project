#!/bin/bash

# Unified Serial Listener Startup Script
# This script starts the unified serial listener that handles:
# - Temperature/Humidity monitoring
# - Touch event detection with TTS
# - Auto-snapshot on temperature threshold
# - Complete workflow triggering

cd "$(dirname "$0")"

echo "🌱 Starting Unified Serial Listener..."
echo ""

SCRIPT_DIR="$(pwd)"
SD_ROOT="/Volumes/SD-128GB/PlantMonitor"

if [ -d "$SD_ROOT" ] && [ -w "$SD_ROOT" ]; then
    export IMAGES_DIR="${IMAGES_DIR:-$SD_ROOT/images}"
    export VIDEOS_DIR="${VIDEOS_DIR:-$SD_ROOT/videos}"
    export LOGS_DIR="${LOGS_DIR:-$SD_ROOT/logs}"
else
    export IMAGES_DIR="${IMAGES_DIR:-$SCRIPT_DIR/images}"
    export VIDEOS_DIR="${VIDEOS_DIR:-$SCRIPT_DIR/videos}"
    export LOGS_DIR="${LOGS_DIR:-$SCRIPT_DIR/logs}"
fi

mkdir -p "$IMAGES_DIR" "$VIDEOS_DIR" "$LOGS_DIR"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "✓ Activating virtual environment..."
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "✓ Activating virtual environment..."
    source venv/bin/activate
elif [ -d "../venv" ]; then
    echo "✓ Activating virtual environment..."
    source ../venv/bin/activate
fi

# Run the unified listener
python3 serial_unified_listener.py
