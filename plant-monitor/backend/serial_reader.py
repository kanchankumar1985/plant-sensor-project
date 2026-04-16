#!/usr/bin/env python3
"""
Serial reader for ESP32 plant sensor data
Reads JSON data from USB serial and stores in TimescaleDB
Triggers webcam snapshot when temperature exceeds threshold
"""

import serial
import json
import time
import psycopg
from datetime import datetime
import os
from dotenv import load_dotenv
from pathlib import Path
import sys
import threading

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

load_dotenv()

# Use centralized logging system
import logging_config
logger = logging_config.get_serial_logger()

# Helper function to log and print
def log_print(message, level='info'):
    """Log message to file and print to console"""
    if level == 'info':
        logger.info(message)
    elif level == 'warning':
        logger.warning(message)
    elif level == 'error':
        logger.error(message)
    elif level == 'debug':
        logger.debug(message)

# Serial configuration
SERIAL_PORT = '/dev/cu.usbserial-0001'
BAUD_RATE = 115200

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': '5433',
    'dbname': 'plantdb',
    'user': 'plantuser',
    'password': 'plantpass'
}

# Temperature threshold for auto-snapshot
TEMP_THRESHOLD = 25.0  # Capture snapshot when temp >= 25°C
last_snapshot_time = None
SNAPSHOT_COOLDOWN = int(os.getenv('SNAPSHOT_COOLDOWN', '30'))  # Configurable cooldown between auto-snapshots

# Sensor health tracking
last_valid_read_ts = 0.0
last_sensor_warn_ts = 0.0

def connect_database():
    """Connect to TimescaleDB"""
    try:
        conn = psycopg.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        log_print(f"Database connection failed: {e}", 'error')
        return None

def connect_serial():
    """Connect to ESP32 serial port"""
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        log_print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud")
        return ser
    except Exception as e:
        log_print(f"Serial connection failed: {e}", 'error')
        return None

def parse_sensor_data(line):
    """Parse JSON sensor data from serial line"""
    try:
        # Clean the line
        line = line.strip()
        if not line.startswith('{'):
            return None
            
        data = json.loads(line)
        
        # Validate required fields
        required_fields = ['device_id', 'temperature_c', 'humidity_pct']
        if all(key in data for key in required_fields):
            # LED state is optional, default to 0 if not present
            if 'led_state' not in data:
                data['led_state'] = 0
            return data
        return None
        
    except json.JSONDecodeError:
        return None
    except Exception as e:
        log_print(f"Parse error: {e}", 'error')
        return None

def insert_touch_event(conn, state, device_id='plant-esp32-01'):
    """Insert touch event into TimescaleDB and trigger video on TOUCHED"""
    try:
        cur = conn.cursor()
        
        insert_query = """
        INSERT INTO touch_events (device_id, state, timestamp)
        VALUES (%s, %s, NOW())
        """
        
        cur.execute(insert_query, (device_id, state))
        conn.commit()
        cur.close()
        
        emoji = "👆" if state == "TOUCHED" else "🖐️"
        log_print(f"{emoji} Touch: {state}")
        
        # Trigger video capture when touched (pass db connection)
        if state == "TOUCHED":
            trigger_touch_video_capture(conn)
        
        return True
        
    except Exception as e:
        log_print(f"Touch event insert failed: {e}", 'error')
        conn.rollback()
        return False

def record_video_in_background(db_conn, snapshot_time):
    """Background thread function to record video without blocking serial reader"""
    try:
        from capture_video import record_video_alert
        import sys
        
        log_print("🎥 Recording video in background...")
        video_filename = record_video_alert()
        
        if video_filename:
            log_print(f"✅ Video saved: {video_filename}")
            
            # Link video to the specific snapshot created for this touch event
            try:
                cur = db_conn.cursor()
                
                # Update the snapshot with video_path using the exact snapshot time
                cur.execute("""
                    UPDATE plant_snapshots 
                    SET video_path = %s 
                    WHERE time = %s
                    RETURNING image_path
                """, (video_filename, snapshot_time))
                
                result = cur.fetchone()
                db_conn.commit()
                
                if result:
                    image_path = result[0]
                    log_print(f"🔗 Video linked to snapshot: {image_path}")
                else:
                    log_print(f"⚠️  Snapshot not found for time: {snapshot_time}", 'warning')
                
                cur.close()
                
            except Exception as e:
                log_print(f"⚠️  Failed to link video to snapshot: {e}", 'error')
                db_conn.rollback()
        else:
            log_print("❌ Video capture failed", 'error')
            
    except Exception as e:
        log_print(f"❌ Video capture error: {e}", 'error')

