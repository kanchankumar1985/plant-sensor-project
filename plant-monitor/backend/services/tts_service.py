"""
Text-to-Speech Service
Uses macOS native 'say' command for reliable laptop speaker output
"""

import subprocess
import threading
import logging
from typing import Optional
import platform

logger = logging.getLogger(__name__)

class TTSService:
    """Local text-to-speech using laptop speakers"""
    
    def __init__(self):
        self.engine = None
        self.lock = threading.Lock()
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Check if macOS 'say' command is available"""
        try:
            # Check if we're on macOS
            if platform.system() == 'Darwin':
                # Test if 'say' command works
                result = subprocess.run(['which', 'say'], capture_output=True, text=True)
                if result.returncode == 0:
                    self.engine = 'macos_say'
                    logger.info("✓ TTS engine initialized (macOS 'say' command)")
                else:
                    logger.warning("macOS 'say' command not found")
                    self.engine = None
            else:
                logger.warning("Non-macOS system - TTS not available")
                self.engine = None
            
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            self.engine = None
    
    def speak(self, text: str, blocking: bool = False):
        """
        Speak text through laptop speakers
        
        Args:
            text: Text to speak
            blocking: If True, wait for speech to complete. If False, speak in background.
        """
        if not self.engine:
            logger.warning("TTS engine not available, skipping speech")
            return
        
        if blocking:
            self._speak_blocking(text)
        else:
            # Speak in background thread to avoid blocking
            thread = threading.Thread(target=self._speak_blocking, args=(text,), daemon=True)
            thread.start()
    
    def _speak_blocking(self, text: str):
        """Speak text (blocking call)"""
        with self.lock:
            try:
                logger.info(f"🔊 Speaking: '{text}'")
                
                # Use macOS 'say' command - much more reliable than pyttsx3
                result = subprocess.run(
                    ['say', '-r', '150', text],  # -r 150 = rate (words per minute)
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    logger.info(f"✓ Speech completed")
                else:
                    logger.error(f"Speech failed with code {result.returncode}: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                logger.error(f"Speech timed out after 10 seconds")
            except Exception as e:
                logger.error(f"Speech failed: {e}")
                # Try to reinitialize main engine on error
                try:
                    self._initialize_engine()
                except:
                    pass
    
    def speak_touch_event(self):
        """Speak the touch event message"""
        self.speak("Sensor touched", blocking=False)
    
    def speak_capture_started(self):
        """Speak capture started message"""
        self.speak("Capturing image", blocking=False)
    
    def speak_analysis_complete(self):
        """Speak analysis complete message"""
        self.speak("Analysis complete", blocking=False)
    
    def test(self):
        """Test TTS functionality"""
        logger.info("Testing TTS...")
        self.speak("Text to speech test successful", blocking=True)


# Singleton instance
_tts_service: Optional[TTSService] = None

def get_tts_service() -> TTSService:
    """Get or create TTS service singleton"""
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service


if __name__ == "__main__":
    # Test TTS
    logging.basicConfig(level=logging.INFO)
    tts = get_tts_service()
    tts.test()
