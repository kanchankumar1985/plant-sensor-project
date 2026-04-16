from datetime import datetime
import os
from pathlib import Path
import json

from dotenv import load_dotenv
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import psycopg

load_dotenv()

# Initialize logging system
import logging_config
logging_config.init_logging()
logger = logging_config.get_app_logger()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://plantuser:plantpass@localhost:5433/plantdb")

app = FastAPI(title="Plant Monitor API")

logger.info("FastAPI application starting")

# Import and register touch sensor routes
from touch_routes import router as touch_router
app.include_router(touch_router)
logger.info("Touch sensor routes registered")

# Import and register logs routes
from routes.logs import router as logs_router
app.include_router(logs_router)
logger.info("Logs API routes registered")

# Mount images directory for static file serving (configurable via IMAGES_DIR env var)
IMAGES_DIR = Path(os.getenv('IMAGES_DIR', str(Path(__file__).parent / "images")))
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")

# Videos directory (configurable via VIDEOS_DIR env var)
VIDEOS_DIR = Path(os.getenv('VIDEOS_DIR', str(Path(__file__).parent / "videos")))
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

# Custom video endpoint with proper MIME type
@app.get("/videos/{filename}")
async def serve_video(filename: str):
    """Serve video files with proper MIME type for browser compatibility"""
    video_path = VIDEOS_DIR / filename
    
    if not video_path.exists():
        return Response(status_code=404, content="Video not found")
    
    # Read video file
    with open(video_path, 'rb') as f:
        video_data = f.read()
    
    # Return with proper headers for AVI/MJPEG playback
    return Response(
        content=video_data,
        media_type="video/x-msvideo",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(len(video_data)),
        }
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SensorReadingIn(BaseModel):
    device_id: str = Field(..., min_length=1)
    temperature_c: float
    humidity_pct: float

class SensorReadingOut(BaseModel):
    time: datetime
    device_id: str
    temperature_c: float
    humidity_pct: float
    led_state: int = 0

class TouchEventIn(BaseModel):
    device_id: str = Field(default="plant-esp32-01")
    state: str = Field(..., pattern="^(TOUCHED|NOT_TOUCHED)$")
    timestamp: datetime | None = None

class TouchEventOut(BaseModel):
    id: int
    timestamp: datetime
    device_id: str
    state: str

def get_conn():
    return psycopg.connect(DATABASE_URL)

@app.get("/health")
def health():
    logger.debug("Health check requested")
    return {"status": "ok"}

@app.post("/api/readings")
def create_reading(payload: SensorReadingIn):
    logger.info(f"Sensor reading received: {payload.device_id} - {payload.temperature_c}°C, {payload.humidity_pct}%")
    sql = """
        INSERT INTO sensor_readings (device_id, temperature_c, humidity_pct)
        VALUES (%s, %s, %s)
        RETURNING time, device_id, temperature_c, humidity_pct
    """
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    (payload.device_id, payload.temperature_c, payload.humidity_pct),
                )
                row = cur.fetchone()
                conn.commit()
        
        logger.info(f"Sensor reading saved: {row[1]} at {row[0]}")
        return {
            "time": row[0],
            "device_id": row[1],
            "temperature_c": row[2],
            "humidity_pct": row[3],
        }
    except Exception as e:
        logger.error(f"Failed to save sensor reading: {e}", exc_info=True)
        raise

@app.get("/api/readings/latest", response_model=SensorReadingOut | None)
def get_latest():
    sql = """
        SELECT time, device_id, temperature_c, humidity_pct, led_state
        FROM sensor_readings
        ORDER BY time DESC
        LIMIT 1
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            row = cur.fetchone()

    if not row:
        return None

    return {
        "time": row[0],
        "device_id": row[1],
        "temperature_c": row[2],
        "humidity_pct": row[3],
        "led_state": row[4] if len(row) > 4 else 0,
    }

@app.get("/api/readings/recent")
def get_recent(limit: int = 50):
    sql = """
        SELECT time, device_id, temperature_c, humidity_pct, led_state
        FROM sensor_readings
        ORDER BY time DESC
        LIMIT %s
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (limit,))
            rows = cur.fetchall()

    data = [
        {
            "time": row[0].isoformat(),
            "device_id": row[1],
            "temperature_c": row[2],
            "humidity_pct": row[3],
            "led_state": row[4] if len(row) > 4 else 0,
        }
        for row in rows
    ]

    data.reverse()
    return data

