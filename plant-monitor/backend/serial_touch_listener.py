#!/usr/bin/env python3
"""
Serial Touch Listener
Monitors ESP32 serial port for TOUCHED events and triggers workflow
"""

import serial
import serial.tools.list_ports
import time
import logging
from datetime import datetime
from pathlib import Path
import sys

# Setup logging
from logging_config import get_camera_logger
logger = get_camera_logger()

# Import workflow orchestrator
from services.touch_workflow import handle_touch_event, get_orchestrator

# Serial configuration
SERIAL_BAUD = 115200
SERIAL_TIMEOUT = 1.0
RECONNECT_DELAY = 5  # seconds


def find_esp32_port():
    """
    Auto-detect ESP32 serial port
    
    Returns:
        Port name or None if not found
    """
    ports = serial.tools.list_ports.comports()
    
    # Look for common ESP32 identifiers
    esp32_keywords = ['CP2102', 'CH340', 'USB-SERIAL', 'UART', 'ESP32']
    
    for port in ports:
        port_desc = (port.description or '').upper()
        port_hwid = (port.hwid or '').upper()
        
        for keyword in esp32_keywords:
            if keyword in port_desc or keyword in port_hwid:
                logger.info(f"✓ Found ESP32 port: {port.device} ({port.description})")
                return port.device
    
    # If no match, list all ports for manual selection
    if ports:
        logger.warning("ESP32 not auto-detected. Available ports:")
        for port in ports:
            logger.warning(f"  - {port.device}: {port.description}")
        
        # Return first port as fallback
        return ports[0].device
    
    return None


def connect_serial(port=None):
    """
    Connect to ESP32 serial port
    
    Args:
        port: Serial port name (auto-detect if None)
        
    Returns:
        Serial connection or None
    """
    if port is None:
        port = find_esp32_port()
    
    if not port:
        logger.error("❌ No serial port found")
        return None
    
    try:
        logger.info(f"🔌 Connecting to {port} at {SERIAL_BAUD} baud...")
        ser = serial.Serial(port, SERIAL_BAUD, timeout=SERIAL_TIMEOUT)
        time.sleep(2)  # Wait for ESP32 to reset
        
        # Flush any startup messages
        ser.reset_input_buffer()
        
        logger.info(f"✓ Connected to {port}")
        return ser
        
    except serial.SerialException as e:
        logger.error(f"❌ Serial connection failed: {e}")
        return None


def listen_for_touch_events(port=None):
    """
    Main loop: listen for TOUCHED events and trigger workflow
    
    Args:
        port: Serial port name (auto-detect if None)
    """
    logger.info("=" * 60)
    logger.info("🎧 SERIAL TOUCH LISTENER STARTED")
    logger.info("=" * 60)
    logger.info("Waiting for touch events from ESP32...")
    logger.info("Press Ctrl+C to stop")
    logger.info("")
    
    ser = None
    last_reconnect_attempt = 0
    
    try:
        while True:
            # Connect or reconnect
            if ser is None or not ser.is_open:
                current_time = time.time()
                if current_time - last_reconnect_attempt >= RECONNECT_DELAY:
                    ser = connect_serial(port)
                    last_reconnect_attempt = current_time
                    
                    if ser is None:
                        logger.warning(f"⏳ Retrying in {RECONNECT_DELAY} seconds...")
                        time.sleep(RECONNECT_DELAY)
                        continue
            
            try:
                # Read line from serial
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    
                    if not line:
                        continue
                    
                    # Log all serial messages
                    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                    logger.info(f"[{timestamp}] Serial: {line}")
                    
                    # Check for TOUCHED event
                    if line == "TOUCHED":
                        logger.info("")
                        logger.info("🖐️" * 20)
                        logger.info("TOUCH EVENT DETECTED!")
                        logger.info("🖐️" * 20)
                        logger.info("")
                        
                        # Trigger workflow
                        handle_touch_event()
                        
                        # Log status after trigger
                        time.sleep(0.5)
                        orchestrator = get_orchestrator()
                        status = orchestrator.get_status()
                        logger.info(f"Workflow status: {status['status']}")
                        logger.info("")
                
                # Small delay to prevent CPU spinning
                time.sleep(0.01)
                
            except serial.SerialException as e:
                logger.error(f"❌ Serial read error: {e}")
                if ser:
                    ser.close()
                ser = None
                time.sleep(RECONNECT_DELAY)
            
            except UnicodeDecodeError as e:
                logger.warning(f"⚠️  Decode error: {e}")
                continue
    
    except KeyboardInterrupt:
        logger.info("")
        logger.info("=" * 60)
        logger.info("🛑 STOPPING SERIAL LISTENER")
        logger.info("=" * 60)
        
        if ser and ser.is_open:
            ser.close()
            logger.info("✓ Serial port closed")
    
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}", exc_info=True)
        if ser and ser.is_open:
            ser.close()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Serial Touch Listener for Plant Monitor')
    parser.add_argument('--port', type=str, help='Serial port (auto-detect if not specified)')
    parser.add_argument('--test-tts', action='store_true', help='Test TTS and exit')
    parser.add_argument('--test-workflow', action='store_true', help='Test workflow and exit')
    
    args = parser.parse_args()
    
    # Test TTS
    if args.test_tts:
        logger.info("Testing TTS...")
        from services.tts_service import get_tts_service
        tts = get_tts_service()
        tts.test()
        return
    
    # Test workflow
    if args.test_workflow:
        logger.info("Testing workflow...")
        handle_touch_event()
        time.sleep(15)
        orchestrator = get_orchestrator()
        status = orchestrator.get_status()
        logger.info(f"Workflow status: {status}")
        return
    
    # Start listener
    listen_for_touch_events(port=args.port)


if __name__ == "__main__":
    main()
