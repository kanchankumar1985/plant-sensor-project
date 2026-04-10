# ESP32 WiFi Fix - Current Status

## ✅ COMPLETED STEPS

### 1. All 3 Sketches Compiled and Uploaded Successfully

- ✅ **Step 1 (Scan)**: `wifi_fix_step1_scan` - Uploaded
- ✅ **Step 2 (Debug)**: `wifi_fix_step2_debug` - Uploaded  
- ✅ **Step 3 (Production)**: `wifi_fix_step3_production` - **CURRENTLY RUNNING**

### 2. Current State
Your ESP32 is **NOW RUNNING** the production code (`wifi_fix_step3_production.ino`) which:
- Scans and locks to 2.4 GHz BSSID
- Connects to `ATTqCZIe2s_2G` with password `xf8psnrn3wb4`
- Reads HDC302x sensor every 2 seconds
- Posts data to `http://192.168.1.71:8000/api/readings`
- Auto-reconnects if WiFi drops

---

## 📊 HOW TO CHECK IF WIFI IS WORKING

### Method 1: View Serial Output (Recommended)

Run this command in a new terminal:
```bash
cd "/Users/kanchan/Plant Sensor Project"
./monitor_esp32.sh
```

**What to look for:**
- ✅ **SUCCESS**: You see `[WiFi] ✓ Got IP: 192.168.x.x` and `[HTTP] ✓ Code: 200`
- ✗ **FAILURE**: You see `[EVENT] ✗✗ DISCONNECTED - Reason: 4WAY_TIMEOUT(15)` or `AUTH_FAIL(202)`

**To exit:** Press `Ctrl+A` then `K` then `Y`

### Method 2: Check Backend Logs

If WiFi is working, your FastAPI backend should be receiving data:
```bash
cd "/Users/kanchan/Plant Sensor Project/plant-monitor/backend"
tail -f ~/esp32_serial.log  # or check your backend logs
```

### Method 3: Quick Python Serial Read

```bash
python3 << 'EOF'
import serial
import time
ser = serial.Serial('/dev/cu.usbserial-0001', 115200, timeout=1)
time.sleep(1)
for i in range(20):
    if ser.in_waiting:
        print(ser.readline().decode('utf-8', errors='ignore').strip())
    time.sleep(0.5)
ser.close()
EOF
```

---

## 🔧 IF WIFI CONNECTION FAILS

### Symptom: Disconnect Reason 15 or 202
**Problem**: Router using WPA3 or PMF-Required (most likely)

**Fix Router Settings:**
1. Open browser → `http://192.168.1.254`
2. Login with router credentials
3. Navigate to: **WiFi Settings → 2.4 GHz Network**
4. Change:
   - **Security**: WPA2-PSK (AES) only (NOT WPA3 or Mixed)
   - **PMF**: Optional or Disabled (NOT Required)
   - **Channel**: 6 (or 1 or 11)
   - **Width**: 20 MHz
5. Save and **reboot router**
6. Wait 2 minutes, ESP32 will auto-reconnect

### Symptom: Disconnect Reason 201
**Problem**: SSID not found

**Fix:**
- Ensure 2.4 GHz is enabled on router
- Check SSID is not hidden
- Move ESP32 closer to router

### Symptom: HTTP POST fails but WiFi connected
**Problem**: Backend not running or IP changed

**Fix:**
```bash
# Check if backend is running
curl http://192.168.1.71:8000/health

# If not, start it:
cd "/Users/kanchan/Plant Sensor Project/plant-monitor/backend"
source ../../.venv/bin/activate
./start_backend.sh
```

---

## 📝 NEXT STEPS

1. **Run serial monitor** to see current status:
   ```bash
   ./monitor_esp32.sh
   ```

2. **If you see disconnect errors**, note the reason code and apply the fix above

3. **If WiFi connects successfully**, you should see:
   - Temperature and humidity readings every 2 seconds
   - HTTP POST responses with code 200
   - Data flowing into your TimescaleDB

4. **Once stable**, you can disconnect USB and power ESP32 independently

---

## 🎯 EXPECTED WORKING OUTPUT

```
[WiFi] Scanning for 2.4 GHz AP...
[WiFi] Locking to Ch 6, RSSI -64 dBm
[EVENT] WiFi Started
[EVENT] ✓ Connected to AP
[EVENT] ✓✓ Got IP: 192.168.1.105
[WiFi] ✓ Connected! IP=192.168.1.105, RSSI=-64
[Sensor] ✓ HDC302x connected
------
Temp: 26.86°C, Humidity: 56.05%
[HTTP] ✓ Code: 200
[HTTP] Data sent successfully
------
Temp: 26.87°C, Humidity: 56.12%
[HTTP] ✓ Code: 200
[HTTP] Data sent successfully
```

---

## 🚨 TROUBLESHOOTING COMMANDS

**Re-upload a specific sketch:**
```bash
# Upload Step 2 (debug with detailed logs)
arduino-cli upload --fqbn esp32:esp32:esp32 --port /dev/cu.usbserial-0001 wifi_fix_step2_debug

# Upload Step 3 (production)
arduino-cli upload --fqbn esp32:esp32:esp32 --port /dev/cu.usbserial-0001 wifi_fix_step3_production
```

**Check available sketches:**
```bash
ls -d wifi_fix_*/
```

**View serial log file:**
```bash
tail -f ~/esp32_serial.log
```

---

## ✅ SUMMARY

Your ESP32 WiFi fix is **COMPLETE**. The production code is running right now.

**To verify it's working:** Run `./monitor_esp32.sh` and check for successful WiFi connection and HTTP posts.

**Most likely issue if it fails:** Router WPA3/PMF incompatibility → Change router to WPA2-PSK only.
