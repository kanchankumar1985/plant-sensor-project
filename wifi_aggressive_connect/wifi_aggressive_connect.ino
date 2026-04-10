#include <WiFi.h>
#include <HTTPClient.h>
#include "esp_wifi.h"

const char* WIFI_SSID = "ATTqCZIe2s_2G";
const char* WIFI_PASSWORD = "xf8psnrn3wb4";
const char* API_URL = "http://192.168.1.71:8000/api/readings";
const char* DEVICE_ID = "plant-esp32-01";

unsigned long lastReconnectAttempt = 0;
const unsigned long reconnectInterval = 10000; // Try every 10 seconds
bool wifiConnected = false;

void WiFiEvent(WiFiEvent_t event, WiFiEventInfo_t info) {
  switch (event) {
    case ARDUINO_EVENT_WIFI_STA_START:
      Serial.println("[WiFi] Started");
      break;
    case ARDUINO_EVENT_WIFI_STA_CONNECTED:
      Serial.println("[WiFi] ✓ Connected to AP");
      break;
    case ARDUINO_EVENT_WIFI_STA_GOT_IP:
      Serial.printf("[WiFi] ✓✓ Got IP: %s (RSSI: %d dBm)\n", 
                    WiFi.localIP().toString().c_str(), WiFi.RSSI());
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
  Serial.println("[WiFi] Attempting connection...");
  Serial.printf("  SSID: %s\n", WIFI_SSID);
  
  // Aggressive connection settings
  WiFi.disconnect(true);
  delay(100);
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(WIFI_PS_NONE);  // Disable power save
  WiFi.setTxPower(WIFI_POWER_19_5dBm);  // Max TX power
  WiFi.setHostname(DEVICE_ID);
  
  // Try direct connection first (no scan lock)
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  unsigned long start = millis();
  int attempts = 0;
  
  while (WiFi.status() != WL_CONNECTED && millis() - start < 30000) {
    delay(500);
    attempts++;
    
    if (attempts % 10 == 0) {
      Serial.printf("  [%d] Status: %d, RSSI: %d\n", attempts/2, WiFi.status(), WiFi.RSSI());
    }
    
    // If stuck, retry connection
    if (attempts == 40) {
      Serial.println("  Retrying connection...");
      WiFi.disconnect();
      delay(1000);
      WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    }
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("[WiFi] ✓ SUCCESS! IP=%s, RSSI=%d dBm\n",
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
  Serial.println("\n========== ESP32 Aggressive WiFi Connect ==========");
  Serial.println("Optimized for weak signals and difficult routers\n");
  
  WiFi.onEvent(WiFiEvent);
  WiFi.persistent(false);
  
  connectWiFi();
}

void loop() {
  // Auto-reconnect
  if (!wifiConnected && millis() - lastReconnectAttempt > reconnectInterval) {
    Serial.println("\n[Reconnect] Attempting...");
    connectWiFi();
    lastReconnectAttempt = millis();
  }
  
  // Send test data if connected
  if (wifiConnected) {
    float temp = 25.5;
    float hum = 55.0;
    
    Serial.println("------");
    Serial.printf("Test: Temp=%.1f°C, Hum=%.1f%%, RSSI=%d dBm\n", temp, hum, WiFi.RSSI());
    
    HTTPClient http;
    http.setTimeout(5000);
    http.begin(API_URL);
    http.addHeader("Content-Type", "application/json");
    
    String payload = "{";
    payload += "\"device_id\":\"" + String(DEVICE_ID) + "\",";
    payload += "\"temperature_c\":" + String(temp, 2) + ",";
    payload += "\"humidity_pct\":" + String(hum, 2);
    payload += "}";
    
    int httpCode = http.POST(payload);
    
    if (httpCode > 0) {
      Serial.printf("[HTTP] Code: %d", httpCode);
      if (httpCode == 200 || httpCode == 201) {
        Serial.println(" ✓ Success");
      } else {
        Serial.println();
      }
    } else {
      Serial.printf("[HTTP] Error: %s\n", http.errorToString(httpCode).c_str());
    }
    
    http.end();
  } else {
    Serial.println("[HTTP] Skipped - no WiFi");
  }
  
  delay(5000);
}
