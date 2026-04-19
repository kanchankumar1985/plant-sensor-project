"""
Touch Workflow Orchestration
Handles the complete pipeline when touch sensor is triggered
"""

import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Import existing services
try:
    from services.tts_service import get_tts_service
except ImportError:
    from tts_service import get_tts_service

# Import existing capture functions
try:
    from capture_snapshot import capture_webcam_image, get_latest_sensor_data, IMAGES_DIR
    from capture_video import record_video_alert, VIDEOS_DIR
    from detect_person import process_image_for_person_detection
    CAPTURE_AVAILABLE = True
except ImportError:
    logger.warning("Capture modules not available - using stubs")
    CAPTURE_AVAILABLE = False
    IMAGES_DIR = Path("./images")
    VIDEOS_DIR = Path("./videos")

# Import database connection
try:
    import psycopg
    DB_CONFIG = {
        "host": "localhost",
        "port": "5433",
        "dbname": "plantdb",
        "user": "plantuser",
        "password": "plantpass"
    }
    DB_AVAILABLE = True
except ImportError:
    logger.warning("Database not available")
    DB_AVAILABLE = False


class TouchWorkflowStatus:
    """Track workflow status"""
    
    def __init__(self):
        self.status = "idle"  # idle, triggered, running, completed, failed
        self.last_trigger_time: Optional[datetime] = None
        self.last_message: Optional[str] = None
        self.current_step: Optional[str] = None
        self.image_path: Optional[str] = None
        self.video_path: Optional[str] = None
        self.yolo_result: Optional[Dict] = None
        self.error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "status": self.status,
            "last_trigger_time": self.last_trigger_time.isoformat() if self.last_trigger_time else None,
            "last_message": self.last_message,
            "current_step": self.current_step,
            "image_path": self.image_path,
            "video_path": self.video_path,
            "yolo_result": self.yolo_result,
            "error": self.error
        }