@app.get("/api/readings/range")
def get_readings_by_range(start_time: str, end_time: str, limit: int = 1000):
    """Get sensor readings within a specific time range"""
    sql = """
        SELECT time, device_id, temperature_c, humidity_pct, led_state
        FROM sensor_readings
        WHERE time >= %s AND time <= %s
        ORDER BY time ASC
        LIMIT %s
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (start_time, end_time, limit))
            rows = cur.fetchall()

    data = [
        {
            "time": row[0].isoformat(),
            "device_id": row[1],
            "temperature_c": row[2],
            "humidity_pct": row[3],
            "led_state": row[4] if len(row) > 4 else 0,
        }
        for row in rows
    ]

    return data

# ========== SNAPSHOT ENDPOINTS ==========

class SnapshotOut(BaseModel):
    time: datetime
    image_url: str
    temperature_c: float
    humidity_pct: float
    led_state: bool
    vlm_result: str | None

@app.get("/api/snapshots/latest", response_model=SnapshotOut | None)
def get_latest_snapshot():
    """Get the most recent plant snapshot with metadata"""
    sql = """
        SELECT time, image_path, temperature_c, humidity_pct, led_state, vlm_result
        FROM plant_snapshots
        ORDER BY time DESC
        LIMIT 1
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            row = cur.fetchone()

    if not row:
        return None

    return {
        "time": row[0],
        "image_url": f"http://localhost:8000/images/{row[1]}",
        "temperature_c": row[2],
        "humidity_pct": row[3],
        "led_state": row[4],
        "vlm_result": row[5],
    }

@app.get("/api/snapshots/recent")
def get_recent_snapshots(limit: int = 10000):
    """Get all plant snapshots with metadata (default: 10,000)"""
    sql = """
        SELECT time, image_path, boxed_image_path, temperature_c, humidity_pct, led_state, vlm_result, person_detected, person_count, detection_metadata, video_path
        FROM plant_snapshots
        ORDER BY time DESC
        LIMIT %s
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (limit,))
            rows = cur.fetchall()

    data = [
        {
            "time": row[0].isoformat(),
            "image_url": f"http://localhost:8000/images/{row[1]}",
            "image_path": row[1],
            "boxed_image_url": f"http://localhost:8000/images/{row[2]}" if row[2] else None,
            "temperature_c": row[3],
            "humidity_pct": row[4],
            "led_state": row[5],
            "vlm_result": row[6],
            "person_detected": row[7],
            "person_count": row[8],
            "detection_metadata": row[9],
            "video_url": f"http://localhost:8000/videos/{row[10]}" if row[10] else None,
        }
        for row in rows
    ]

    return data

# ========== PERSON DETECTION ENDPOINTS ==========

@app.get("/api/snapshots/latest-detection")
def get_latest_detection():
    """Get the most recent snapshot with person detection metadata"""
    sql = """
        SELECT time, image_path, boxed_image_path, temperature_c, humidity_pct, 
               led_state, vlm_result, person_detected, person_count, detection_metadata
        FROM plant_snapshots
        WHERE detection_metadata IS NOT NULL
        ORDER BY time DESC
        LIMIT 1
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            row = cur.fetchone()

    if not row:
        return None

    return {
        "time": row[0],
        "image_path": row[1],
        "boxed_image_path": row[2],
        "image_url": f"http://localhost:8000/images/{row[1]}" if row[1] else None,
        "boxed_image_url": f"http://localhost:8000/images/{row[2]}" if row[2] else None,
        "temperature_c": row[3],
        "humidity_pct": row[4],
        "led_state": row[5],
        "vlm_result": row[6],
        "person_detected": row[7],
        "person_count": row[8],
        "detection_metadata": row[9],
    }

# ========== TOUCH SENSOR ENDPOINTS ==========

@app.post("/api/touch-event", response_model=TouchEventOut)
def create_touch_event(payload: TouchEventIn):
    """Record a touch sensor event"""
    sql = """
        INSERT INTO touch_events (device_id, state, timestamp)
        VALUES (%s, %s, COALESCE(%s, NOW()))
        RETURNING id, timestamp, device_id, state
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (payload.device_id, payload.state, payload.timestamp),
            )
            row = cur.fetchone()
            conn.commit()

    return {
        "id": row[0],
        "timestamp": row[1],
        "device_id": row[2],
        "state": row[3],
    }

@app.get("/api/touch-event/latest")
def get_latest_touch_event():
    """Get the most recent touch event"""
    sql = """
        SELECT id, timestamp, device_id, state
        FROM touch_events
        ORDER BY timestamp DESC
        LIMIT 1
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            row = cur.fetchone()

    if not row:
        return None

    return {
        "id": row[0],
        "timestamp": row[1],
        "device_id": row[2],
        "state": row[3],
    }

