#!/usr/bin/env python3
"""
Extended capture pipeline with VLM analysis
Integrates YOLO detection + VLM reasoning + intelligent rules
"""

import json
import psycopg
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import os
import time
from dotenv import load_dotenv

from detect_person import process_image_for_person_detection
from capture_snapshot import capture_webcam_image
from capture_video import record_video_alert
from vlm.vlm_analyzer import analyze_image_with_vlm, analyze_video_with_vlm
from vlm.analysis_rules import apply_analysis_rules, get_analysis_summary

# Use centralized logging
import logging_config
logger = logging_config.get_camera_logger()

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": "5433",
    "dbname": "plantdb",
    "user": "plantuser",
    "password": "plantpass"
}


# Load environment
load_dotenv()

# Fast-mode / sampling controls (env-configurable)
VLM_ENABLED_ENV = os.getenv('VLM_ENABLED', 'true').lower() in ('1', 'true', 'yes', 'y')
VLM_SAMPLE_EVERY_N = int(os.getenv('VLM_SAMPLE_EVERY_N', '1'))  # run on every Nth snapshot (1 = every)
VLM_COOLDOWN_SECONDS = int(os.getenv('VLM_COOLDOWN_SECONDS', '0'))  # min seconds between VLM runs
VLM_VIDEO_ENABLED = os.getenv('VLM_VIDEO_ENABLED', 'false').lower() in ('1', 'true', 'yes', 'y')
VLM_MAX_QUEUE = int(os.getenv('VLM_MAX_QUEUE', '3'))

# Internal gating state
_last_vlm_time: Optional[float] = None
_vlm_counter: int = 0


def _should_run_vlm() -> bool:
    """
    Decide whether to run VLM now based on env-configured sampling and cooldown.
    """
    global _last_vlm_time, _vlm_counter

    if not VLM_ENABLED_ENV:
        return False

    now = time.time()

    # Cooldown gate
    if VLM_COOLDOWN_SECONDS > 0 and _last_vlm_time is not None:
        if (now - _last_vlm_time) < VLM_COOLDOWN_SECONDS:
            return False

    # Sampling gate
    _vlm_counter += 1
    if VLM_SAMPLE_EVERY_N > 1 and (_vlm_counter % VLM_SAMPLE_EVERY_N) != 0:
        return False

    # Approve run; stamp time
    _last_vlm_time = now
    return True


def connect_database():
    """Connect to TimescaleDB"""
    try:
        conn = psycopg.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.info(f"❌ Database connection failed: {e}")
        return None

def get_queue_depth(conn) -> int:
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COUNT(*)
            FROM plant_snapshots
            WHERE analysis_status IN ('queued','processing')
            """
        )
        n = cur.fetchone()[0]
        cur.close()
        return int(n)
    except Exception:
        return 0

def get_last_completed_at(conn) -> Optional[datetime]:
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT MAX(analyzed_at)
            FROM plant_snapshots
            WHERE analyzed_at IS NOT NULL
            """
        )
        row = cur.fetchone()
        cur.close()
        return row[0]
    except Exception:
        return None

def insert_snapshot_quick(
    conn,
    image_filename: str,
    sensor_data: Dict[str, Any],
    yolo_result: Dict[str, Any],
    status: str,
    error: Optional[str],
    sensor_timestamp: Optional[datetime] = None,
    video_filename: Optional[str] = None,
    vlm_model: Optional[str] = None,
) -> bool:
    """Insert snapshot quickly with a pre-set analysis status (queued/skipped)."""
    try:
        cur = conn.cursor()
        yolo_metadata = yolo_result['metadata']
        boxed_image_path = Path(yolo_result['boxed_image_path']).name if yolo_result['boxed_image_path'] else None

        if sensor_timestamp:
            insert_query = """
            INSERT INTO plant_snapshots 
            (time, image_path, temperature_c, humidity_pct, led_state,
             person_detected, person_count, detection_metadata, boxed_image_path, video_path,
             vlm_summary, vlm_analysis, plant_visible, plant_occluded, plant_health_guess,
             yellowing_visible, drooping_visible, wilting_visible, image_quality,
             analysis_status, analysis_error, analysis_reliability, vlm_model, analyzed_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING time
            """
            cur.execute(
                insert_query,
                (
                    sensor_timestamp,
                    image_filename,
                    sensor_data['temperature_c'],
                    sensor_data['humidity_pct'],
                    bool(sensor_data['led_state']),
                    yolo_metadata['person_detected'],
                    yolo_metadata['person_count'],
                    json.dumps(yolo_metadata),
                    boxed_image_path,
                    video_filename,
                    None,  # vlm_summary
                    None,  # vlm_analysis
                    None,  # plant_visible
                    None,  # plant_occluded
                    None,  # plant_health_guess
                    None,  # yellowing_visible
                    None,  # drooping_visible
                    None,  # wilting_visible
                    None,  # image_quality
                    status,
                    error,
                    None,  # analysis_reliability
                    vlm_model,
                    None,  # analyzed_at
                ),
            )
        else:
            insert_query = """
            INSERT INTO plant_snapshots 
            (time, image_path, temperature_c, humidity_pct, led_state,
             person_detected, person_count, detection_metadata, boxed_image_path, video_path,
             vlm_summary, vlm_analysis, plant_visible, plant_occluded, plant_health_guess,
             yellowing_visible, drooping_visible, wilting_visible, image_quality,
             analysis_status, analysis_error, analysis_reliability, vlm_model, analyzed_at)
            VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING time
            """
            cur.execute(
                insert_query,
                (
                    image_filename,
                    sensor_data['temperature_c'],
                    sensor_data['humidity_pct'],
                    bool(sensor_data['led_state']),
                    yolo_metadata['person_detected'],
                    yolo_metadata['person_count'],
                    json.dumps(yolo_metadata),
                    boxed_image_path,
                    video_filename,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    status,
                    error,
                    None,
                    vlm_model,
                    None,
                ),
            )

        ts = cur.fetchone()[0]
        conn.commit()
        cur.close()
        logger.info(f"✓ Snapshot saved with status '{status}': {ts}")
        return True
    except Exception as e:
        logger.info(f"❌ Quick snapshot insert failed: {e}")
        conn.rollback()
        return False