def trigger_touch_video_capture(db_conn):
    """Trigger snapshot and video capture when touch sensor is activated"""
    log_print(f"\n👆 TOUCH DETECTED!")
    log_print("📸 Capturing snapshot for touch event...")
    
    try:
        # Capture snapshot immediately for this touch event
        from capture_with_vlm import capture_and_analyze
        from capture_snapshot import get_latest_sensor_data
        
        # Get current sensor data
        sensor_data = get_latest_sensor_data(db_conn)
        if not sensor_data:
            log_print("⚠️  Using default sensor values", 'warning')
            sensor_data = {
                'temperature_c': 0.0,
                'humidity_pct': 0.0,
                'led_state': False
            }
        
        # Capture snapshot with VLM analysis (this returns the snapshot timestamp)
        success = capture_and_analyze(sensor_data, db_conn)
        
        if success:
            # Get the timestamp of the snapshot we just created
            cur = db_conn.cursor()
            cur.execute("SELECT time FROM plant_snapshots ORDER BY time DESC LIMIT 1")
            snapshot_time = cur.fetchone()[0]
            cur.close()
            
            log_print(f"✅ Snapshot captured at: {snapshot_time}")
            log_print("🎥 Starting video recording (5s) in background thread...")
            
            # Start video recording in a separate thread, pass snapshot time
            video_thread = threading.Thread(
                target=record_video_in_background, 
                args=(db_conn, snapshot_time), 
                daemon=True
            )
            video_thread.start()
            
            log_print("✓ Video recording started (non-blocking)")
            log_print("📡 Continuing temperature monitoring...\n")
        else:
            log_print("❌ Snapshot capture failed, skipping video", 'error')
            
    except Exception as e:
        log_print(f"❌ Touch snapshot/video error: {e}", 'error')

def trigger_snapshot_if_needed(sensor_data, db_conn):
    """Trigger webcam snapshot with VLM analysis if temperature exceeds threshold"""
    global last_snapshot_time
    
    temperature = sensor_data['temperature_c']
    
    if temperature < TEMP_THRESHOLD:
        return False
    
    # Check cooldown period
    current_time = time.time()
    if last_snapshot_time is not None:
        time_since_last = current_time - last_snapshot_time
        if time_since_last < SNAPSHOT_COOLDOWN:
            return False
    
    # Trigger snapshot with VLM analysis
    try:
        from capture_with_vlm import capture_and_analyze
        
        log_print(f"\n🔥 TEMPERATURE ALERT: {temperature}°C > {TEMP_THRESHOLD}°C")
        log_print("📸 Triggering automatic snapshot with VLM analysis...")
        
        # Get exact timestamp from most recent sensor reading
        cur = db_conn.cursor()
        cur.execute("SELECT time FROM sensor_readings ORDER BY time DESC LIMIT 1")
        sensor_timestamp = cur.fetchone()[0]
        cur.close()
        
        success = capture_and_analyze(sensor_data, db_conn, sensor_timestamp)
        
        if success:
            last_snapshot_time = current_time
            log_print(f"✅ Auto-snapshot with detection captured successfully!")
            log_print(f"⏳ Next auto-snapshot available in {SNAPSHOT_COOLDOWN} seconds\n")
            return True
        else:
            log_print("❌ Auto-snapshot failed\n", 'error')
            return False
            
    except ImportError as e:
        log_print(f"⚠️  VLM analysis not available: {e}", 'warning')
        log_print("💡 Install required packages: ultralytics, torch, Pillow, requests", 'warning')
        log_print("⏭️  Skipping auto-snapshot (sensor data still recorded)\n", 'warning')
        return False
    except Exception as e:
        log_print(f"❌ Snapshot trigger error: {e}\n", 'error')
        return False

