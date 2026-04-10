from datetime import datetime
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import psycopg

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://plantuser:plantpass@localhost:5433/plantdb")

app = FastAPI(title="Plant Monitor API")

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
    return {"status": "ok"}

@app.post("/api/readings")
def create_reading(payload: SensorReadingIn):
    sql = """
        INSERT INTO sensor_readings (device_id, temperature_c, humidity_pct)
        VALUES (%s, %s, %s)
        RETURNING time, device_id, temperature_c, humidity_pct
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (payload.device_id, payload.temperature_c, payload.humidity_pct),
            )
            row = cur.fetchone()
            conn.commit()

    return {
        "time": row[0],
        "device_id": row[1],
        "temperature_c": row[2],
        "humidity_pct": row[3],
    }

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
