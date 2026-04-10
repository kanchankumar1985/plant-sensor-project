#include <WiFi.h>
#include "esp_wifi.h"

const char* WIFI_SSID = "ATTqCZIe2s_2G";
const char* WIFI_PASS = "xf8psnrn3wb4";

const char* reasonName(uint8_t reason) {
  switch (reason) {
    case WIFI_REASON_UNSPECIFIED: return "UNSPECIFIED(1)";
    case WIFI_REASON_AUTH_EXPIRE: return "AUTH_EXPIRE(2)";
    case WIFI_REASON_AUTH_LEAVE: return "AUTH_LEAVE(3)";
    case WIFI_REASON_ASSOC_EXPIRE: return "ASSOC_EXPIRE(4)";
    case WIFI_REASON_ASSOC_TOOMANY: return "ASSOC_TOOMANY(5)";
    case WIFI_REASON_NOT_AUTHED: return "NOT_AUTHED(6)";
    case WIFI_REASON_NOT_ASSOCED: return "NOT_ASSOCED(7)";
    case WIFI_REASON_ASSOC_LEAVE: return "ASSOC_LEAVE(8)";
    case WIFI_REASON_4WAY_HANDSHAKE_TIMEOUT: return "4WAY_TIMEOUT(15)★WPA3/PMF";
    case WIFI_REASON_GROUP_KEY_UPDATE_TIMEOUT: return "GROUP_KEY_TIMEOUT(16)";
    case WIFI_REASON_IE_IN_4WAY_DIFFERS: return "IE_DIFFERS(17)";
    case WIFI_REASON_GROUP_CIPHER_INVALID: return "GROUP_CIPHER(18)";
    case WIFI_REASON_PAIRWISE_CIPHER_INVALID: return "PAIRWISE_CIPHER(19)";
    case WIFI_REASON_AKMP_INVALID: return "AKMP_INVALID(20)";
    case WIFI_REASON_UNSUPP_RSN_IE_VERSION: return "RSN_VERSION(21)";
    case WIFI_REASON_INVALID_RSN_IE_CAP: return "RSN_CAP(22)";
    case WIFI_REASON_BEACON_TIMEOUT: return "BEACON_TIMEOUT(200)";
    case WIFI_REASON_NO_AP_FOUND: return "NO_AP_FOUND(201)★HIDDEN/BAND";
    case WIFI_REASON_AUTH_FAIL: return "AUTH_FAIL(202)★PASSWORD/WPA3";
    case WIFI_REASON_ASSOC_FAIL: return "ASSOC_FAIL(204)";
    case WIFI_REASON_HANDSHAKE_TIMEOUT: return "HANDSHAKE_TIMEOUT(204)";
    default: return "UNKNOWN";
  }
}

void WiFiEvent(WiFiEvent_t event, WiFiEventInfo_t info) {
  switch (event) {
    case ARDUINO_EVENT_WIFI_STA_START:
      Serial.println("[EVENT] WiFi Started");
      break;
    case ARDUINO_EVENT_WIFI_STA_CONNECTED:
      Serial.println("[EVENT] ✓ Connected to AP");
      break;
    case ARDUINO_EVENT_WIFI_STA_GOT_IP:
      Serial.printf("[EVENT] ✓✓ Got IP: %s\n", WiFi.localIP().toString().c_str());
      break;
    case ARDUINO_EVENT_WIFI_STA_DISCONNECTED: {
      uint8_t r = info.wifi_sta_disconnected.reason;
      Serial.printf("[EVENT] ✗✗ DISCONNECTED - Reason: %s\n", reasonName(r));
      Serial.println("\n>>> DIAGNOSIS:");
      if (r == 15 || r == 202) {
        Serial.println("    ROUTER SECURITY ISSUE DETECTED!");
        Serial.println("    → Router is using WPA3 or PMF-Required");
        Serial.println("    → ESP32 cannot handle this security mode");
        Serial.println("    FIX: Change router to WPA2-PSK (AES) only");
        Serial.println("         Disable WPA3 and set PMF to Optional/Off");
      } else if (r == 201) {
        Serial.println("    SSID NOT FOUND");
        Serial.println("    → Network hidden or 5 GHz only");
        Serial.println("    FIX: Ensure 2.4 GHz is enabled and broadcasting");
      } else if (r == 4 || r == 200) {
        Serial.println("    SIGNAL/INTERFERENCE ISSUE");
        Serial.println("    FIX: Move closer to router or change channel");
      }
      Serial.println();
      break;
    }
    default:
      break;
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n========== ESP32 WiFi Diagnostic - Step 2: Connection Test ==========");
  Serial.println("This will attempt connection and show detailed error codes\n");
  
  WiFi.onEvent(WiFiEvent);
  WiFi.persistent(false);
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.disconnect(true);
  delay(500);
  
  Serial.printf("Connecting to: %s\n", WIFI_SSID);
  Serial.println("Password: xf8psnrn3wb4");
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 25000) {
    Serial.printf("[STATUS] %d (t=%lu ms)\n", WiFi.status(), millis() - start);
    delay(1000);
  }
  
  Serial.println("\n========== RESULT ==========");
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("✓✓✓ CONNECTION SUCCESS ✓✓✓");
    Serial.printf("  IP: %s\n", WiFi.localIP().toString().c_str());
    Serial.printf("  RSSI: %d dBm\n", WiFi.RSSI());
    Serial.println("\nNext: Upload Step 3 (production code with auto-reconnect)");
  } else {
    Serial.printf("✗✗✗ CONNECTION FAILED ✗✗✗ (status=%d)\n", WiFi.status());
    Serial.println("\nCheck the DISCONNECTED event above for the exact problem.");
    Serial.println("Most likely: Router security needs to be changed to WPA2-PSK only");
  }
}

void loop() {
  delay(5000);
  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("[LOOP] Connected, RSSI=%d\n", WiFi.RSSI());
  } else {
    Serial.printf("[LOOP] Disconnected, status=%d\n", WiFi.status());
  }
}