def insert_sensor_data(conn, data):
    """Insert sensor data into TimescaleDB"""
    try:
        cur = conn.cursor()
        
        insert_query = """
        INSERT INTO sensor_readings (time, device_id, temperature_c, humidity_pct, led_state)
        VALUES (NOW(), %s, %s, %s, %s)
        """
        
        cur.execute(insert_query, (
            data['device_id'],
            data['temperature_c'],
            data['humidity_pct'],
            data['led_state']
        ))
        
        conn.commit()
        cur.close()
        
        led_status = "ON" if data['led_state'] == 1 else "OFF"
        log_print(f"✓ Inserted: {data['device_id']} - {data['temperature_c']}°C, {data['humidity_pct']}%, LED: {led_status}")
        
        # Update last valid sensor timestamp
        global last_valid_read_ts
        last_valid_read_ts = time.time()
        
        # Check if we should trigger snapshot (pass full sensor data and db connection)
        trigger_snapshot_if_needed(data, conn)
        
        return True
        
    except Exception as e:
        log_print(f"Database insert failed: {e}", 'error')
        conn.rollback()
        return False

def main():
    """Main serial reader loop"""
    log_print("🌱 Plant Sensor Serial Reader Starting...")
    log_print(f"📝 Logging to: {logging_config.LOGS_PATH}")
    log_print(f"🌡️  Temperature threshold: {TEMP_THRESHOLD}°C")
    log_print(f"📸 Auto-snapshot: Enabled (cooldown: {SNAPSHOT_COOLDOWN} sec)")
    
    # Connect to database
    db_conn = connect_database()
    if not db_conn:
        log_print("❌ Cannot connect to database. Exiting.", 'error')
        return
    
    # Connect to serial port
    ser = connect_serial()
    if not ser:
        log_print("❌ Cannot connect to serial port. Exiting.", 'error')
        return
    
    log_print("🚀 Serial reader running. Press Ctrl+C to stop.")
    
    # Flush initial garbage data
    time.sleep(2)
    ser.reset_input_buffer()
    
    try:
        while True:
            try:
                # Read line from serial
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                
                if line:
                    # Handle touch events
                    if line.startswith('TOUCH_EVENT:'):
                        state = line.split(':', 1)[1]
                        insert_touch_event(db_conn, state)
                        continue
                    
                    # Log raw line for debugging (only first 100 chars)
                    if line.startswith('READY') or line.startswith('ERROR') or line.startswith('INFO') or line.startswith('DEBUG'):
                        log_print(f"📟 {line}")
                        continue
                    
                    # Only process lines that look like JSON
                    if line.startswith('{') and line.endswith('}'):
                        # Parse sensor data
                        sensor_data = parse_sensor_data(line)
                        
                        if sensor_data:
                            # Insert into database
                            insert_sensor_data(db_conn, sensor_data)
                        else:
                            # It might be a touch-only payload; log for visibility
                            try:
                                data = json.loads(line)
                                if isinstance(data, dict) and 'touch_state' in data and ('temperature_c' not in data or 'humidity_pct' not in data):
                                    log_print("ℹ️ Touch-only payload received (no temperature/humidity); skipping sensor_readings insert")
                            except Exception:
                                pass
                    elif line and len(line) < 200:
                        # Log non-JSON lines for debugging (truncated)
                        log_print(f"📟 {line[:100]}")
                    
                    # Sensor health warning if no valid inserts for a while
                    now = time.time()
                    global last_sensor_warn_ts, last_valid_read_ts
                    if last_valid_read_ts == 0.0:
                        last_valid_read_ts = now
                    elif (now - last_valid_read_ts) > 30 and (now - last_sensor_warn_ts) > 30:
                        delta = int(now - last_valid_read_ts)
                        log_print(f"⚠️  No valid temperature readings inserted in the last {delta}s. Sensor may be offline; firmware will auto-retry.", 'warning')
                        last_sensor_warn_ts = now
                
            except UnicodeDecodeError:
                continue
            except Exception as e:
                log_print(f"Error in main loop: {e}", 'error')
                time.sleep(1)
                
    except KeyboardInterrupt:
        log_print("\n🛑 Stopping serial reader...")
    
    finally:
        if ser:
            ser.close()
        if db_conn:
            db_conn.close()
        log_print("✅ Serial reader stopped.")
        log_print(f"📝 Log saved to: {logging_config.LOGS_PATH}")

if __name__ == "__main__":
    main()
