#include <WiFi.h>

const char* authType(wifi_auth_mode_t auth) {
  switch (auth) {
    case WIFI_AUTH_OPEN: return "OPEN";
    case WIFI_AUTH_WEP: return "WEP";
    case WIFI_AUTH_WPA_PSK: return "WPA";
    case WIFI_AUTH_WPA2_PSK: return "WPA2";
    case WIFI_AUTH_WPA_WPA2_PSK: return "WPA+WPA2";
    case WIFI_AUTH_WPA2_ENTERPRISE: return "WPA2-ENT";
    case WIFI_AUTH_WPA3_PSK: return "WPA3";
    case WIFI_AUTH_WPA2_WPA3_PSK: return "WPA2+WPA3";
    default: return "UNKNOWN";
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n========== ESP32 WiFi Diagnostic - Step 1: Network Scan ==========");
  Serial.println("This will show all WiFi networks and identify issues\n");
  
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  delay(100);
  
  Serial.println("Scanning networks...");
  int n = WiFi.scanNetworks(false, true);
  
  Serial.printf("\nFound %d networks:\n\n", n);
  Serial.println("  # | SSID                         | Ch | RSSI | Auth            | BSSID             | Notes");
  Serial.println("----+------------------------------+----+------+-----------------+-------------------+------------------");
  
  bool found_target = false;
  
  for (int i = 0; i < n; i++) {
    String ssid = WiFi.SSID(i);
    int32_t rssi = WiFi.RSSI(i);
    int32_t channel = WiFi.channel(i);
    wifi_auth_mode_t auth = WiFi.encryptionType(i);
    String bssid = WiFi.BSSIDstr(i);
    
    String notes = "";
    bool is_target = (ssid == "ATTqCZIe2s_2G");
    
    if (is_target) {
      found_target = true;
      if (channel > 14) notes += "5GHz-PROBLEM! ";
      if (auth == WIFI_AUTH_WPA3_PSK || auth == WIFI_AUTH_WPA2_WPA3_PSK) notes += "WPA3-PROBLEM! ";
      if (rssi < -75) notes += "WEAK-SIGNAL! ";
      if (notes == "") notes = "OK";
      notes = " ← TARGET: " + notes;
    }
    
    Serial.printf("%3d | %-28s | %2d | %4d | %-15s | %s%s\n",
                  i+1, ssid.c_str(), channel, rssi, authType(auth), bssid.c_str(), notes.c_str());
  }
  
  Serial.println("\n========== DIAGNOSTIC RESULTS ==========");
  if (!found_target) {
    Serial.println("✗ PROBLEM: ATTqCZIe2s_2G not found!");
    Serial.println("  → Check: Is 2.4 GHz enabled on router?");
    Serial.println("  → Check: Is SSID hidden?");
    Serial.println("  → Check: ESP32 antenna connected?");
  } else {
    Serial.println("✓ Network ATTqCZIe2s_2G found");
    Serial.println("\nNext: Upload Step 2 sketch to test connection with event logging");
  }
}

void loop() {}