@app.get("/api/touch-event/recent")
def get_recent_touch_events(limit: int = 100):
    """Get recent touch events"""
    sql = """
        SELECT id, timestamp, device_id, state
        FROM touch_events
        ORDER BY timestamp DESC
        LIMIT %s
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (limit,))
            rows = cur.fetchall()

    data = [
        {
            "id": row[0],
            "timestamp": row[1].isoformat(),
            "device_id": row[2],
            "state": row[3],
        }
        for row in rows
    ]

    data.reverse()
    return data

@app.get("/api/touch-event/status")
def get_touch_status():
    """Get current touch status from latest_touch_state view"""
    sql = """
        SELECT device_id, timestamp, state
        FROM latest_touch_state
        WHERE device_id = 'plant-esp32-01'
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            row = cur.fetchone()

    if not row:
        return {
            "device_id": "plant-esp32-01",
            "timestamp": None,
            "state": "NOT_TOUCHED",
            "is_touched": False,
        }

    return {
        "device_id": row[0],
        "timestamp": row[1].isoformat(),
        "state": row[2],
        "is_touched": row[2] == "TOUCHED",
    }

# ========== VLM ANALYSIS ENDPOINTS ==========

@app.get("/api/analysis/latest-image")
def get_latest_image_analysis():
    """Get the most recent image with VLM analysis"""
    sql = """
        SELECT time, image_path, boxed_image_path, video_path, temperature_c, humidity_pct, 
               led_state, person_detected, person_count, plant_visible, plant_occluded,
               plant_health_guess, yellowing_visible, drooping_visible, wilting_visible,
               image_quality, vlm_summary, vlm_analysis, analysis_reliability, 
               analysis_status, vlm_model, analyzed_at
        FROM plant_snapshots
        WHERE analysis_status IS NOT NULL
        ORDER BY time DESC
        LIMIT 1
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            row = cur.fetchone()

    if not row:
        return None

    return {
        "time": row[0],
        "image_path": row[1],
        "boxed_image_path": row[2],
        "video_path": row[3],
        "image_url": f"http://localhost:8000/images/{row[1]}" if row[1] else None,
        "boxed_image_url": f"http://localhost:8000/images/{row[2]}" if row[2] else None,
        "video_url": f"http://localhost:8000/videos/{row[3]}" if row[3] else None,
        "temperature_c": row[4],
        "humidity_pct": row[5],
        "led_state": row[6],
        "person_detected": row[7],
        "person_count": row[8],
        "plant_visible": row[9],
        "plant_occluded": row[10],
        "plant_health_guess": row[11],
        "yellowing_visible": row[12],
        "drooping_visible": row[13],
        "wilting_visible": row[14],
        "image_quality": row[15],
        "vlm_summary": row[16],
        "vlm_analysis": row[17],
        "analysis_reliability": row[18],
        "analysis_status": row[19],
        "vlm_model": row[20],
        "analyzed_at": row[21],
    }

@app.get("/api/analysis/latest-video")
def get_latest_video_analysis():
    """Get the most recent video event analysis"""
    sql = """
        SELECT time, video_path, snapshot_id, vlm_summary, vlm_analysis,
               person_entered, person_left, person_stayed, plant_touched, plant_blocked,
               plant_visible_throughout, significant_motion, motion_description, event_type,
               frames_analyzed, frame_paths, analysis_status, vlm_model, analyzed_at
        FROM video_analysis
        WHERE analysis_status IS NOT NULL
        ORDER BY time DESC
        LIMIT 1
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            row = cur.fetchone()

    if not row:
        return None

    return {
        "time": row[0],
        "video_path": row[1],
        "video_url": f"http://localhost:8000/videos/{row[1]}" if row[1] else None,
        "snapshot_id": row[2],
        "vlm_summary": row[3],
        "vlm_analysis": row[4],
        "person_entered": row[5],
        "person_left": row[6],
        "person_stayed": row[7],
        "plant_touched": row[8],
        "plant_blocked": row[9],
        "plant_visible_throughout": row[10],
        "significant_motion": row[11],
        "motion_description": row[12],
        "event_type": row[13],
        "frames_analyzed": row[14],
        "frame_paths": row[15],
        "analysis_status": row[16],
        "vlm_model": row[17],
        "analyzed_at": row[18],
    }

