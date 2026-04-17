# TTS Fix Summary

## Problem
Text-to-Speech (TTS) was only working once, then failing on subsequent touch events.

## Root Cause
The `pyttsx3` library has known threading issues when:
1. The same engine instance is reused across multiple threads
2. `runAndWait()` is called multiple times on the same engine instance

## Solution
Modified `@/Users/kanchan/Plant Sensor Project/plant-monitor/backend/services/tts_service.py:59-85` to:

1. **Reinitialize engine for each speech**: Create a fresh `pyttsx3` engine instance for every TTS call
2. **Proper cleanup**: Call `engine.stop()` and delete the engine after each use
3. **Error recovery**: Reinitialize main engine if any errors occur

### Code Changes

```python
def _speak_blocking(self, text: str):
    """Speak text (blocking call)"""
    with self.lock:
        try:
            logger.info(f"🔊 Speaking: '{text}'")
            
            # Reinitialize engine for each speech to avoid threading issues
            # This is a known workaround for pyttsx3
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)
            engine.setProperty('volume', 0.9)
            
            engine.say(text)
            engine.runAndWait()
            
            # Clean up
            engine.stop()
            del engine
            
            logger.info(f"✓ Speech completed")
        except Exception as e:
            logger.error(f"Speech failed: {e}")
            # Try to reinitialize main engine on error
            try:
                self._initialize_engine()
            except:
                pass
```

## Testing
Created `test_tts_multiple.py` to verify TTS works repeatedly:

```bash
cd /Users/kanchan/Plant\ Sensor\ Project/plant-monitor/backend
source .venv/bin/activate
python3 test_tts_multiple.py
```

**Test Results**: ✅ Successfully spoke 5 times in a row

```
🧪 Test 1/5 - ✓ Speech completed
🧪 Test 2/5 - ✓ Speech completed
🧪 Test 3/5 - ✓ Speech completed
🧪 Test 4/5 - ✓ Speech completed
🧪 Test 5/5 - ✓ Speech completed
```

## Additional Improvements

### Serial Line Filtering
Also improved `serial_unified_listener.py` to filter out truncated/partial serial lines:

```python
# Only log complete messages that start with known prefixes
if line.startswith('DEBUG:') or line.startswith('INFO:') or \
   line.startswith('ERROR:') or line.startswith('TOUCH') or \
   line.startswith('✓') or line.startswith('❌'):
    logger.info(f"{line}")
```

This prevents log spam from incomplete JSON fragments.

## Verification

To verify the fix is working:

1. **Start the unified listener:**
   ```bash
   ./start_unified_listener.sh
   ```

2. **Touch the sensor multiple times** - you should hear "Sensor touched" each time

3. **Check logs** - you should see:
   ```
   🔊 Speaking: 'Sensor touched'
   ✓ Speech completed
   ```

## Status
✅ **FIXED** - TTS now works reliably for multiple touch events

## Files Modified
1. `services/tts_service.py` - Fixed TTS engine reinitialization
2. `serial_unified_listener.py` - Improved serial line filtering

## Files Created
1. `test_tts_multiple.py` - TTS testing utility
