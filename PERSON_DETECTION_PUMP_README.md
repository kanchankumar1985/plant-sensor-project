# Person Detection Pump Control (Testing Mode)

## Overview

**TEMPORARY TESTING MODE**: The pump now triggers when a **person is detected** in the camera image, instead of yellow leaves.

This is for testing the complete workflow before switching back to yellow leaf detection.

## How It Works Now

### Complete Workflow:

```
1. Touch Sensor
   ↓
2. ESP32: "TOUCHED"
   ESP32: "VLM_ANALYSIS_REQUESTED"
   ↓
3. Python: Capture image
   Python: Run YOLO person detection
   ↓
4. Python: Check person_detected in database
   ↓
5. IF person_detected == True:
      Python → ESP32: "PUMP_ON_YELLOW_LEAVES"
      ESP32: Turn ON pump (2 seconds)
      ESP32: Turn ON LED (2 seconds)
   ELSE:
      Pump stays OFF
```

## Changes Made

### 1. Queue Cleaned ✅
- Marked 41 pending items as completed
- Fresh start for testing
- Queue status:
  - Queued: 0
  - Processing: 0
  - Completed: 4562
  - Failed: 2343

### 2. Logic Changed ✅
**Before:**
- Waited for VLM worker (30 seconds)
- Checked `yellowing_visible` field
- Triggered pump if yellow leaves detected

**Now:**
- No waiting for VLM worker
- Checks `person_detected` field immediately
- Triggers pump if person detected

## Testing Steps

### 1. Touch the Sensor

**Expected Logs:**
```
🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️
TOUCH EVENT DETECTED!
🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️🖐️

📸 Person detection requested - capturing image...
📸 Image captured: plant_20260420_221830.jpg
🔍 Running YOLO person detection...
👤 Person detected: True
👥 Person count: 1
✅ Image captured and person detection complete

🔍 Person Detection Result:
   Person detected: True
   Person count: 1
   Image: plant_20260420_221830.jpg

👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤
PERSON DETECTED IN IMAGE!
💧 Triggering pump...
👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤👤

========================================
🚰 Pump ON due to: YELLOW LEAVES DETECTED
========================================
✓ Pump will run for 2 seconds

[Pump runs for 2 seconds]

========================================
🛑 Pump OFF
========================================
```

### 2. If No Person in Frame

**Expected Logs:**
```
🔍 Person Detection Result:
   Person detected: False
   Person count: 0
   Image: plant_20260420_221830.jpg

✅ No person detected - pump will not run
```

## Database Query

The system now queries:
```sql
SELECT person_detected, person_count, image_path
FROM plant_snapshots
ORDER BY time DESC
LIMIT 1
```

Instead of:
```sql
SELECT yellowing_visible, vlm_analysis, vlm_summary
FROM plant_snapshots
WHERE analysis_status = 'completed'
ORDER BY time DESC
LIMIT 1
```

## Advantages for Testing

✅ **Instant Response** - No 30-second VLM wait
✅ **Reliable** - YOLO person detection is very accurate
✅ **Easy to Test** - Just stand in front of camera
✅ **Fast Iteration** - Test pump control immediately
✅ **No VLM Worker Needed** - Person detection happens during capture

## Switching Back to Yellow Leaves

When ready to switch back to yellow leaf detection:

1. **Update the query** in `serial_unified_listener.py`:
```python
# Change from:
query = """
SELECT person_detected, person_count, image_path
FROM plant_snapshots
ORDER BY time DESC
LIMIT 1
"""

# Back to:
query = """
SELECT yellowing_visible, vlm_analysis, vlm_summary
FROM plant_snapshots
WHERE analysis_status = 'completed'
ORDER BY time DESC
LIMIT 1
"""
```

2. **Update the condition**:
```python
# Change from:
if person_detected:

# Back to:
if yellowing_visible:
```

3. **Add VLM wait logic** back (30-second polling)

4. **Update log messages** from "PERSON DETECTED" to "YELLOW LEAVES DETECTED"

## Current Status

✅ Queue cleaned (0 pending)
✅ Person detection logic active
✅ Unified listener running
✅ ESP32 ready to receive commands
✅ Pump cooldown: 60 seconds

## Test Now!

**Touch the sensor and stand in front of the camera!**

The pump should:
1. Turn ON if you're in the frame
2. Stay OFF if you're not in the frame
3. Run for exactly 2 seconds
4. Respect 60-second cooldown

## Files Modified

1. `/Users/kanchan/Plant Sensor Project/plant-monitor/backend/serial_unified_listener.py`
   - Function: `check_yellow_leaves_and_pump()`
   - Changed to check `person_detected` instead of `yellowing_visible`
   - Removed VLM wait loop
   - Updated log messages

2. `/Users/kanchan/Plant Sensor Project/plant-monitor/backend/clean_vlm_queue.py`
   - New script to clean queue
   - Marks queued/processing as completed

## Summary

🎯 **Purpose**: Test pump control workflow with reliable person detection
⚡ **Speed**: Instant (no VLM wait)
🎮 **Easy Testing**: Just stand in front of camera
🔄 **Reversible**: Easy to switch back to yellow leaves

**Ready to test!** Touch the sensor! 🌱👤💧
