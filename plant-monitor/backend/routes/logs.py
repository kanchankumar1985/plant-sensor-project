"""
API routes for accessing system logs.
Provides endpoints to view and download log files.
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, PlainTextResponse
from typing import Optional
import logging_config

router = APIRouter(prefix="/api/logs", tags=["logs"])
logger = logging_config.get_api_logger()


@router.get("/latest")
async def get_latest_logs(limit: int = Query(default=100, ge=1, le=10000)):
    """
    Get the latest N log lines from the most recent log file.
    
    Args:
        limit: Number of lines to return (default: 100, max: 10000)
    
    Returns:
        JSON with log lines array
    """
    try:
        logger.info(f"Fetching latest {limit} log lines")
        lines = logging_config.get_latest_logs(lines=limit)
        
        return JSONResponse({
            "success": True,
            "count": len(lines),
            "lines": lines,
            "logs_dir": str(logging_config.LOGS_PATH)
        })
    
    except Exception as e:
        logger.error(f"Error fetching latest logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files")
async def list_log_files():
    """
    Get list of all available log files.
    
    Returns:
        JSON with array of log file metadata
    """
    try:
        logger.info("Listing all log files")
        files = logging_config.get_all_log_files()
        
        return JSONResponse({
            "success": True,
            "count": len(files),
            "files": files,
            "logs_dir": str(logging_config.LOGS_PATH)
        })
    
    except Exception as e:
        logger.error(f"Error listing log files: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/file/{filename}")
async def get_log_file(
    filename: str,
    lines: Optional[int] = Query(default=None, ge=1, le=100000)
):
    """
    Get content of a specific log file.
    
    Args:
        filename: Name of the log file (e.g., "app_20260413.log")
        lines: Optional number of lines to return from end of file
    
    Returns:
        Plain text content of the log file
    """
    try:
        logger.info(f"Reading log file: {filename} (lines: {lines or 'all'})")
        
        if lines:
            content_lines = logging_config.read_log_file(filename, lines=lines)
        else:
            # Read entire file
            content_lines = logging_config.read_log_file(filename, lines=1000000)
        
        if not content_lines:
            raise HTTPException(status_code=404, detail="Log file not found")
        
        content = "\n".join(content_lines)
        
        return PlainTextResponse(
            content=content,
            media_type="text/plain; charset=utf-8"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading log file {filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_log_stats():
    """
    Get statistics about the logging system.
    
    Returns:
        JSON with logging statistics
    """
    try:
        files = logging_config.get_all_log_files()
        
        total_size = sum(f['size'] for f in files)
        
        stats = {
            "success": True,
            "logs_dir": str(logging_config.LOGS_PATH),
            "total_files": len(files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "oldest_file": files[-1]['name'] if files else None,
            "newest_file": files[0]['name'] if files else None
        }
        
        logger.info(f"Log stats: {stats['total_files']} files, {stats['total_size_mb']} MB")
        
        return JSONResponse(stats)
    
    except Exception as e:
        logger.error(f"Error getting log stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
