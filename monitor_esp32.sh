#!/bin/bash
# ESP32 Serial Monitor Script
# Usage: ./monitor_esp32.sh

PORT="/dev/cu.usbserial-0001"
BAUD=115200

echo "=========================================="
echo "ESP32 Serial Monitor"
echo "Port: $PORT"
echo "Baud: $BAUD"
echo "Press Ctrl+C to exit"
echo "=========================================="
echo ""

# Check if port exists
if [ ! -e "$PORT" ]; then
    echo "Error: Port $PORT not found"
    echo "Available ports:"
    ls -1 /dev/cu.* 2>/dev/null
    exit 1
fi

# Kill any existing processes using the port
lsof 2>/dev/null | grep "$PORT" | awk '{print $2}' | xargs kill -9 2>/dev/null

# Use screen to monitor serial output
# -L = log to file
# -Logfile = specify log file location
screen -L -Logfile ~/esp32_serial.log "$PORT" $BAUD
