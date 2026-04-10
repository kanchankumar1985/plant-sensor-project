#include <WiFi.h>
#include <HTTPClient.h>
#include "esp_wifi.h"

// WiFi credentials
const char* WIFI_SSID = "ATTqCZIe2s_2G";
const char* WIFI_PASSWORD = "xf8psnrn3wb4";
const char* API_URL = "http://192.168.1.71:8000/api/readings";
const char* DEVICE_ID = "plant-esp32-01";

unsigned long lastReconnectAttempt = 0;
const unsigned long reconnectInterval = 30000;
bool wifiConnected = false;

// Find and lock to 2.4 GHz AP
bool scanAndLock2G() {
  Serial.println("[WiFi] Scanning for 2.4 GHz AP...");
  int n = WiFi.scanNetworks(false, true);
  
  int bestRSSI = -999;
  uint8_t bestBSSID[6];
  int bestChannel = 0;
  
  for (int i = 0; i < n; i++) {
    if (WiFi.SSID(i) == String(WIFI_SSID) && WiFi.channel(i) <= 14) {
      if (WiFi.RSSI(i) > bestRSSI) {
        bestRSSI = WiFi.RSSI(i);
        bestChannel = WiFi.channel(i);
        memcpy(bestBSSID, WiFi.BSSID(i), 6);
      }
    }
  }
  
  if (bestChannel == 0) {
    Serial.println("[WiFi] ERROR: 2.4 GHz SSID not found");
    return false;
  }
  
  Serial.printf("[WiFi] Locking to Ch %d, RSSI %d dBm\n", bestChannel, bestRSSI);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD, bestChannel, bestBSSID, true);
  return true;
}

void WiFiEvent(WiFiEvent_t event, WiFiEventInfo_t info) {
  switch (event) {
    case ARDUINO_EVENT_WIFI_STA_CONNECTED:
      Serial.println("[WiFi] Connected to AP");
      break;
    case ARDUINO_EVENT_WIFI_STA_GOT_IP:
      Serial.printf("[WiFi] ✓ Got IP: %s\n", WiFi.localIP().toString().c_str());
      wifiConnected = true;
      break;
    case ARDUINO_EVENT_WIFI_STA_DISCONNECTED:
      Serial.printf("[WiFi] Disconnected (reason=%d)\n", info.wifi_sta_disconnected.reason);
      wifiConnected = false;
      break;
    default:
      break;
  }
}

bool connectWiFi() {
  if (!scanAndLock2G()) return false;
  
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 20000) {
    delay(100);
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("[WiFi] ✓ Connected! IP=%s, RSSI=%d dBm\n",
                  WiFi.localIP().toString().c_str(), WiFi.RSSI());
    return true;
  } else {
    Serial.printf("[WiFi] ✗ Failed (status=%d)\n", WiFi.status());
    return false;
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n========== ESP32 WiFi Test (No Sensor) ==========");
  
  WiFi.onEvent(WiFiEvent);
  WiFi.persistent(false);
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.setHostname(DEVICE_ID);
  WiFi.disconnect(true);
  delay(500);
  
  connectWiFi();
}

void loop() {
  // Auto-reconnect if disconnected
  if (!wifiConnected && millis() - lastReconnectAttempt > reconnectInterval) {
    Serial.println("[WiFi] Reconnecting...");
    WiFi.disconnect();
    delay(100);
    connectWiFi();
    lastReconnectAttempt = millis();
  }
  
  // Send test data if connected
  if (wifiConnected) {
    // Simulate sensor data
    float temp = 25.5;
    float hum = 55.0;
    
    Serial.println("------");
    Serial.printf("Test Data: Temp=%.2f°C, Humidity=%.2f%%\n", temp, hum);
    
    HTTPClient http;
    http.begin(API_URL);
    http.addHeader("Content-Type", "application/json");
    
    String payload = "{";
    payload += "\"device_id\":\"" + String(DEVICE_ID) + "\",";
    payload += "\"temperature_c\":" + String(temp, 2) + ",";
    payload += "\"humidity_pct\":" + String(hum, 2);
    payload += "}";
    
    int httpCode = http.POST(payload);
    
    if (httpCode > 0) {
      Serial.printf("[HTTP] ✓ Code: %d\n", httpCode);
      if (httpCode == 200 || httpCode == 201) {
        Serial.println("[HTTP] Data sent successfully");
      }
    } else {
      Serial.printf("[HTTP] ✗ Error: %s\n", http.errorToString(httpCode).c_str());
    }
    
    http.end();
  } else {
    Serial.println("[HTTP] Skipped - WiFi not connected");
  }
  
  delay(5000);  // Send every 5 seconds
}