def insert_snapshot_with_vlm(
    conn,
    image_filename: str,
    sensor_data: Dict[str, Any],
    yolo_result: Dict[str, Any],
    vlm_result: Dict[str, Any],
    enhanced_analysis: Dict[str, Any],
    sensor_timestamp: Optional[datetime] = None,
    video_filename: Optional[str] = None
) -> bool:
    """
    Insert snapshot with full VLM analysis into database
    
    Args:
        conn: Database connection
        image_filename: Name of captured image
        sensor_data: Temperature, humidity, LED state
        yolo_result: YOLO detection results
        vlm_result: Raw VLM analysis results
        enhanced_analysis: Enhanced analysis with rules applied
        sensor_timestamp: Optional exact timestamp from sensor
        video_filename: Optional video clip filename
        
    Returns:
        Success status
    """
    try:
        cur = conn.cursor()
        
        # Extract data
        yolo_metadata = yolo_result['metadata']
        boxed_image_path = Path(yolo_result['boxed_image_path']).name if yolo_result['boxed_image_path'] else None
        
        vlm_analysis = vlm_result.get('analysis', {})
        vlm_success = vlm_result.get('success', False)
        vlm_error = vlm_result.get('error')
        vlm_model = vlm_result.get('model')
        
        reliability = enhanced_analysis.get('reliability', {})
        
        # Determine analysis status
        if vlm_success:
            analysis_status = 'completed'
        elif vlm_error:
            analysis_status = 'failed'
        else:
            analysis_status = 'pending'
        
        # Generate summary
        vlm_summary = get_analysis_summary(enhanced_analysis)
        
        if sensor_timestamp:
            # Use exact timestamp from sensor_readings
            insert_query = """
            INSERT INTO plant_snapshots 
            (time, image_path, temperature_c, humidity_pct, led_state,
             person_detected, person_count, detection_metadata, boxed_image_path, video_path,
             vlm_summary, vlm_analysis, plant_visible, plant_occluded, plant_health_guess,
             yellowing_visible, drooping_visible, wilting_visible, image_quality,
             analysis_status, analysis_error, analysis_reliability, vlm_model, analyzed_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING time
            """
            
            cur.execute(insert_query, (
                sensor_timestamp,
                image_filename,
                sensor_data['temperature_c'],
                sensor_data['humidity_pct'],
                bool(sensor_data['led_state']),
                yolo_metadata['person_detected'],
                yolo_metadata['person_count'],
                json.dumps(yolo_metadata),
                boxed_image_path,
                video_filename,
                vlm_summary,
                json.dumps(vlm_analysis) if vlm_analysis else None,
                vlm_analysis.get('plant_visible', True),
                vlm_analysis.get('plant_occluded', False),
                vlm_analysis.get('plant_health_guess'),
                vlm_analysis.get('yellowing_visible', False),
                vlm_analysis.get('drooping_visible', False),
                vlm_analysis.get('wilting_visible', False),
                vlm_analysis.get('image_quality'),
                analysis_status,
                vlm_error,
                json.dumps(reliability),
                vlm_model,
                datetime.utcnow() if vlm_success else None
            ))
        else:
            # Use NOW() for manual captures
            insert_query = """
            INSERT INTO plant_snapshots 
            (time, image_path, temperature_c, humidity_pct, led_state,
             person_detected, person_count, detection_metadata, boxed_image_path, video_path,
             vlm_summary, vlm_analysis, plant_visible, plant_occluded, plant_health_guess,
             yellowing_visible, drooping_visible, wilting_visible, image_quality,
             analysis_status, analysis_error, analysis_reliability, vlm_model, analyzed_at)
            VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING time
            """
            
            cur.execute(insert_query, (
                image_filename,
                sensor_data['temperature_c'],
                sensor_data['humidity_pct'],
                bool(sensor_data['led_state']),
                yolo_metadata['person_detected'],
                yolo_metadata['person_count'],
                json.dumps(yolo_metadata),
                boxed_image_path,
                video_filename,
                vlm_summary,
                json.dumps(vlm_analysis) if vlm_analysis else None,
                vlm_analysis.get('plant_visible', True),
                vlm_analysis.get('plant_occluded', False),
                vlm_analysis.get('plant_health_guess'),
                vlm_analysis.get('yellowing_visible', False),
                vlm_analysis.get('drooping_visible', False),
                vlm_analysis.get('wilting_visible', False),
                vlm_analysis.get('image_quality'),
                analysis_status,
                vlm_error,
                json.dumps(reliability),
                vlm_model,
                datetime.utcnow() if vlm_success else None
            ))
        
        timestamp = cur.fetchone()[0]
        conn.commit()
        cur.close()
        
        # Insert analysis row
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO image_analysis (
                time, image_path, snapshot_time, vlm_summary, vlm_analysis,
                person_present, person_count, plant_visible, plant_occluded, plant_health_guess,
                yellowing_visible, drooping_visible, wilting_visible, image_quality,
                analysis_status, analysis_error, vlm_model, analyzed_at
            ) VALUES (
                NOW(), %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s
            )
            """,
            (
                image_filename,
                timestamp,
                vlm_summary,
                json.dumps(vlm_analysis) if vlm_analysis else None,
                vlm_analysis.get('person_present', False),
                vlm_analysis.get('person_count', 0),
                vlm_analysis.get('plant_visible', True),
                vlm_analysis.get('plant_occluded', False),
                vlm_analysis.get('plant_health_guess'),
                vlm_analysis.get('yellowing_visible', False),
                vlm_analysis.get('drooping_visible', False),
                vlm_analysis.get('wilting_visible', False),
                vlm_analysis.get('image_quality'),
                analysis_status,
                vlm_error,
                vlm_model,
                datetime.utcnow() if vlm_success else None,
            ),
        )
        conn.commit()
        cur.close()
        
        logger.info(f"✓ Snapshot with VLM analysis saved: {timestamp}")
        return True
        
    except Exception as e:
        logger.info(f"❌ Database insert failed: {e}")
        conn.rollback()
        return False


def insert_video_analysis(
    conn,
    video_filename: str,
    snapshot_id: int,
    vlm_result: Dict[str, Any]
) -> bool:
    """
    Insert video analysis results into database
    
    Args:
        conn: Database connection
        video_filename: Name of video file
        snapshot_id: Related snapshot ID
        vlm_result: VLM video analysis results
        
    Returns:
        Success status
    """
    try:
        cur = conn.cursor()
        
        vlm_analysis = vlm_result.get('analysis', {})
        vlm_success = vlm_result.get('success', False)
        vlm_error = vlm_result.get('error')
        vlm_model = vlm_result.get('model')
        frame_paths = vlm_result.get('frame_paths', [])
        
        analysis_status = 'completed' if vlm_success else 'failed' if vlm_error else 'pending'
        
        insert_query = """
        INSERT INTO video_analysis
        (time, video_path, snapshot_id, vlm_summary, vlm_analysis,
         person_entered, person_left, person_stayed, plant_touched, plant_blocked,
         plant_visible_throughout, significant_motion, motion_description, event_type,
         frames_analyzed, frame_paths, analysis_status, analysis_error, vlm_model, analyzed_at)
        VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        
        cur.execute(insert_query, (
            video_filename,
            snapshot_id,
            vlm_analysis.get('summary'),
            json.dumps(vlm_analysis) if vlm_analysis else None,
            vlm_analysis.get('person_entered', False),
            vlm_analysis.get('person_left', False),
            vlm_analysis.get('person_stayed', False),
            vlm_analysis.get('plant_touched', False),
            vlm_analysis.get('plant_blocked', False),
            vlm_analysis.get('plant_visible_throughout', True),
            vlm_analysis.get('significant_motion', False),
            vlm_analysis.get('motion_description'),
            vlm_analysis.get('event_type'),
            len(frame_paths),
            frame_paths,
            analysis_status,
            vlm_error,
            vlm_model,
            datetime.utcnow() if vlm_success else None
        ))
        
        video_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        
        logger.info(f"✓ Video analysis saved (ID: {video_id})")
        return True
        
    except Exception as e:
        logger.info(f"❌ Video analysis insert failed: {e}")
        conn.rollback()
        return False


