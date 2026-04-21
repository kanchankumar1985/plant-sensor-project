#!/usr/bin/env python3
"""
Unified Serial Listener for Plant Monitor
Combines functionality of serial_reader.py and serial_touch_listener.py

Features:
- Reads temperature/humidity sensor data from ESP32
- Saves sensor data to TimescaleDB continuously
- Detects touch events and triggers TTS + workflow
- Auto-captures on temperature threshold
- Handles all serial communication in one place
"""

import serial
import serial.tools.list_ports
import json
import time
import psycopg
from datetime import datetime
from pathlib import Path
import sys
import os
from dotenv import load_dotenv

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

load_dotenv()

# Use centralized logging
from logging_config import get_serial_logger
logger = get_serial_logger()

# Import touch workflow
from services.touch_workflow import handle_touch_event, get_orchestrator

# Serial configuration
SERIAL_BAUD = 115200
SERIAL_TIMEOUT = 1.0
RECONNECT_DELAY = 5  # seconds

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': '5433',
    'dbname': 'plantdb',
    'user': 'plantuser',
    'password': 'plantpass'
}

# Temperature threshold for auto-snapshot
TEMP_THRESHOLD = 25.0
SNAPSHOT_COOLDOWN = int(os.getenv('SNAPSHOT_COOLDOWN', '30'))
last_snapshot_time = None

# Sensor health tracking
last_valid_read_ts = 0.0


def find_esp32_port():
    """Auto-detect ESP32 serial port"""
    ports = serial.tools.list_ports.comports()
    
    esp32_keywords = ['CP2102', 'CH340', 'USB-SERIAL', 'UART', 'ESP32']
    
    for port in ports:
        port_desc = (port.description or '').upper()
        port_hwid = (port.hwid or '').upper()
        
        for keyword in esp32_keywords:
            if keyword in port_desc or keyword in port_hwid:
                logger.info(f"✓ Found ESP32 port: {port.device} ({port.description})")
                return port.device
    
    if ports:
        logger.warning("ESP32 not auto-detected. Available ports:")
        for port in ports:
            logger.warning(f"  - {port.device}: {port.description}")
        return ports[0].device
    
    return None


def connect_database():
    """Connect to TimescaleDB"""
    try:
        conn = psycopg.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None


def connect_serial(port=None):
    """Connect to ESP32 serial port"""
    if port is None:
        port = find_esp32_port()
    
    if not port:
        logger.error("❌ No serial port found")
        return None
    
    try:
        logger.info(f"🔌 Connecting to {port} at {SERIAL_BAUD} baud...")
        ser = serial.Serial(port, SERIAL_BAUD, timeout=SERIAL_TIMEOUT)
        time.sleep(2)  # Wait for ESP32 to reset
        ser.reset_input_buffer()
        logger.info(f"✓ Connected to {port}")
        return ser
    except serial.SerialException as e:
        logger.error(f"❌ Serial connection failed: {e}")
        return None


def parse_sensor_data(line):
    """Parse JSON sensor data from serial line"""
    try:
        line = line.strip()
        if not line.startswith('{'):
            return None
        
        data = json.loads(line)
        
        # Validate required fields
        required_fields = ['device_id', 'temperature_c', 'humidity_pct']
        if all(key in data for key in required_fields):
            if 'led_state' not in data:
                data['led_state'] = 0
            return data
        return None
    except json.JSONDecodeError:
        return None


def insert_sensor_reading(conn, data):
    """Insert sensor reading into database"""
    try:
        cur = conn.cursor()
        insert_query = """
        INSERT INTO sensor_readings (time, device_id, temperature_c, humidity_pct, led_state)
        VALUES (NOW(), %s, %s, %s, %s)
        RETURNING time
        """
        cur.execute(insert_query, (
            data['device_id'],
            data['temperature_c'],
            data['humidity_pct'],
            data['led_state']
        ))
        timestamp = cur.fetchone()[0]
        conn.commit()
        cur.close()
        return timestamp
    except Exception as e:
        logger.error(f"Database insert failed: {e}")
        conn.rollback()
        return None


def check_temperature_threshold(temp):
    """Check if temperature exceeds threshold and trigger snapshot"""
    global last_snapshot_time
    
    if temp >= TEMP_THRESHOLD:
        current_time = time.time()
        
        # Check cooldown
        if last_snapshot_time is None or (current_time - last_snapshot_time) >= SNAPSHOT_COOLDOWN:
            logger.info(f"🔥 Temperature alert: {temp}°C >= {TEMP_THRESHOLD}°C")
            logger.info("📸 Triggering auto-snapshot...")
            
            try:
                from capture_with_vlm import capture_and_analyze
                db_conn = connect_database()
                if db_conn:
                    capture_and_analyze(db_conn=db_conn)
                    db_conn.close()
                last_snapshot_time = current_time
            except Exception as e:
                logger.error(f"Auto-snapshot failed: {e}")


