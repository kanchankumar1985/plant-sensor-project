# Ollama Timeout Fix

## Issues Fixed

### 1. **Ollama Request Timeout (120 seconds)**
**Problem:** VLM analysis was timing out after 120 seconds
**Solution:** Increased timeout to 300 seconds (5 minutes)

### 2. **Pipeline Crash on VLM Failure**
**Problem:** When VLM failed, the code crashed with `AttributeError: 'NoneType' object has no attribute 'get'`
**Solution:** Added None check in `analysis_rules.py` to handle VLM failures gracefully

## Changes Made

### 1. Environment Variable (.env)
```bash
OLLAMA_TIMEOUT=300
```
- Increased from default 120s to 300s
- Gives VLM more time to analyze complex images
- Configurable per deployment

### 2. Error Handling (vlm/analysis_rules.py)
```python
def check_reliability(vlm_analysis, yolo_metadata=None):
    # Handle None or failed VLM analysis
    if vlm_analysis is None:
        return {
            "reliable": False,
            "confidence": "none",
            "reasons": ["VLM analysis failed or timed out"],
            "warnings": ["No VLM data available"]
        }
    # ... rest of function
```

### 3. Ollama Service Restart
- Killed stuck Ollama processes
- Restarted Ollama server cleanly
- Verified 2 models available (llava:7b, llama2:latest)

## How It Works Now

### Successful Analysis Flow:
1. Image captured → YOLO detection → VLM analysis (up to 300s)
2. VLM returns structured JSON
3. Rules engine validates reliability
4. Data saved to database
5. ✅ Success

### Timeout/Failure Flow:
1. Image captured → YOLO detection → VLM analysis starts
2. VLM times out after 300s OR fails
3. VLM returns None
4. Rules engine detects None, returns low reliability
5. Data still saved to database with "analysis failed" status
6. ⚠️ Graceful degradation (no crash)

## Testing

### Verify timeout setting:
```bash
cd /Users/kanchan/Plant\ Sensor\ Project/plant-monitor/backend
grep OLLAMA_TIMEOUT .env
# Should show: OLLAMA_TIMEOUT=300
```

### Verify Ollama is running:
```bash
curl http://localhost:11434/api/tags
# Should return JSON with models list
```

### Test VLM analysis:
```bash
source /Users/kanchan/Plant\ Sensor\ Project/.venv/bin/activate
python -c "from vlm.ollama_client import get_ollama_client; c = get_ollama_client(); print('Timeout:', c.timeout, 'seconds')"
# Should show: Timeout: 300 seconds
```

## Why Timeout Happened

### Possible Causes:
1. **Model loading**: First request loads model into memory (~4.7GB)
2. **Image size**: Large images (>500KB) take longer to process
3. **CPU inference**: No GPU acceleration on Mac (slower)
4. **Model complexity**: llava:7b is analyzing image + generating structured JSON
5. **Concurrent requests**: Multiple analyses queued

### Solutions Applied:
- ✅ Increased timeout to 300s
- ✅ Graceful error handling
- ✅ Ollama restart to clear stuck processes
- ✅ Model stays loaded after first use (faster subsequent requests)

## Performance Tips

### Speed up VLM analysis:
1. **Keep Ollama running**: First request is slow (model loading)
2. **Reduce image size**: Resize to 800x600 before analysis
3. **Use smaller model**: Consider `llava:13b` → `llava:7b` (already using smallest)
4. **Batch processing**: Analyze multiple images in sequence (model stays loaded)
5. **GPU acceleration**: Not available on Mac, but would help significantly

### Monitor performance:
```bash
# Check Ollama logs
tail -f ~/.ollama/logs/server.log

# Monitor memory usage
top -pid $(pgrep ollama)

# Check model size
ollama list
```

## Troubleshooting

### Still timing out after 300s?
1. Check Ollama logs: `~/.ollama/logs/server.log`
2. Restart Ollama: `pkill ollama && ollama serve`
3. Try smaller images: Resize to 640x480
4. Check system resources: `top` (CPU/memory)

### VLM returns None but no timeout?
1. Check Ollama connection: `curl http://localhost:11434/api/tags`
2. Verify model exists: `ollama list | grep llava`
3. Test manually: `ollama run llava:7b "describe this image"`

### Pipeline still crashes?
1. Check `analysis_rules.py` has None check (line 30-36)
2. Verify `.env` has `OLLAMA_TIMEOUT=300`
3. Restart serial_reader.py to reload environment

## Current Status

✅ **Timeout increased**: 120s → 300s
✅ **Error handling**: None checks added
✅ **Ollama restarted**: Clean state
✅ **Ready to test**: Run `python serial_reader.py`

The system will now:
- Wait up to 5 minutes for VLM analysis
- Gracefully handle timeouts without crashing
- Continue monitoring even if VLM fails
- Log all events to `logs/serial_reader_*.log`
