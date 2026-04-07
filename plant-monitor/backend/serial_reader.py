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

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

load_dotenv()

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
SNAPSHOT_COOLDOWN = 20  # Wait 60 seconds (1 minute) between auto-snapshots

def connect_database():
    """Connect to TimescaleDB"""
    try:
        conn = psycopg.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

def connect_serial():
    """Connect to ESP32 serial port"""
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud")
        return ser
    except Exception as e:
        print(f"Serial connection failed: {e}")
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
        print(f"Parse error: {e}")
        return None

def trigger_snapshot_if_needed(sensor_data, db_conn):
    """Trigger webcam snapshot with person detection if temperature exceeds threshold"""
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
    
    # Trigger snapshot with person detection
    try:
        from capture_with_detection import capture_and_detect
        
        print(f"\n🔥 TEMPERATURE ALERT: {temperature}°C > {TEMP_THRESHOLD}°C")
        print("📸 Triggering automatic snapshot with person detection...")
        
        # Get exact timestamp from most recent sensor reading
        cur = db_conn.cursor()
        cur.execute("SELECT time FROM sensor_readings ORDER BY time DESC LIMIT 1")
        sensor_timestamp = cur.fetchone()[0]
        cur.close()
        
        success = capture_and_detect(sensor_data, db_conn, sensor_timestamp)
        
        if success:
            last_snapshot_time = current_time
            print(f"✅ Auto-snapshot with detection captured successfully!")
            print(f"⏳ Next auto-snapshot available in {SNAPSHOT_COOLDOWN//60} minutes\n")
            return True
        else:
            print("❌ Auto-snapshot failed\n")
            return False
            
    except Exception as e:
        print(f"❌ Snapshot trigger error: {e}\n")
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
        print(f"✓ Inserted: {data['device_id']} - {data['temperature_c']}°C, {data['humidity_pct']}%, LED: {led_status}")
        
        # Check if we should trigger snapshot (pass full sensor data and db connection)
        trigger_snapshot_if_needed(data, conn)
        
        return True
        
    except Exception as e:
        print(f"Database insert failed: {e}")
        conn.rollback()
        return False

def main():
    """Main serial reader loop"""
    print("🌱 Plant Sensor Serial Reader Starting...")
    print(f"🌡️  Temperature threshold: {TEMP_THRESHOLD}°C")
    print(f"📸 Auto-snapshot: Enabled (cooldown: {SNAPSHOT_COOLDOWN//60} min)")
    
    # Connect to database
    db_conn = connect_database()
    if not db_conn:
        print("❌ Cannot connect to database. Exiting.")
        return
    
    # Connect to serial port
    ser = connect_serial()
    if not ser:
        print("❌ Cannot connect to serial port. Exiting.")
        return
    
    print("🚀 Serial reader running. Press Ctrl+C to stop.")
    
    try:
        while True:
            try:
                # Read line from serial
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                
                if line:
                    # Print raw line for debugging
                    if line.startswith('READY') or line.startswith('ERROR'):
                        print(f"📟 {line}")
                        continue
                    
                    # Parse sensor data
                    sensor_data = parse_sensor_data(line)
                    
                    if sensor_data:
                        # Insert into database
                        insert_sensor_data(db_conn, sensor_data)
                    elif line and not line.startswith('{'):
                        print(f"📟 {line}")
                
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\n🛑 Stopping serial reader...")
    
    finally:
        if ser:
            ser.close()
        if db_conn:
            db_conn.close()
        print("✅ Serial reader stopped.")

if __name__ == "__main__":
    main()
