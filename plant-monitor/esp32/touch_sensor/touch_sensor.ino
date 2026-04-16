/*
 * Keyes Capacitive Touch Sensor with ESP32
 * 
 * Hardware:
 * - Touch Sensor VCC → ESP32 3.3V
 * - Touch Sensor GND → ESP32 GND
 * - Touch Sensor S → ESP32 GPIO4
 * 
 * Features:
 * - Debounced touch detection
 * - Serial output for debugging
 * - HTTP POST to backend when state changes
 * - WiFi auto-reconnect
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ===== CONFIGURATION =====
const char* WIFI_SSID = "YOUR_WIFI_SSID";        // Replace with your WiFi name
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"; // Replace with your WiFi password
const char* BACKEND_URL = "http://192.168.1.100:8000/api/touch-event"; // Replace with your laptop IP

const int TOUCH_PIN = 4;           // GPIO4 for touch sensor
const int DEBOUNCE_MS = 50;        // Debounce delay
const int WIFI_RETRY_DELAY = 5000; // WiFi retry interval
const bool SERIAL_ONLY_MODE = false; // Set true to disable WiFi for testing

// ===== STATE VARIABLES =====
int lastTouchState = LOW;
int currentTouchState = LOW;
unsigned long lastDebounceTime = 0;
bool wifiConnected = false;

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n=== Touch Sensor Starting ===");
  
  // Configure touch sensor pin
  pinMode(TOUCH_PIN, INPUT);
  
  // Initialize WiFi if not in serial-only mode
  if (!SERIAL_ONLY_MODE) {
    connectWiFi();
  } else {
    Serial.println("[MODE] Serial-only mode enabled (WiFi disabled)");
  }
  
  Serial.println("[READY] Touch sensor initialized");
  Serial.println("Touch the sensor to test...\n");
}

void loop() {
  // Read current sensor state
  int reading = digitalRead(TOUCH_PIN);
  
  // Debounce logic
  if (reading != lastTouchState) {
    lastDebounceTime = millis();
  }
  
  if ((millis() - lastDebounceTime) > DEBOUNCE_MS) {
    // State has been stable for debounce period
    if (reading != currentTouchState) {
      currentTouchState = reading;
      handleStateChange(currentTouchState);
    }
  }
  
  lastTouchState = reading;
  
  // Check WiFi connection periodically
  if (!SERIAL_ONLY_MODE && !wifiConnected) {
    static unsigned long lastWiFiCheck = 0;
    if (millis() - lastWiFiCheck > WIFI_RETRY_DELAY) {
      lastWiFiCheck = millis();
      connectWiFi();
    }
  }
  
  delay(10); // Small delay to prevent CPU hogging
}

void handleStateChange(int state) {
  String stateStr = (state == HIGH) ? "TOUCHED" : "NOT_TOUCHED";
  
  // Print to Serial Monitor
  Serial.print("[STATE] ");
  Serial.println(stateStr);
  
  // Send to backend if WiFi is connected
  if (!SERIAL_ONLY_MODE && wifiConnected) {
    sendTouchEvent(stateStr);
  }
}

void connectWiFi() {
  Serial.print("[WiFi] Connecting to ");
  Serial.print(WIFI_SSID);
  Serial.print("...");
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    Serial.println(" Connected!");
    Serial.print("[WiFi] IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    wifiConnected = false;
    Serial.println(" Failed!");
    Serial.println("[WiFi] Will retry in 5 seconds");
  }
}

void sendTouchEvent(String state) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[HTTP] WiFi not connected, skipping POST");
    wifiConnected = false;
    return;
  }
  
  HTTPClient http;
  http.begin(BACKEND_URL);
  http.addHeader("Content-Type", "application/json");
  
  // Create JSON payload
  StaticJsonDocument<200> doc;
  doc["timestamp"] = getISOTimestamp();
  doc["state"] = state;
  
  String jsonPayload;
  serializeJson(doc, jsonPayload);
  
  Serial.print("[HTTP] Sending: ");
  Serial.println(jsonPayload);
  
  int httpCode = http.POST(jsonPayload);
  
  if (httpCode > 0) {
    Serial.print("[HTTP] Response code: ");
    Serial.println(httpCode);
    
    if (httpCode == 200 || httpCode == 201) {
      String response = http.getString();
      Serial.print("[HTTP] Response: ");
      Serial.println(response);
    }
  } else {
    Serial.print("[HTTP] Error: ");
    Serial.println(http.errorToString(httpCode));
  }
  
  http.end();
}

String getISOTimestamp() {
  // Simple timestamp - in production, use NTP for accurate time
  unsigned long ms = millis();
  char timestamp[30];
  sprintf(timestamp, "2026-04-13T%02lu:%02lu:%02lu.%03luZ", 
          (ms / 3600000) % 24, 
          (ms / 60000) % 60, 
          (ms / 1000) % 60, 
          ms % 1000);
  return String(timestamp);
}
