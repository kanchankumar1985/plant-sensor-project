"""
Touch sensor event API routes
Handles touch events from ESP32 and provides latest status
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import os
import psycopg
from psycopg.rows import dict_row
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration - use same format as app.py
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://plantuser:plantpass@localhost:5433/plantdb")

router = APIRouter(prefix="/api", tags=["touch"])


# ===== REQUEST/RESPONSE MODELS =====

class TouchEventRequest(BaseModel):
    timestamp: str = Field(..., description="ISO 8601 timestamp from ESP32")
    state: str = Field(..., description="Touch state: TOUCHED or NOT_TOUCHED")
    device_id: Optional[str] = Field(default="plant-esp32-01", description="Device identifier")
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2026-04-13T12:00:00Z",
                "state": "TOUCHED",
                "device_id": "plant-esp32-01"
            }
        }


class TouchEventResponse(BaseModel):
    success: bool
    message: str
    event_id: Optional[int] = None


class LatestTouchStatus(BaseModel):
    id: int
    timestamp: datetime
    state: str
    device_id: str
    seconds_ago: Optional[float] = None


# ===== DATABASE HELPERS =====

def get_db_connection():
    """Create database connection with error handling"""
    try:
        conn = psycopg.connect(DATABASE_URL)
        return conn
    except psycopg.Error as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed"
        )


def insert_touch_event(timestamp_str: str, state: str, device_id: str = "plant-esp32-01") -> int:
    """
    Insert touch event into database
    
    Args:
        timestamp_str: ISO timestamp string
        state: Touch state (TOUCHED or NOT_TOUCHED)
        device_id: Device identifier (default: plant-esp32-01)
        
    Returns:
        Event ID of inserted row
        
    Raises:
        HTTPException: If database operation fails
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Parse timestamp
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except ValueError:
            # Fallback to current time if parsing fails
            timestamp = datetime.utcnow()
            logger.warning(f"Invalid timestamp format: {timestamp_str}, using current time")
        
        # Validate state
        if state not in ["TOUCHED", "NOT_TOUCHED"]:
            raise ValueError(f"Invalid state: {state}")
        
        # Insert event
        insert_query = """
            INSERT INTO touch_events (timestamp, state, device_id)
            VALUES (%s, %s, %s)
            RETURNING id
        """
        
        cur.execute(insert_query, (timestamp, state, device_id))
        event_id = cur.fetchone()[0]
        
        conn.commit()
        logger.info(f"Touch event inserted: id={event_id}, state={state}, device_id={device_id}, timestamp={timestamp}")
        
        return event_id
        
    except psycopg.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Database insert failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to insert touch event: {str(e)}"
        )
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    finally:
        if conn:
            cur.close()
            conn.close()


def get_latest_touch_event() -> Optional[dict]:
    """
    Fetch the most recent touch event from database
    
    Returns:
        Dictionary with event data or None if no events exist
    """
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(row_factory=dict_row)
        
        query = """
            SELECT id, timestamp, state, device_id
            FROM touch_events
            ORDER BY timestamp DESC
            LIMIT 1
        """
        
        cur.execute(query)
        result = cur.fetchone()
        
        if result:
            # Calculate seconds since event
            from datetime import timezone
            now = datetime.now(timezone.utc)
            event_time = result['timestamp']
            
            # Ensure timezone-aware
            if event_time.tzinfo is None:
                event_time = event_time.replace(tzinfo=timezone.utc)
            
            seconds_ago = (now - event_time).total_seconds()
            
            return {
                "id": result['id'],
                "timestamp": result['timestamp'],
                "state": result['state'],
                "device_id": result['device_id'],
                "seconds_ago": seconds_ago
            }
        
        return None
        
    except psycopg.Error as e:
        logger.error(f"Database query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch latest touch event"
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_latest_touch_event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch latest touch event"
        )
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


# ===== API ROUTES =====

@router.post("/touch-event", response_model=TouchEventResponse, status_code=status.HTTP_201_CREATED)
async def create_touch_event(event: TouchEventRequest):
    """
    Receive touch event from ESP32 and store in database
    
    - **timestamp**: ISO 8601 timestamp from ESP32
    - **state**: Touch state (TOUCHED or NOT_TOUCHED)
    - **device_id**: Device identifier (optional, defaults to plant-esp32-01)
    """
    logger.info(f"Received touch event: state={event.state}, device_id={event.device_id}, timestamp={event.timestamp}")
    
    try:
        event_id = insert_touch_event(event.timestamp, event.state, event.device_id)
        
        return TouchEventResponse(
            success=True,
            message=f"Touch event recorded: {event.state}",
            event_id=event_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/touch/latest", response_model=LatestTouchStatus)
async def get_latest_touch():
    """
    Get the most recent touch sensor status
    
    Returns the latest touch event with timestamp and how long ago it occurred
    """
    try:
        latest = get_latest_touch_event()
        
        if not latest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No touch events found"
            )
        
        return LatestTouchStatus(**latest)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/touch/history")
async def get_touch_history(limit: int = 50):
    """
    Get recent touch event history
    
    - **limit**: Maximum number of events to return (default: 50)
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(row_factory=dict_row)
        
        query = """
            SELECT id, timestamp, state, device_id
            FROM touch_events
            ORDER BY timestamp DESC
            LIMIT %s
        """
        
        cur.execute(query, (limit,))
        results = cur.fetchall()
        
        return {
            "success": True,
            "count": len(results),
            "events": results
        }
        
    except psycopg.Error as e:
        logger.error(f"Database query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch touch history"
        )
    finally:
        if conn:
            cur.close()
            conn.close()
