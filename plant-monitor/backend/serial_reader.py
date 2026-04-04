#!/usr/bin/env python3
"""
Serial reader for ESP32 plant sensor data
Reads JSON data from USB serial and stores in TimescaleDB
"""

import serial
import json
import time
import psycopg2
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Serial configuration
SERIAL_PORT = '/dev/cu.usbserial-0001'
BAUD_RATE = 115200

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': '5433',
    'database': 'plantdb',
    'user': 'plantuser',
    'password': 'plantpass'
}

def connect_database():
    """Connect to TimescaleDB"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
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
        if all(key in data for key in ['device_id', 'temperature_c', 'humidity_pct']):
            return data
        return None
        
    except json.JSONDecodeError:
        return None
    except Exception as e:
        print(f"Parse error: {e}")
        return None

def insert_sensor_data(conn, data):
    """Insert sensor data into TimescaleDB"""
    try:
        cur = conn.cursor()
        
        insert_query = """
        INSERT INTO sensor_readings (time, device_id, temperature_c, humidity_pct)
        VALUES (NOW(), %s, %s, %s)
        """
        
        cur.execute(insert_query, (
            data['device_id'],
            data['temperature_c'],
            data['humidity_pct']
        ))
        
        conn.commit()
        cur.close()
        
        print(f"✓ Inserted: {data['device_id']} - {data['temperature_c']}°C, {data['humidity_pct']}%")
        return True
        
    except Exception as e:
        print(f"Database insert failed: {e}")
        conn.rollback()
        return False

def main():
    """Main serial reader loop"""
    print("🌱 Plant Sensor Serial Reader Starting...")
    
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
