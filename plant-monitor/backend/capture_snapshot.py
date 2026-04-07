#!/usr/bin/env python3
"""
Webcam snapshot capture for plant monitoring system
Captures image, fetches latest sensor data, and stores in TimescaleDB
"""
import os
import cv2
import json
from pathlib import Path
from datetime import datetime
import psycopg
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': '5433',
    'database': 'plantdb',
    'user': 'plantuser',
    'password': 'plantpass'
}

# Image storage configuration
IMAGES_DIR = Path(os.getenv('IMAGES_DIR', str(Path(__file__).parent / "images")))
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Camera settings (configurable via environment variables)
CAMERA_AUTO_EXPOSURE = int(os.getenv('CAMERA_AUTO_EXPOSURE', '1'))  # 1=manual, 3=auto
CAMERA_EXPOSURE = int(os.getenv('CAMERA_EXPOSURE', '-6'))  # Range: -13 (darkest) to -1 (brightest)
CAMERA_BRIGHTNESS = int(os.getenv('CAMERA_BRIGHTNESS', '128'))  # Range: 0-255
CAMERA_CONTRAST = int(os.getenv('CAMERA_CONTRAST', '32'))  # Range: 0-100
CAMERA_WARMUP_TIME = float(os.getenv('CAMERA_WARMUP_TIME', '0.5'))  # Seconds to wait after setting properties

# Image compression settings
IMAGE_JPEG_QUALITY = int(os.getenv('IMAGE_JPEG_QUALITY', '85'))  # 0-100, higher = better quality but larger file

def connect_database():
    """Connect to TimescaleDB"""
    try:
        conn = psycopg.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

def capture_webcam_image():
    """Capture image from webcam (device 0)"""
    try:
        # Initialize webcam
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ Cannot open webcam")
            return None
        
        # Set camera properties (configurable via environment variables)
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, CAMERA_AUTO_EXPOSURE)
        cap.set(cv2.CAP_PROP_EXPOSURE, CAMERA_EXPOSURE)
        cap.set(cv2.CAP_PROP_BRIGHTNESS, CAMERA_BRIGHTNESS)
        cap.set(cv2.CAP_PROP_CONTRAST, CAMERA_CONTRAST)
        
        # Allow camera to adjust
        import time
        time.sleep(CAMERA_WARMUP_TIME)
        
        # Capture frame
        ret, frame = cap.read()
        
        # Release webcam
        cap.release()
        
        if not ret:
            print("❌ Failed to capture image")
            return None
        
        # Generate timestamp-based filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"plant_{timestamp}.jpg"
        filepath = IMAGES_DIR / filename
        
        # Save image with JPEG compression
        cv2.imwrite(str(filepath), frame, [cv2.IMWRITE_JPEG_QUALITY, IMAGE_JPEG_QUALITY])
        
        # Show file size
        file_size_kb = filepath.stat().st_size / 1024
        print(f"📸 Image captured: {filename} ({file_size_kb:.1f} KB)")
        
        return filename
        
    except Exception as e:
        print(f"❌ Webcam capture failed: {e}")
        return None

def get_latest_sensor_data(conn):
    """Fetch latest sensor reading from database"""
    try:
        cur = conn.cursor()
        
        query = """
        SELECT temperature_c, humidity_pct, led_state
        FROM sensor_readings
        ORDER BY time DESC
        LIMIT 1
        """
        
        cur.execute(query)
        row = cur.fetchone()
        cur.close()
        
        if not row:
            print("⚠️  No sensor data found")
            return None
        
        return {
            'temperature_c': row[0],
            'humidity_pct': row[1],
            'led_state': bool(row[2])
        }
        
    except Exception as e:
        print(f"❌ Failed to fetch sensor data: {e}")
        return None

def run_vlm(image_path):
    """
    Placeholder for future VLM (Vision Language Model) integration
    This will be used to analyze plant health using AI
    """
    return "Not analyzed yet"

def insert_snapshot(conn, image_path, sensor_data, vlm_result, sensor_timestamp=None):
    """Insert snapshot metadata into plant_snapshots table"""
    try:
        cur = conn.cursor()
        
        if sensor_timestamp:
            # Use the exact timestamp from sensor_readings table
            insert_query = """
            INSERT INTO plant_snapshots 
            (time, image_path, temperature_c, humidity_pct, led_state, vlm_result)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING time
            """
            
            cur.execute(insert_query, (
                sensor_timestamp,
                image_path,
                sensor_data['temperature_c'],
                sensor_data['humidity_pct'],
                bool(sensor_data['led_state']),
                vlm_result
            ))
        else:
            # Use NOW() for manual captures
            insert_query = """
            INSERT INTO plant_snapshots 
            (time, image_path, temperature_c, humidity_pct, led_state, vlm_result)
            VALUES (NOW(), %s, %s, %s, %s, %s)
            RETURNING time
            """
            
            cur.execute(insert_query, (
                image_path,
                sensor_data['temperature_c'],
                sensor_data['humidity_pct'],
                bool(sensor_data['led_state']),
                vlm_result
            ))
        
        timestamp = cur.fetchone()[0]
        conn.commit()
        cur.close()
        
        print(f"✓ Snapshot saved to database: {timestamp}")
        return True
        
    except Exception as e:
        print(f"❌ Database insert failed: {e}")
        conn.rollback()
        return False

