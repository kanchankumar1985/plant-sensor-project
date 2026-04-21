"""
Touch Workflow API Routes
Provides endpoints to trigger and monitor touch workflows
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/touch-workflow", tags=["touch-workflow"])

# Import workflow orchestrator
try:
    from services.touch_workflow import handle_touch_event, get_orchestrator
    WORKFLOW_AVAILABLE = True
except ImportError:
    logger.warning("Touch workflow not available")
    WORKFLOW_AVAILABLE = False


class TouchTriggerResponse(BaseModel):
    success: bool
    message: str
    workflow_status: Optional[Dict[str, Any]] = None


class WorkflowStatusResponse(BaseModel):
    success: bool
    status: Dict[str, Any]


@router.post("/trigger", response_model=TouchTriggerResponse)
async def trigger_touch_workflow():
    """
    Manually trigger the touch workflow
    (Same as physical touch sensor)
    """
    if not WORKFLOW_AVAILABLE:
        raise HTTPException(status_code=503, detail="Touch workflow not available")
    
    try:
        logger.info("🖐️  Manual touch workflow trigger via API")
        
        # Trigger workflow
        handle_touch_event()
        
        # Get status
        orchestrator = get_orchestrator()
        status = orchestrator.get_status()
        
        return TouchTriggerResponse(
            success=True,
            message="Touch workflow triggered successfully",
            workflow_status=status
        )
        
    except Exception as e:
        logger.error(f"Failed to trigger workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=WorkflowStatusResponse)
async def get_workflow_status():
    """
    Get current workflow status
    """
    if not WORKFLOW_AVAILABLE:
        raise HTTPException(status_code=503, detail="Touch workflow not available")
    
    try:
        orchestrator = get_orchestrator()
        status = orchestrator.get_status()
        
        return WorkflowStatusResponse(
            success=True,
            status=status
        )
        
    except Exception as e:
        logger.error(f"Failed to get status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-tts")
async def test_tts():
    """
    Test text-to-speech functionality
    """
    try:
        from services.tts_service import get_tts_service
        
        tts = get_tts_service()
        tts.speak("Text to speech test successful", blocking=False)
        
        return {"success": True, "message": "TTS test triggered"}
        
    except Exception as e:
        logger.error(f"TTS test failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
