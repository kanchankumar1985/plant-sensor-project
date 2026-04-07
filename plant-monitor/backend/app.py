from datetime import datetime
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import psycopg

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://plantuser:plantpass@localhost:5433/plantdb")

app = FastAPI(title="Plant Monitor API")

# Mount images directory for static file serving
IMAGES_DIR = Path(__file__).parent / "images"
IMAGES_DIR.mkdir(exist_ok=True)
app.mount("/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")

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
def get_recent_snapshots(limit: int = 10):
    """Get recent plant snapshots with metadata"""
    sql = """
        SELECT time, image_path, temperature_c, humidity_pct, led_state, vlm_result
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
            "temperature_c": row[2],
            "humidity_pct": row[3],
            "led_state": row[4],
            "vlm_result": row[5],
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