def main_loop(port=None):
    """Main unified listener loop"""
    logger.info("=" * 60)
    logger.info("🌱 UNIFIED SERIAL LISTENER STARTED")
    logger.info("=" * 60)
    logger.info("Features:")
    logger.info("  • Temperature/Humidity monitoring")
    logger.info("  • Touch event detection with TTS")
    logger.info("  • Auto-snapshot on temperature threshold")
    logger.info("  • Complete workflow triggering")
    logger.info("=" * 60)
    logger.info("Press Ctrl+C to stop")
    logger.info("")
    
    ser = None
    db_conn = None
    last_reconnect_attempt = 0
    
    try:
        # Connect to database
        db_conn = connect_database()
        if not db_conn:
            logger.warning("⚠️  Database not available - running without DB")
        else:
            logger.info("✓ Database connected")
        
        while True:
            # Connect or reconnect serial
            if ser is None or not ser.is_open:
                current_time = time.time()
                if current_time - last_reconnect_attempt >= RECONNECT_DELAY:
                    ser = connect_serial(port)
                    last_reconnect_attempt = current_time
                    
                    if ser is None:
                        logger.warning(f"⏳ Retrying in {RECONNECT_DELAY} seconds...")
                        time.sleep(RECONNECT_DELAY)
                        continue
            
            try:
                # Read line from serial (blocking with timeout)
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                
                if not line:
                    continue
                
                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                
                # Check for TOUCHED event (highest priority)
                if line == "TOUCHED":
                    logger.info("")
                    logger.info("🖐️" * 20)
                    logger.info("TOUCH EVENT DETECTED!")
                    logger.info("🖐️" * 20)
                    logger.info("")
                    
                    # Set serial port in orchestrator for pump control
                    orchestrator = get_orchestrator()
                    orchestrator.set_serial_port(ser)
                    
                    # Trigger workflow (non-blocking - pump will trigger when YOLO completes)
                    handle_touch_event()
                    logger.info("✅ Workflow started (pump will trigger when person detected)")
                    logger.info("")
                    continue
                
                # Try to parse as sensor data JSON
                sensor_data = parse_sensor_data(line)
                
                if sensor_data:
                    # Determine LED state string
                    led_str = "ON" if sensor_data['led_state'] == 1 else "OFF"
                    
                    # Save to database first
                    if db_conn:
                        timestamp_str = insert_sensor_reading(db_conn, sensor_data)
                        if timestamp_str:
                            logger.info(f"✓ Inserted: {sensor_data['device_id']} - "
                                      f"{sensor_data['temperature_c']:.2f}°C, "
                                      f"{sensor_data['humidity_pct']:.2f}%, "
                                      f"LED: {led_str}")
                    else:
                        # Just log if no DB
                        logger.info(f"📊 Temp: {sensor_data['temperature_c']:.2f}°C, "
                                  f"Humidity: {sensor_data['humidity_pct']:.2f}%, "
                                  f"LED: {led_str}")
                    
                    # DISABLED: Auto temperature threshold snapshot
                    # check_temperature_threshold(sensor_data['temperature_c'])
                    
                    # Update health tracking
                    global last_valid_read_ts
                    last_valid_read_ts = time.time()
                
                else:
                    # Log other messages (DEBUG, touch sensor state, etc.)
                    # Filter out JSON fragments and only log complete, meaningful messages
                    if line and not line.startswith('{') and not line.endswith('}'):
                        # Only log lines that look like complete messages (start with known prefixes)
                        if line.startswith('DEBUG:') or line.startswith('INFO:') or line.startswith('ERROR:') or \
                           line.startswith('TOUCH') or line.startswith('✓') or line.startswith('❌'):
                            logger.info(f"{line}")
            
            except serial.SerialException as e:
                logger.error(f"❌ Serial read error: {e}")
                if ser:
                    ser.close()
                ser = None
                time.sleep(RECONNECT_DELAY)
            
            except UnicodeDecodeError as e:
                logger.warning(f"⚠️  Decode error: {e}")
                continue
    
    except KeyboardInterrupt:
        logger.info("")
        logger.info("=" * 60)
        logger.info("🛑 STOPPING UNIFIED LISTENER")
        logger.info("=" * 60)
        
        if ser and ser.is_open:
            ser.close()
            logger.info("✓ Serial port closed")
        
        if db_conn:
            db_conn.close()
            logger.info("✓ Database connection closed")
    
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}", exc_info=True)
        if ser and ser.is_open:
            ser.close()
        if db_conn:
            db_conn.close()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Unified Serial Listener for Plant Monitor')
    parser.add_argument('--port', type=str, help='Serial port (auto-detect if not specified)')
    parser.add_argument('--test-tts', action='store_true', help='Test TTS and exit')
    parser.add_argument('--test-workflow', action='store_true', help='Test workflow and exit')
    
    args = parser.parse_args()
    
    # Test TTS
    if args.test_tts:
        logger.info("Testing TTS...")
        from services.tts_service import get_tts_service
        tts = get_tts_service()
        tts.test()
        return
    
    # Test workflow
    if args.test_workflow:
        logger.info("Testing workflow...")
        handle_touch_event()
        time.sleep(15)
        orchestrator = get_orchestrator()
        status = orchestrator.get_status()
        logger.info(f"Workflow status: {status}")
        return
    
    # Start unified listener
    main_loop(port=args.port)


if __name__ == "__main__":
    main()
