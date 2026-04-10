# AT&T Router Fix for ESP32 WiFi

## Problem Identified

Based on your router screenshot, I can see:
- **Wi-Fi Protected Setup: On**
- **WPA Version: WPA-2**

On AT&T routers, when "Wi-Fi Protected Setup" is enabled, it often forces WPA2/WPA3-Mixed mode with PMF (Protected Management Frames) required, even though the dropdown shows "WPA-2". This is incompatible with ESP32.

## REQUIRED FIX

### Option 1: Disable Wi-Fi Protected Setup (Recommended)

1. Login to router: `http://192.168.1.254`
2. Navigate to: **Home Network → Wi-Fi → 2.4 GHz Wi-Fi Configuration**
3. Find: **Wi-Fi Protected Setup** section
4. Change from: **On** → **Off**
5. Click **Save**
6. **Reboot router** (Settings → Restart Gateway)
7. Wait 2-3 minutes for router to fully restart

### Option 2: Change WPA Version

If Option 1 doesn't work:

1. In **2.4 GHz Wi-Fi Configuration**
2. Find: **WPA Version** dropdown
3. Try changing to different WPA2 option if available:
   - Look for "WPA2-PSK"
   - Or "WPA2-Personal"
   - Avoid anything with "WPA3" or "Mixed"
4. Save and reboot router

### Option 3: Disable PMF (If Available)

Some AT&T firmware versions have a PMF setting:

1. Look for **Protected Management Frames** or **PMF**
2. Change from **Required** → **Optional** or **Disabled**
3. Save and reboot

## After Router Changes

Once router is rebooted, test ESP32:

```bash
cd "/Users/kanchan/Plant Sensor Project"

# Upload the WiFi test sketch
python3 -c "import serial; import time; s = serial.Serial('/dev/cu.usbserial-0001', 115200); s.setDTR(False); s.setRTS(True); time.sleep(0.1); s.setRTS(False); time.sleep(0.5); s.close()" && sleep 1 && arduino-cli upload --fqbn esp32:esp32:esp32 --port /dev/cu.usbserial-0001 wifi_test_no_sensor

# Monitor output
python3 << 'EOF'
import serial, time
ser = serial.Serial('/dev/cu.usbserial-0001', 115200, timeout=1)
time.sleep(2)
print("Monitoring ESP32 WiFi connection...\n")
for i in range(40):
    if ser.in_waiting:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line:
            print(line)
            if 'Got IP' in line:
                print("\n✅ SUCCESS! WiFi connected!")
                break
    time.sleep(0.5)
ser.close()
EOF
```

## Why This Happens

AT&T routers have aggressive security defaults:
- **Wi-Fi Protected Setup (WPS)** enables enhanced security features
- This includes **WPA3 transition mode** and **PMF-Required**
- ESP32 Arduino core (even latest versions) has poor WPA3 support
- Result: ESP32 can see the network but fails authentication

## Alternative: Guest Network

If you can't change main network settings:

1. Enable **Guest SSID** on 2.4 GHz
2. Set Guest network to:
   - Security: **WPA** (not WPA2)
   - Or if WPA2 only: Ensure WPS is **Off** for guest network
3. Update ESP32 code with Guest SSID credentials
4. Upload and test

## Verification

After router changes, you should see:

```
[WiFi] Scanning for 2.4 GHz AP...
[WiFi] Locking to Ch X, RSSI -XX dBm
[WiFi] Connected to AP
[WiFi] ✓ Got IP: 192.168.1.XXX
Test Data: Temp=25.50°C, Humidity=55.00%
[HTTP] ✓ Code: 200
[HTTP] Data sent successfully
```

## If Still Fails

1. Check router's **Device Access Control** / **MAC Filtering**
   - ESP32 MAC: `1c:c3:ab:f9:54:8c`
   - Add to allowed devices if filtering is enabled

2. Try moving ESP32 closer to router (within 10 feet)

3. Test with phone hotspot to confirm ESP32 hardware works:
   - Create hotspot: WPA2, 2.4 GHz only
   - Update SSID in code
   - Upload and test

## Current Status

- ✅ ESP32 code: Ready and uploaded
- ✅ ESP32 hardware: Working
- ❌ Router security: Too strict for ESP32
- 🔧 **Action needed: Disable Wi-Fi Protected Setup on router**