class TouchWorkflowOrchestrator:
    """Orchestrates the complete touch-triggered workflow"""
    
    def __init__(self):
        self.tts = get_tts_service()
        self.status = TouchWorkflowStatus()
        self.lock = threading.Lock()
    
    def handle_touch_event(self):
        """
        Main entry point for touch event
        Runs the complete workflow in background
        """
        logger.info("=" * 60)
        logger.info("🖐️  TOUCH EVENT DETECTED")
        logger.info("=" * 60)
        
        # Update status
        with self.lock:
            self.status.status = "triggered"
            self.status.last_trigger_time = datetime.utcnow()
            self.status.error = None
        
        # Speak immediately (non-blocking)
        logger.info("🔊 Speaking: 'Sensor touched'")
        self.tts.speak_touch_event()
        self.status.last_message = "Sensor touched"
        
        # Run workflow in background thread
        thread = threading.Thread(target=self._run_workflow, daemon=True)
        thread.start()
    
    def _run_workflow(self):
        """Execute the complete workflow (runs in background thread)"""
        try:
            with self.lock:
                self.status.status = "running"
            
            # Step 1: Capture snapshot
            self._capture_snapshot()
            
            # Step 2: Record video clip
            self._record_video()
            
            # Step 3: Run YOLO detection
            self._run_yolo()
            
            # Step 4: Queue VLM analysis
            self._queue_vlm_analysis()
            
            # Step 5: Save to database
            self._save_to_database()
            
            # Workflow complete
            with self.lock:
                self.status.status = "completed"
                self.status.current_step = "completed"
            
            logger.info("=" * 60)
            logger.info("✅ TOUCH WORKFLOW COMPLETED")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ Workflow failed: {e}", exc_info=True)
            with self.lock:
                self.status.status = "failed"
                self.status.error = str(e)
    
    def _capture_snapshot(self):
        """Step 1: Capture webcam snapshot"""
        with self.lock:
            self.status.current_step = "capturing_snapshot"
        
        logger.info("📸 Step 1: Capturing snapshot...")
        
        if not CAPTURE_AVAILABLE:
            logger.warning("⚠️  Capture not available - skipping")
            return
        
        try:
            image_filename = capture_webcam_image()
            if image_filename:
                self.status.image_path = str(IMAGES_DIR / image_filename)
                logger.info(f"✓ Snapshot saved: {image_filename}")
            else:
                logger.warning("⚠️  Snapshot capture failed")
        except Exception as e:
            logger.error(f"❌ Snapshot capture error: {e}")
    
    def _record_video(self):
        """Step 2: Record video clip"""
        with self.lock:
            self.status.current_step = "recording_video"
        
        logger.info("🎥 Step 2: Recording video clip...")
        
        if not CAPTURE_AVAILABLE:
            logger.warning("⚠️  Video recording not available - skipping")
            return
        
        try:
            video_filename = record_video_alert(duration=5, fps=10)
            if video_filename:
                self.status.video_path = str(VIDEOS_DIR / video_filename)
                logger.info(f"✓ Video saved: {video_filename}")
            else:
                logger.warning("⚠️  Video recording failed")
        except Exception as e:
            logger.error(f"❌ Video recording error: {e}")
    
    def _run_yolo(self):
        """Step 3: Run YOLO person detection"""
        with self.lock:
            self.status.current_step = "running_yolo"
        
        logger.info("🔍 Step 3: Running YOLO detection...")
        
        if not self.status.image_path or not CAPTURE_AVAILABLE:
            logger.warning("⚠️  No image available for YOLO - skipping")
            return
        
        try:
            yolo_result = process_image_for_person_detection(self.status.image_path)
            if yolo_result:
                self.status.yolo_result = yolo_result.get('metadata', {})
                logger.info(f"✓ YOLO complete - Person detected: {yolo_result['metadata'].get('person_detected', False)}")
            else:
                logger.warning("⚠️  YOLO detection failed")
        except Exception as e:
            logger.error(f"❌ YOLO detection error: {e}")
    
    def _queue_vlm_analysis(self):
        """Step 4: Queue VLM analysis (background worker will process)"""
        with self.lock:
            self.status.current_step = "queuing_vlm"
        
        logger.info("🤖 Step 4: Queuing VLM analysis...")
        logger.info("   VLM worker will process in background")
        
        # VLM analysis is handled by vlm_worker.py
        # The snapshot will be marked as 'queued' in database
        # and worker will pick it up automatically
    
    def _save_to_database(self):
        """Step 5: Save workflow results to database"""
        with self.lock:
            self.status.current_step = "saving_database"
        
        logger.info("💾 Step 5: Saving to database...")
        
        if not DB_AVAILABLE:
            logger.warning("⚠️  Database not available - skipping")
            return
        
        try:
            # Import capture_with_vlm to use its database insertion
            from capture_with_vlm import capture_and_analyze, connect_database
            
            # Get sensor data
            conn = connect_database()
            if not conn:
                logger.warning("⚠️  Database connection failed")
                return
            
            # The capture_and_analyze function will handle database insertion
            # with VLM queuing
            logger.info("✓ Database save queued (handled by capture pipeline)")
            try:
                _ = capture_and_analyze(
                    sensor_data=None,
                    db_conn=conn,
                    sensor_timestamp=None,
                    enable_vlm=True,
                )
            finally:
                try:
                    conn.close()
                except Exception:
                    pass
            
        except Exception as e:
            logger.error(f"❌ Database save error: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current workflow status"""
        with self.lock:
            return self.status.to_dict()


# Singleton instance
_orchestrator: Optional[TouchWorkflowOrchestrator] = None

def get_orchestrator() -> TouchWorkflowOrchestrator:
    """Get or create orchestrator singleton"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = TouchWorkflowOrchestrator()
    return _orchestrator


def handle_touch_event():
    """Convenience function to trigger workflow"""
    orchestrator = get_orchestrator()
    orchestrator.handle_touch_event()


if __name__ == "__main__":
    # Test workflow
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s'
    )
    
    logger.info("Testing touch workflow...")
    handle_touch_event()
    
    # Wait for workflow to complete
    time.sleep(15)
    
    orchestrator = get_orchestrator()
    status = orchestrator.get_status()
    logger.info(f"Final status: {status}")