def capture_and_analyze(
    sensor_data: Optional[Dict[str, Any]] = None,
    db_conn: Optional[psycopg.Connection] = None,
    sensor_timestamp: Optional[datetime] = None,
    enable_vlm: bool = True
) -> bool:
    """
    Complete pipeline: capture → YOLO → VLM → rules → database
    
    Args:
        sensor_data: Optional sensor data dict
        db_conn: Optional existing database connection
        sensor_timestamp: Optional exact timestamp from sensor
        enable_vlm: Whether to run VLM analysis (can disable for testing)
        
    Returns:
        Success status
    """
    logger.info("\n🌱 Starting capture with VLM analysis...")
    
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
        
        from capture_snapshot import IMAGES_DIR
        image_path = str(IMAGES_DIR / image_filename)
        
        # Step 2: Run YOLO person detection
        logger.info("\n🔍 Running YOLO person detection...")
        yolo_result = process_image_for_person_detection(image_path)
        
        # Step 3: Get sensor data if not provided
        if sensor_data is None:
            from capture_snapshot import get_latest_sensor_data
            sensor_data = get_latest_sensor_data(db_conn)
            if not sensor_data:
                logger.info("⚠️  Using default sensor values")
                sensor_data = {
                    'temperature_c': 0.0,
                    'humidity_pct': 0.0,
                    'led_state': False
                }
        
        # Step 4: Record video if temperature is high (DISABLED - now triggered by touch sensor)
        video_filename = None
        # Video recording is now triggered by touch sensor in serial_reader.py
        # if sensor_data['temperature_c'] >= 25.0:
        #     logger.info(f"\n🔥 Temperature alert: {sensor_data['temperature_c']}°C ≥ 25°C")
        #     video_filename = record_video_alert()
        #     if video_filename:
        #         logger.info(f"   📹 Video recorded: {video_filename}")
        
        # Step 5: Always queue VLM; insert snapshot quickly as 'queued'
        status = 'queued'
        reason = None
        model_name = os.getenv('OLLAMA_MODEL', 'llava:7b')

        logger.info("\n💾 Saving to database...")
        snapshot_success = insert_snapshot_quick(
            db_conn,
            image_filename,
            sensor_data,
            yolo_result,
            status,
            reason,
            sensor_timestamp,
            video_filename,
            model_name if status == 'queued' else None,
        )
        
        if not snapshot_success:
            return False
        
        # Step 8: Analyze video if available (disabled by default)
        if video_filename and enable_vlm and _should_run_vlm() and VLM_VIDEO_ENABLED:
            logger.info("\n🎬 Running VLM video analysis...")
            from capture_video import VIDEOS_DIR
            video_path = str(VIDEOS_DIR / video_filename)
            
            video_vlm_result = analyze_video_with_vlm(
                video_path,
                frame_count=5,
                yolo_metadata=yolo_result['metadata']
            )
            
            # Video linking: if plant_snapshots has no id, skip linking gracefully
            try:
                cur = db_conn.cursor()
                cur.execute("SELECT id FROM plant_snapshots ORDER BY time DESC LIMIT 1")
                row = cur.fetchone()
                cur.close()
                if row and row[0] is not None:
                    snapshot_id = row[0]
                    insert_video_analysis(db_conn, video_filename, snapshot_id, video_vlm_result)
                else:
                    logger.info("⚠️  Skipping video->snapshot link (no id column)")
            except Exception:
                logger.info("⚠️  Skipping video->snapshot link (id lookup failed)")
        elif video_filename and not VLM_VIDEO_ENABLED:
            logger.info("⚠️  Skipping VLM video analysis (disabled)")
        
        # Print final summary
        logger.info(f"\n✅ Complete pipeline finished!")
        logger.info(f"   📸 Image: {image_filename}")
        if yolo_result['boxed_image_path']:
            logger.info(f"   🖼️  Boxed: {Path(yolo_result['boxed_image_path']).name}")
        if video_filename:
            logger.info(f"   📹 Video: {video_filename}")
        logger.info(f"   👤 Person detected: {yolo_result['metadata']['person_detected']}")
        logger.info(f"   🌡️  Temp: {sensor_data['temperature_c']}°C")
        logger.info(f"   🤖 VLM status: {status}{(' - ' + reason) if reason else ''}")
        
        return True
        
    except Exception as e:
        logger.info(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if close_conn:
            db_conn.close()


if __name__ == "__main__":
    # Test the complete pipeline
    import sys
    
    enable_vlm = '--no-vlm' not in sys.argv
    
    if not enable_vlm:
        logger.info("⚠️  VLM analysis disabled (--no-vlm flag)")
    
    capture_and_analyze(enable_vlm=enable_vlm)
