#!/usr/bin/env python3
"""
Test TTS multiple times to verify it works repeatedly
"""

import sys
import time
import logging

# Setup path
sys.path.insert(0, '/Users/kanchan/Plant Sensor Project/plant-monitor/backend')

from services.tts_service import get_tts_service

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

def test_multiple_tts():
    """Test TTS service multiple times"""
    logger.info("=" * 60)
    logger.info("Testing TTS Multiple Times")
    logger.info("=" * 60)
    
    tts = get_tts_service()
    
    # Test 5 times
    for i in range(1, 6):
        logger.info(f"\n🧪 Test {i}/5")
        tts.speak(f"Test number {i}", blocking=True)
        logger.info(f"✓ Test {i} completed")
        time.sleep(1)
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ All TTS tests completed successfully!")
    logger.info("=" * 60)

if __name__ == "__main__":
    test_multiple_tts()
