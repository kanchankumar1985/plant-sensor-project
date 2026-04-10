# ESP32 WiFi Fix - Step-by-Step Instructions

## Problem
Your ESP32 cannot connect to AT&T router `ATTqCZIe2s_2G` - most likely due to WPA3/PMF security incompatibility.

## Solution Steps

### STEP 1: Diagnose the Network (5 minutes)

1. Open Arduino IDE
2. Open sketch: `wifi_fix_step1_scan/wifi_fix_step1_scan.ino`
3. Upload to ESP32
4. Open Serial Monitor (115200 baud)
5. **Look for**: Your network `ATTqCZIe2s_2G` in the scan results
6. **Check for problems**:
   - If channel > 14: Router is 5 GHz only (ESP32 needs 2.4 GHz)
   - If auth shows "WPA3" or "WPA2+WPA3": Security incompatibility
   - If RSSI < -75: Signal too weak

**Expected output:**
```
  3 | ATTqCZIe2s_2G                |  6 |  -58 | WPA2            | AA:BB:CC:DD:EE:FF ← TARGET: OK
```

If you see "WPA2+WPA3" or "WPA3" → **Router needs to be changed to WPA2-only**

---

### STEP 2: Test Connection with Detailed Logging (5 minutes)

1. Open sketch: `wifi_fix_step2_debug/wifi_fix_step2_debug.ino`
2. Upload to ESP32
3. Open Serial Monitor (115200 baud)
4. **Watch for disconnect events** - they will show the exact problem

**If you see:**
```
[EVENT] ✗✗ DISCONNECTED - Reason: 4WAY_TIMEOUT(15)★WPA3/PMF
>>> DIAGNOSIS:
    ROUTER SECURITY ISSUE DETECTED!
```

**Then you MUST fix the router settings** (see Step 2B below)

**If connection succeeds:**
```
✓✓✓ CONNECTION SUCCESS ✓✓✓
  IP: 192.168.1.105
  RSSI: -64 dBm
```

Then skip to Step 3.

---

### STEP 2B: Fix AT&T Router Settings (10 minutes)

**ONLY do this if Step 2 showed reason code 15 or 202**

1. Open browser → `http://192.168.1.254`
2. Login with router credentials (printed on router label)
3. Navigate to: **Settings → WiFi → 2.4 GHz Network**
4. **Change these settings:**
   - **Security Mode**: Change to **WPA2-PSK (AES)** only
     - Do NOT use "WPA2/WPA3-Mixed" or "WPA3"
   - **PMF (Protected Management Frames)**: Set to **Optional** or **Disabled**
     - Do NOT use "Required"
   - **Channel**: Set to **6** (or 1 or 11)
   - **Channel Width**: Set to **20 MHz** (not 40 MHz)
5. Click **Save**
6. **Reboot router** (unplug power, wait 10 seconds, plug back in)
7. Wait 2 minutes for router to fully boot
8. **Re-run Step 2** - connection should now succeed

---

### STEP 3: Upload Production Code (2 minutes)

1. Open sketch: `wifi_fix_step3_production/wifi_fix_step3_production.ino`
2. **Verify settings in code:**
   - Line 7: `const char* WIFI_SSID = "ATTqCZIe2s_2G";` ✓
   - Line 8: `const char* WIFI_PASSWORD = "xf8psnrn3wb4";` ✓
   - Line 11: Update `API_URL` if your Mac IP changed
3. Upload to ESP32
4. Open Serial Monitor (115200 baud)

**Expected output:**
```
[WiFi] Scanning for 2.4 GHz AP...
[WiFi] Locking to Ch 6, RSSI -64 dBm
[WiFi] Connected to AP
[WiFi] ✓ Got IP: 192.168.1.105
------
Temp: 26.86°C, Humidity: 56.05%
[HTTP] ✓ Code: 200
[HTTP] Data sent successfully
```

---

## What Each Sketch Does

### Step 1 (Scan):
- Shows all WiFi networks ESP32 can see
- Identifies if your network is 2.4 GHz or 5 GHz
- Shows security type (WPA2, WPA3, etc.)
- Shows signal strength

### Step 2 (Debug):
- Attempts connection with detailed event logging
- Shows exact disconnect reason codes
- Tells you what the problem is and how to fix it

### Step 3 (Production):
- Scans and locks to 2.4 GHz BSSID (prevents band steering issues)
- Auto-reconnects if WiFi drops
- Reads HDC302x sensor
- Posts data to FastAPI every 2 seconds
- Production-ready code for your plant monitor

---

## Troubleshooting

**"Network not found in scan"**
- Ensure 2.4 GHz is enabled on router
- Check SSID is not hidden
- Move ESP32 closer to router

**"Reason: 4WAY_TIMEOUT(15) or AUTH_FAIL(202)"**
- Router security is WPA3 or has PMF-Required
- **Fix**: Change router to WPA2-PSK (AES) only, PMF Optional/Off

**"Reason: NO_AP_FOUND(201)"**
- SSID hidden or 5 GHz only
- **Fix**: Enable 2.4 GHz broadcasting on router

**"Connection works but HTTP POST fails"**
- Check Mac IP address hasn't changed
- Ensure FastAPI backend is running: `uvicorn app:app --reload --port 8000`
- Check firewall isn't blocking ESP32

---

## Quick Reference: AT&T Router Settings

**Optimal settings for ESP32:**
- Security: WPA2-PSK (AES) only
- PMF: Optional or Disabled
- Channel: 1, 6, or 11
- Width: 20 MHz
- Band Steering: Disabled (or use separate SSIDs for 2.4/5 GHz)

---

## After WiFi is Working

Once Step 3 works reliably:
1. Let it run for 24 hours to ensure stability
2. Monitor Serial output for disconnects
3. If stable, you can remove USB cable and power ESP32 independently
4. Data will continue posting to your FastAPI/TimescaleDB

---

## Need Help?

If you get stuck:
1. Copy the full Serial Monitor output from Step 2
2. Look for the disconnect reason code
3. Match it to the troubleshooting section above
4. Most issues are fixed by changing router to WPA2-PSK only
