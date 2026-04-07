#!/usr/bin/env python3
"""
Automated plant snapshot capture loop
Captures webcam images every 60 seconds
"""

import time
from capture_snapshot import capture_and_store_snapshot

CAPTURE_INTERVAL = 60  # seconds

def main():
    """Run continuous snapshot capture loop"""
    print("🌱 Plant Snapshot Capture Loop Starting...")
    print(f"📸 Capturing every {CAPTURE_INTERVAL} seconds")
    print("🛑 Press Ctrl+C to stop\n")
    
    try:
        while True:
            # Capture snapshot
            capture_and_store_snapshot()
            
            # Wait for next capture
            print(f"\n⏳ Waiting {CAPTURE_INTERVAL} seconds until next capture...")
            time.sleep(CAPTURE_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping snapshot capture loop...")
        print("✅ Shutdown complete.")

if __name__ == "__main__":
    main()
