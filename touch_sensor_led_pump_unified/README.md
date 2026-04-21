# ESP32 Unified Plant Monitor - Automatic & Manual Pump Control

## Overview

This Arduino sketch provides **dual-mode pump control** for your ESP32 plant monitoring system:

1. **Manual Mode**: Touch sensor triggers pump
2. **Automatic Mode**: High temperature triggers pump
3. **Cooldown Protection**: Prevents excessive watering

## Hardware Setup

### Connections (Already Working)

- **Touch Sensor**: VCC→3.3V, GND→GND, S→GPIO4
- **LED Module**: VCC→3.3V, GND→GND, S→GPIO19
- **Pump MOSFET**: TRIG→GPIO5, GND→GND, VIN±→External 5V USB
- **HDC302X Sensor**: VCC→3.3V, GND→GND, SDA→GPIO21, SCL→GPIO22

## Configuration

### Default Settings

```cpp
TOUCH_PIN = 4
LED_PIN = 19
PUMP_PIN = 5
TEMP_THRESHOLD = 25.0°C
PUMP_DURATION = 2000ms (2 seconds)
PUMP_COOLDOWN = 30000ms (30 seconds)
```

### Logic Inversion

If your pump or LED behaves opposite to expected:

**For Pump (lines 35-36):**
```cpp
const bool PUMP_ACTIVE_HIGH = true;  // Change to false if pump is inverted
```

**For LED (lines 35-36):**
```cpp
const bool LED_ACTIVE_HIGH = true;   // Change to false if LED is inverted
```

## How It Works

### Manual Trigger (Touch Sensor)
1. Touch the sensor
2. Pump turns ON immediately
3. LED turns ON
4. Runs for 2 seconds
5. Both turn OFF
6. Cooldown starts (30 seconds)

### Automatic Trigger (Temperature)
1. Temperature exceeds 25.0°C
2. Cooldown period has passed
3. Pump turns ON automatically
4. LED turns ON
5. Runs for 2 seconds
6. Both turn OFF
7. Cooldown starts (30 seconds)

### Cooldown Protection
- After pump runs, it won't run again for 30 seconds
- Prevents over-watering
- Status messages show remaining cooldown time
- Manual touch trigger works even during cooldown

## Serial Output Examples

### Temperature Monitoring
```
Temperature: 26.1 °C
{"device_id":"ESP32_PLANT_01","temperature_c":26.07,"humidity_pct":52.44,"led_state":0,"pump_state":0,"timestamp":1069}
```

### Touch Trigger
```
TOUCHED
========================================
🚰 Pump ON due to: TOUCH
========================================
✓ Pump will run for 2 seconds
```

### Temperature Trigger
```
🔥 High temperature detected: 26.1 °C
========================================
🚰 Pump ON due to: HIGH TEMPERATURE
========================================
✓ Pump will run for 2 seconds
```

### Cooldown Status
```
Cooldown active (15 seconds remaining)
```

### Pump Stop
```
========================================
🛑 Pump OFF
========================================
```

## Testing Steps

### 1. Test Touch Trigger
- Upload the sketch
- Open Serial Monitor (115200 baud)
- Touch the sensor
- **Expected**: 
  - See "TOUCHED" message
  - See "Pump ON due to: TOUCH"
  - Pump runs for 2 seconds
  - LED lights up for 2 seconds
  - See "Pump OFF"
  - Cooldown starts

### 2. Test Temperature Trigger
- Wait for temperature to be above 25°C (or lower threshold in code)
- Wait for cooldown to expire
- **Expected**:
  - See "High temperature detected: X.X °C"
  - See "Pump ON due to: HIGH TEMPERATURE"
  - Pump runs for 2 seconds
  - LED lights up for 2 seconds
  - See "Pump OFF"
  - Cooldown starts

### 3. Test Cooldown Behavior
- Trigger pump (touch or temperature)
- Try to trigger again immediately
- **Expected**:
  - See "Cooldown active (X seconds remaining)"
  - Pump does not run until cooldown expires
  - Manual touch still works (overrides cooldown)

## Customization

### Change Temperature Threshold
```cpp
const float TEMP_THRESHOLD = 25.0;  // Change to your desired temperature
```

### Change Pump Duration
```cpp
const unsigned long PUMP_DURATION = 2000;  // Change to milliseconds (e.g., 5000 = 5 seconds)
```

### Change Cooldown Period
```cpp
const unsigned long PUMP_COOLDOWN = 30000;  // Change to milliseconds (e.g., 60000 = 1 minute)
```

## Integration with Python Listener

The sketch sends JSON data compatible with `serial_unified_listener.py`:

```json
{
  "device_id": "ESP32_PLANT_01",
  "temperature_c": 26.07,
  "humidity_pct": 52.44,
  "led_state": 0,
  "pump_state": 0,
  "timestamp": 1069
}
```

Start the listener:
```bash
cd plant-monitor/backend
./start_unified_listener.sh
```

## Troubleshooting

### Pump Not Running
1. Check MOSFET wiring (VIN+, VIN-, OUT+, OUT-)
2. Verify external 5V USB power is connected
3. Try inverting pump logic: `PUMP_ACTIVE_HIGH = false`

### LED Not Working
1. Check LED wiring (VCC, GND, S)
2. Try inverting LED logic: `LED_ACTIVE_HIGH = false`

### Temperature Not Reading
1. Check HDC302X wiring (SDA→21, SCL→22)
2. Verify I2C address (0x44)
3. Check Serial Monitor for "HDC302X sensor connected"

### Pump Runs Continuously
1. Increase cooldown: `PUMP_COOLDOWN = 60000` (1 minute)
2. Increase temperature threshold: `TEMP_THRESHOLD = 30.0`

## Features Summary

✅ Dual-mode pump control (manual + automatic)
✅ Temperature/humidity monitoring (HDC302X)
✅ Touch sensor trigger
✅ LED status indicator
✅ Cooldown protection
✅ JSON data output
✅ Detailed Serial logging
✅ Easy logic inversion
✅ Beginner-friendly code
✅ Compatible with Python listener

## Files

- `touch_sensor_led_pump_unified.ino` - Main Arduino sketch
- `README.md` - This documentation

## License

Open source - modify as needed for your project!
