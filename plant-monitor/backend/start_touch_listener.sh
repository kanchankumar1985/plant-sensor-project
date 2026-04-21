#!/bin/bash

# Quick start script for touch sensor listener
# Usage: ./start_touch_listener.sh

echo "🌱 Starting Touch Sensor Listener..."
echo ""

# Activate virtual environment
source "/Users/kanchan/Plant Sensor Project/.venv/bin/activate"

# Navigate to backend directory
cd "/Users/kanchan/Plant Sensor Project/plant-monitor/backend"

# Check if pyttsx3 is installed
if ! python -c "import pyttsx3" 2>/dev/null; then
    echo "⚠️  pyttsx3 not found. Installing..."
    pip install pyttsx3==2.90
fi

# Check if pyserial is installed
if ! python -c "import serial" 2>/dev/null; then
    echo "⚠️  pyserial not found. Installing..."
    pip install pyserial==3.5
fi

echo ""
echo "✓ Dependencies ready"
echo ""

# Start listener
python serial_touch_listener.py "$@"