def capture_snapshot_with_data_and_conn(sensor_data, db_conn):
    """Capture snapshot with provided sensor data and db connection (for temperature-triggered captures)"""
    print("\n🌱 Starting plant snapshot capture...")
    
    try:
        # Get the exact timestamp from the most recent sensor_readings insert
        cur = db_conn.cursor()
        cur.execute("SELECT time FROM sensor_readings ORDER BY time DESC LIMIT 1")
        sensor_timestamp = cur.fetchone()[0]
        cur.close()
        
        # Capture webcam image
        image_filename = capture_webcam_image()
        if not image_filename:
            return False
        
        # Run VLM analysis (placeholder for now)
        image_path = str(IMAGES_DIR / image_filename)
        vlm_result = run_vlm(image_path)
        
        # Insert snapshot metadata with exact sensor timestamp
        success = insert_snapshot(db_conn, image_filename, sensor_data, vlm_result, sensor_timestamp)
        
        if success:
            print(f"✅ Snapshot complete!")
            print(f"   📸 Image: {image_filename}")
            print(f"   ⏰ Time: {sensor_timestamp}")
            print(f"   🌡️  Temp: {sensor_data['temperature_c']}°C")
            print(f"   💧 Humidity: {sensor_data['humidity_pct']}%")
            print(f"   💡 LED: {'ON' if sensor_data['led_state'] else 'OFF'}")
            print(f"   🤖 VLM: {vlm_result}")
        
        return success
        
    except Exception as e:
        print(f"❌ Snapshot capture failed: {e}")
        return False

def capture_snapshot_with_data(sensor_data):
    """Capture snapshot with provided sensor data (for temperature-triggered captures)"""
    print("\n🌱 Starting plant snapshot capture...")
    
    # Connect to database
    db_conn = connect_database()
    if not db_conn:
        return False
    
    try:
        # Capture webcam image
        image_filename = capture_webcam_image()
        if not image_filename:
            return False
        
        # Run VLM analysis (placeholder for now)
        image_path = str(IMAGES_DIR / image_filename)
        vlm_result = run_vlm(image_path)
        
        # Insert snapshot metadata with provided sensor data
        success = insert_snapshot(db_conn, image_filename, sensor_data, vlm_result)
        
        if success:
            print(f"✅ Snapshot complete!")
            print(f"   📸 Image: {image_filename}")
            print(f"   🌡️  Temp: {sensor_data['temperature_c']}°C")
            print(f"   💧 Humidity: {sensor_data['humidity_pct']}%")
            print(f"   💡 LED: {'ON' if sensor_data['led_state'] else 'OFF'}")
            print(f"   🤖 VLM: {vlm_result}")
        
        return success
        
    finally:
        db_conn.close()

def capture_and_store_snapshot():
    """Main function to capture snapshot and store metadata (fetches latest sensor data)"""
    print("\n🌱 Starting plant snapshot capture...")
    
    # Connect to database
    db_conn = connect_database()
    if not db_conn:
        return False
    
    try:
        # Capture webcam image
        image_filename = capture_webcam_image()
        if not image_filename:
            return False
        
        # Get latest sensor data
        sensor_data = get_latest_sensor_data(db_conn)
        if not sensor_data:
            print("⚠️  Using default sensor values")
            sensor_data = {
                'temperature_c': 0.0,
                'humidity_pct': 0.0,
                'led_state': False
            }
        
        # Run VLM analysis (placeholder for now)
        image_path = str(IMAGES_DIR / image_filename)
        vlm_result = run_vlm(image_path)
        
        # Insert snapshot metadata
        success = insert_snapshot(db_conn, image_filename, sensor_data, vlm_result)
        
        if success:
            print(f"✅ Snapshot complete!")
            print(f"   📸 Image: {image_filename}")
            print(f"   🌡️  Temp: {sensor_data['temperature_c']}°C")
            print(f"   💧 Humidity: {sensor_data['humidity_pct']}%")
            print(f"   💡 LED: {'ON' if sensor_data['led_state'] else 'OFF'}")
            print(f"   🤖 VLM: {vlm_result}")
        
        return success
        
    finally:
        db_conn.close()

if __name__ == "__main__":
    capture_and_store_snapshot()