@app.get("/api/analysis/recent")
def get_recent_analyses(limit: int = 20):
    """Get recent VLM analyses"""
    sql = """
        SELECT time, image_path, plant_health_guess, vlm_summary, 
               analysis_status, person_detected, temperature_c, humidity_pct
        FROM plant_snapshots
        WHERE analysis_status IS NOT NULL
        ORDER BY time DESC
        LIMIT %s
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (limit,))
            rows = cur.fetchall()

    return [
        {
            "time": row[0].isoformat(),
            "image_url": f"http://localhost:8000/images/{row[1]}" if row[1] else None,
            "plant_health_guess": row[2],
            "vlm_summary": row[3],
            "analysis_status": row[4],
            "person_detected": row[5],
            "temperature_c": row[6],
            "humidity_pct": row[7],
        }
        for row in rows
    ]

@app.get("/api/analysis/health-alerts")
def get_health_alerts():
    """Get snapshots with plant health concerns"""
    sql = """
        SELECT time, image_path, plant_health_guess, yellowing_visible, 
               drooping_visible, wilting_visible, vlm_summary, temperature_c, humidity_pct
        FROM plant_snapshots
        WHERE analysis_status = 'completed'
          AND (yellowing_visible = TRUE 
               OR drooping_visible = TRUE 
               OR wilting_visible = TRUE
               OR plant_health_guess IN ('yellowing', 'drooping', 'wilting'))
        ORDER BY time DESC
        LIMIT 50
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()

    return [
        {
            "time": row[0].isoformat(),
            "image_url": f"http://localhost:8000/images/{row[1]}" if row[1] else None,
            "plant_health_guess": row[2],
            "yellowing_visible": row[3],
            "drooping_visible": row[4],
            "wilting_visible": row[5],
            "vlm_summary": row[6],
            "temperature_c": row[7],
            "humidity_pct": row[8],
        }
        for row in rows
    ]

@app.get("/api/analysis/status")
def get_ai_status():
    """Get AI system status (Ollama, model, queue)"""
    # Check Ollama connection
    ollama_connected = False
    model_name = None
    available_models = []
    
    try:
        from vlm.ollama_client import get_ollama_client
        client = get_ollama_client()
        ollama_connected = client.check_health()
        model_name = client.model
        
        # Try to get available models
        import requests
        response = requests.get(f"{client.host}/api/tags", timeout=2)
        if response.ok:
            models = response.json().get('models', [])
            available_models = [m.get('name') for m in models]
    except Exception as e:
        print(f"Ollama status check failed: {e}")
    
    # Get queue stats from database
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Count by status
            cur.execute("""
                SELECT analysis_status, COUNT(*) 
                FROM plant_snapshots 
                WHERE analysis_status IS NOT NULL
                GROUP BY analysis_status
            """)
            status_counts = dict(cur.fetchall())
            
            # Get recent stats
            cur.execute("""
                SELECT 
                    MAX(analyzed_at) as last_analysis,
                    COUNT(*) FILTER (WHERE DATE(analyzed_at) = CURRENT_DATE) as today_count,
                    AVG(EXTRACT(EPOCH FROM (analyzed_at - time))) as avg_time
                FROM plant_snapshots
                WHERE analyzed_at IS NOT NULL
            """)
            stats = cur.fetchone()
            
            # Get recent errors
            cur.execute("""
                SELECT time, analysis_error
                FROM plant_snapshots
                WHERE analysis_error IS NOT NULL
                ORDER BY time DESC
                LIMIT 5
            """)
            error_rows = cur.fetchall()
    
    recent_errors = [
        {"time": row[0].isoformat(), "message": row[1], "type": "Analysis Error"}
        for row in error_rows
    ]
    
    return {
        "ollama_connected": ollama_connected,
        "ollama_host": "http://localhost:11434",
        "model_name": model_name,
        "model_size": "7B" if model_name and "7b" in model_name.lower() else "Unknown",
        "available_models": available_models,
        "model_loaded": ollama_connected and model_name is not None,
        "database_connected": True,
        "pending_count": status_counts.get('queued', 0),
        "processing_count": status_counts.get('processing', 0),
        "completed_count": status_counts.get('completed', 0),
        "failed_count": status_counts.get('failed', 0),
        "skipped_count": status_counts.get('skipped', 0),
        "last_analysis_time": stats[0].isoformat() if stats[0] else None,
        "analyses_today": stats[1] or 0,
        "avg_processing_time": float(stats[2]) if stats[2] else None,
        "success_rate": status_counts.get('completed', 0) / max(sum(status_counts.values()), 1),
        "recent_errors": recent_errors,
    }

@app.post("/api/analysis/run-latest")
def trigger_analysis():
    """Trigger VLM analysis on the most recent snapshot"""
    # This would trigger the analysis pipeline
    # For now, return a placeholder
    return {
        "status": "triggered",
        "message": "Analysis pipeline triggered. Run capture_with_vlm.py manually for now."
    }
