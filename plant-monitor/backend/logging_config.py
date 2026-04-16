"""
Centralized logging configuration for Plant Monitor system.
Provides consistent logging across all backend components.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
import os
from dotenv import load_dotenv

load_dotenv()

# Get logs directory from environment or use default
LOGS_DIR = os.getenv('LOGS_DIR', str(Path(__file__).parent / 'logs'))
LOGS_PATH = Path(LOGS_DIR)

# Create logs directory if it doesn't exist
LOGS_PATH.mkdir(parents=True, exist_ok=True)

# Log format
LOG_FORMAT = '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Log file naming
def get_log_filename(component_name: str) -> Path:
    """Generate log filename with current date"""
    date_str = datetime.now().strftime('%Y%m%d')
    return LOGS_PATH / f"{component_name}_{date_str}.log"


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = True
) -> logging.Logger:
    """
    Create and configure a logger instance.
    
    Args:
        name: Logger name (usually module name or component name)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to write logs to file
        log_to_console: Whether to write logs to console
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler with rotation (max 10MB per file, keep 5 backups)
    if log_to_file:
        log_file = get_log_filename(name)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def get_all_log_files() -> list[dict]:
    """
    Get list of all log files in the logs directory.
    
    Returns:
        List of dicts with file info (name, size, modified_time)
    """
    log_files = []
    
    if not LOGS_PATH.exists():
        return log_files
    
    for log_file in sorted(LOGS_PATH.glob('*.log*'), key=lambda p: p.stat().st_mtime, reverse=True):
        stat = log_file.stat()
        log_files.append({
            'name': log_file.name,
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'path': str(log_file)
        })
    
    return log_files


def read_log_file(filename: str, lines: int = 100) -> list[str]:
    """
    Read last N lines from a log file safely.
    
    Args:
        filename: Log file name (not full path, just filename)
        lines: Number of lines to read from end
    
    Returns:
        List of log lines
    """
    # Sanitize filename to prevent path traversal
    safe_filename = Path(filename).name
    log_file = LOGS_PATH / safe_filename
    
    if not log_file.exists():
        return []
    
    if not log_file.is_file():
        return []
    
    # Check if file is within logs directory (security)
    try:
        log_file.resolve().relative_to(LOGS_PATH.resolve())
    except ValueError:
        return []
    
    # Read last N lines efficiently
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            all_lines = f.readlines()
            return [line.rstrip() for line in all_lines[-lines:]]
    except Exception as e:
        return [f"Error reading log file: {str(e)}"]


def get_latest_logs(lines: int = 100) -> list[str]:
    """
    Get latest log lines from the most recent log file.
    
    Args:
        lines: Number of lines to retrieve
    
    Returns:
        List of log lines
    """
    log_files = get_all_log_files()
    
    if not log_files:
        return ["No log files found"]
    
    # Get most recent log file
    latest_file = log_files[0]['name']
    return read_log_file(latest_file, lines)


# Pre-configured loggers for common components
def get_app_logger() -> logging.Logger:
    """Get logger for main FastAPI app"""
    return setup_logger('app', level=logging.INFO)


def get_serial_logger() -> logging.Logger:
    """Get logger for serial reader"""
    return setup_logger('serial_reader', level=logging.INFO)


def get_camera_logger() -> logging.Logger:
    """Get logger for camera/capture operations"""
    return setup_logger('camera', level=logging.INFO)


def get_yolo_logger() -> logging.Logger:
    """Get logger for YOLO detection"""
    return setup_logger('yolo', level=logging.INFO)


def get_vlm_logger() -> logging.Logger:
    """Get logger for VLM analysis"""
    return setup_logger('vlm', level=logging.INFO)


def get_db_logger() -> logging.Logger:
    """Get logger for database operations"""
    return setup_logger('database', level=logging.INFO)


def get_api_logger() -> logging.Logger:
    """Get logger for API routes"""
    return setup_logger('api', level=logging.INFO)


# Initialize logging system
def init_logging():
    """Initialize the logging system - call this at app startup"""
    print(f"📝 Logging initialized")
    print(f"📁 Logs directory: {LOGS_PATH}")
    print(f"📊 Log files will be created per component with date suffix")
    
    # Create a startup log entry
    logger = get_app_logger()
    logger.info("=" * 80)
    logger.info("Plant Monitor System Starting")
    logger.info(f"Logs directory: {LOGS_PATH}")
    logger.info("=" * 80)


if __name__ == "__main__":
    # Test the logging system
    init_logging()
    
    test_logger = setup_logger('test')
    test_logger.debug("This is a debug message")
    test_logger.info("This is an info message")
    test_logger.warning("This is a warning message")
    test_logger.error("This is an error message")
    
    print(f"\nLog files created:")
    for log_file in get_all_log_files():
        print(f"  - {log_file['name']} ({log_file['size']} bytes)")
