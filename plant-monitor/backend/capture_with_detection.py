#!/usr/bin/env python3
"""
Integrated capture pipeline with person detection
Captures image → runs YOLO detection → saves to database
"""

import json
import psycopg
from pathlib import Path
from datetime import datetime
from detect_person import process_image_for_person_detection
from capture_snapshot import capture_webcam_image, run_vlm

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": "5433",
    "dbname": "plantdb",
    "user": "plantuser",
    "password": "plantpass"
}

def connect_database():
    """Connect to TimescaleDB"""
    try:
        conn = psycopg.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def insert_snapshot_with_detection(conn, image_filename, sensor_data, detection_result, vlm_result=None, sensor_timestamp=None):
    """
    Insert snapshot with person detection metadata into database
    
    Args:
        conn: Database connection
        image_filename: Name of captured image file
        sensor_data: Dict with temperature_c, humidity_pct, led_state
        detection_result: Dict with metadata, json_path, boxed_image_path
        vlm_result: Optional VLM analysis result
        sensor_timestamp: Optional exact timestamp from sensor_readings
        
    Returns:
        bool: Success status
    """
    try:
        cur = conn.cursor()
        
        metadata = detection_result['metadata']
        boxed_image_path = Path(detection_result['boxed_image_path']).name if detection_result['boxed_image_path'] else None
        
        if sensor_timestamp:
            # Use exact timestamp from sensor_readings
            insert_query = """
            INSERT INTO plant_snapshots 
            (time, image_path, temperature_c, humidity_pct, led_state, vlm_result,
             person_detected, person_count, detection_metadata, boxed_image_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING time
            """
            
            cur.execute(insert_query, (
                sensor_timestamp,
                image_filename,
                sensor_data['temperature_c'],
                sensor_data['humidity_pct'],
                bool(sensor_data['led_state']),
                vlm_result,
                metadata['person_detected'],
                metadata['person_count'],
                json.dumps(metadata),
                boxed_image_path
            ))
        else:
            # Use NOW() for manual captures
            insert_query = """
            INSERT INTO plant_snapshots 
            (time, image_path, temperature_c, humidity_pct, led_state, vlm_result,
             person_detected, person_count, detection_metadata, boxed_image_path)
            VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING time
            """
            
            cur.execute(insert_query, (
                image_filename,
                sensor_data['temperature_c'],
                sensor_data['humidity_pct'],
                bool(sensor_data['led_state']),
                vlm_result,
                metadata['person_detected'],
                metadata['person_count'],
                json.dumps(metadata),
                boxed_image_path
            ))
        
        timestamp = cur.fetchone()[0]
        conn.commit()
        cur.close()
        
        print(f"✓ Snapshot with detection saved to database: {timestamp}")
        return True
        
    except Exception as e:
        print(f"❌ Database insert failed: {e}")
        conn.rollback()
        return False

def capture_and_detect(sensor_data=None, db_conn=None, sensor_timestamp=None):
    """
    Complete pipeline: capture → detect people → save to database
    
    Args:
        sensor_data: Optional sensor data dict
        db_conn: Optional existing database connection
        sensor_timestamp: Optional exact timestamp from sensor_readings
        
    Returns:
        bool: Success status
    """
    print("\n🌱 Starting capture with person detection...")
    
    # Use provided connection or create new one
    close_conn = False
    if db_conn is None:
        db_conn = connect_database()
        if not db_conn:
            return False
        close_conn = True
    
    try:
        # Step 1: Capture webcam image
        image_filename = capture_webcam_image()
        if not image_filename:
            return False
        
        # Get full image path
        from capture_snapshot import IMAGES_DIR
        image_path = str(IMAGES_DIR / image_filename)
        
        # Step 2: Run person detection
        detection_result = process_image_for_person_detection(image_path)
        
        # Step 3: Decide on VLM analysis
        # FUTURE HOOK: Skip VLM if person detected
        vlm_result = None
        if detection_result['metadata']['person_detected']:
            print("⚠️  Person detected - skipping plant VLM analysis")
            vlm_result = "Skipped: Person detected in frame"
        else:
            print("✓ No person detected - ready for plant VLM analysis")
            vlm_result = run_vlm(image_path)  # Placeholder for now
        
        # Step 4: Get sensor data if not provided
        if sensor_data is None:
            from capture_snapshot import get_latest_sensor_data
            sensor_data = get_latest_sensor_data(db_conn)
            if not sensor_data:
                print("⚠️  Using default sensor values")
                sensor_data = {
                    'temperature_c': 0.0,
                    'humidity_pct': 0.0,
                    'led_state': False
                }
        
        # Step 5: Insert to database
        success = insert_snapshot_with_detection(
            db_conn, 
            image_filename, 
            sensor_data, 
            detection_result, 
            vlm_result,
            sensor_timestamp
        )
        
        if success:
            print(f"\n✅ Capture with detection complete!")
            print(f"   📸 Image: {image_filename}")
            print(f"   🖼️  Boxed: {Path(detection_result['boxed_image_path']).name if detection_result['boxed_image_path'] else 'N/A'}")
            print(f"   👤 Person detected: {detection_result['metadata']['person_detected']}")
            print(f"   👥 Person count: {detection_result['metadata']['person_count']}")
            print(f"   🌡️  Temp: {sensor_data['temperature_c']}°C")
            print(f"   💧 Humidity: {sensor_data['humidity_pct']}%")
            print(f"   💡 LED: {'ON' if sensor_data['led_state'] else 'OFF'}")
            print(f"   🤖 VLM: {vlm_result}")
        
        return success
        
    finally:
        if close_conn:
            db_conn.close()

if __name__ == "__main__":
    # Test the integrated pipeline
    capture_and_detect()
