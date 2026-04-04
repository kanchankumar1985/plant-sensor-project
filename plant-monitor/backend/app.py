from datetime import datetime
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import psycopg

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://plantuser:plantpass@localhost:5433/plantdb")

app = FastAPI(title="Plant Monitor API")

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
        SELECT time, device_id, temperature_c, humidity_pct
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
    }

@app.get("/api/readings/recent")
def get_recent(limit: int = 50):
    sql = """
        SELECT time, device_id, temperature_c, humidity_pct
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
        }
        for row in rows
    ]

    data.reverse()
    return data

@app.get("/api/readings/range")
def get_readings_by_range(start_time: str, end_time: str, limit: int = 1000):
    """Get sensor readings within a specific time range"""
    sql = """
        SELECT time, device_id, temperature_c, humidity_pct
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
        }
        for row in rows
    ]

    return data
