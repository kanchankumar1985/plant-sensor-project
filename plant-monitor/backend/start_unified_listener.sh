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
