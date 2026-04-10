# ESP32 WiFi - Final Diagnosis

## Current Status: ❌ WiFi Not Working

### What We Tested:
1. ✅ Disabled Wi-Fi Protected Setup on router
2. ✅ ESP32 can now see the network (RSSI -61 to -63 dBm - good signal)
3. ✅ ESP32 hardware working
4. ❌ **Authentication fails with reason 2 (AUTH_EXPIRE)**

### Root Cause:
**AT&T router still has WPA3/PMF security enabled despite WPS being off.**

The router's "WPA Version: WPA-2" setting is actually WPA2/WPA3-Mixed mode. AT&T firmware doesn't provide a pure WPA2-PSK option in some models.

### Disconnect Reason 2 (AUTH_EXPIRE):
- Authentication handshake times out
- Caused by PMF (Protected Management Frames) being required
- ESP32 Arduino core cannot complete WPA3/PMF handshake
- Your phone works because it supports WPA3

---

## ✅ WORKING SOLUTION: Use USB Serial (Current Setup)

Your plant monitor is **already working perfectly via USB serial**:

### Current Architecture:
```
ESP32 (USB) → MacBook → serial_reader.py → FastAPI → TimescaleDB → React Frontend
```

### Advantages:
- ✅ Already stable and working
- ✅ No WiFi compatibility issues
- ✅ Direct connection to development machine
- ✅ Easy debugging via serial monitor
- ✅ No router configuration needed

### To Use:
```bash
cd "/Users/kanchan/Plant Sensor Project/plant-monitor/backend"

# Terminal 1: Start backend
./start_backend.sh

# Terminal 2: Start serial reader
python serial_reader.py

# Terminal 3: Start frontend
cd ../frontend
npm run dev
```

---

## 🔧 Alternative WiFi Solutions

### Option 1: Use Guest Network (If Available)

Some AT&T routers allow weaker security on Guest network:

1. Enable Guest SSID on 2.4 GHz
2. Set Guest security to **WPA** (not WPA2)
3. Update ESP32 code with Guest credentials
4. Test connection

### Option 2: Use Phone Hotspot

For wireless deployment without router issues:

1. Create phone hotspot:
   - Name: `PlantMonitor`
   - Password: `plant1234`
   - Security: WPA2-PSK
   - Band: 2.4 GHz only

2. Update ESP32 code:
   ```cpp
   const char* WIFI_SSID = "PlantMonitor";
   const char* WIFI_PASSWORD = "plant1234";
   ```

3. Upload and test - should connect immediately

### Option 3: Different Router/Access Point

If you have another router or WiFi access point:

1. Configure with pure WPA2-PSK (not WPA3)
2. Disable PMF/802.11w
3. Set 2.4 GHz channel to 1, 6, or 11
4. Test ESP32 connection

### Option 4: Update Router Firmware

Some users report AT&T firmware updates add pure WPA2 option:

1. Check for router firmware updates
2. After update, look for "WPA2-Personal" or "WPA2-PSK" option
3. Avoid "WPA-2" which is WPA2/WPA3-Mixed

---

## 📋 Files Created for WiFi Testing

All these sketches are ready to use:

1. **`wifi_fix_step1_scan/`** - Network scanner
2. **`wifi_fix_step2_debug/`** - Connection debugger with error codes
3. **`wifi_fix_step3_production/`** - Full plant monitor with WiFi + sensor
4. **`wifi_test_no_sensor/`** - WiFi test without sensor requirement
5. **`wifi_aggressive_connect/`** - Optimized for difficult routers
6. **`monitor_esp32.sh`** - Serial monitor script

To use any sketch:
```bash
cd "/Users/kanchan/Plant Sensor Project"

# Upload (replace sketch_name with actual folder)
python3 -c "import serial; import time; s = serial.Serial('/dev/cu.usbserial-0001', 115200); s.setDTR(False); s.setRTS(True); time.sleep(0.1); s.setRTS(False); time.sleep(0.5); s.close()" && sleep 1 && arduino-cli upload --fqbn esp32:esp32:esp32 --port /dev/cu.usbserial-0001 sketch_name
```

---

## 🎯 Recommendation

**Continue using USB serial for your plant monitor.**

WiFi is not essential for this project since:
- MacBook is always running the backend
- USB provides stable, fast connection
- No security/compatibility issues
- Easy debugging and monitoring

If you need wireless in the future:
- Use phone hotspot (easiest)
- Or get a separate 2.4 GHz access point with pure WPA2-PSK

---

## Technical Details

### What We Learned:
- AT&T BGW routers enforce WPA3 transition mode
- "Wi-Fi Protected Setup: Off" helps but doesn't fully disable WPA3
- "WPA Version: WPA-2" dropdown is misleading (actually WPA2/WPA3-Mixed)
- ESP32 Arduino core 3.3.7 cannot handle WPA3/PMF-Required
- Signal strength is good (-61 dBm) - not a range issue
- Password is correct - not a credential issue

### Disconnect Codes Seen:
- **201**: SSID not found (fixed by disabling WPS)
- **36**: AUTH_LEAVE (transient during reconnect)
- **2**: AUTH_EXPIRE (persistent - WPA3/PMF incompatibility)
- **3**: AUTH_LEAVE (clean disconnect)

### ESP32 MAC Address:
`1c:c3:ab:f9:54:8c`

---

## Summary

Your ESP32 WiFi issue is a **router security incompatibility**, not an ESP32 problem. The AT&T router's firmware doesn't allow pure WPA2-PSK mode that ESP32 requires.

**Best solution: Keep using USB serial - it works perfectly.**
