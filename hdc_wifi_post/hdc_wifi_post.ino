#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <Adafruit_HDC302x.h>
#include <Adafruit_Sensor.h>

const char* WIFI_SSID = "ATTqCZIe2s_2G";
const char* WIFI_PASSWORD = "xf8psnrn3wb4";

// Your Mac's IP address
const char* API_URL = "http://192.168.1.71:8000/api/readings";

Adafruit_HDC302x hdc = Adafruit_HDC302x();

const char* DEVICE_ID = "plant-esp32-01";

void connectWiFi() {
  Serial.println("Starting WiFi connection...");
  Serial.print("SSID: ");
  Serial.println(WIFI_SSID);
  
  WiFi.mode(WIFI_STA);
  WiFi.disconnect(true, true);
  delay(2000);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(1000);
    Serial.print(".");
    attempts++;
    
    if (attempts % 10 == 0) {
      Serial.println();
      Serial.print("WiFi Status: ");
      Serial.println(WiFi.status());
    }
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.println("WiFi connected successfully!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    Serial.print("Signal strength (RSSI): ");
    Serial.println(WiFi.RSSI());
  } else {
    Serial.println();
    Serial.println("WiFi connection failed!");
    Serial.print("Final status: ");
    Serial.println(WiFi.status());
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  Wire.begin(21, 22);

  if (!hdc.begin(0x44, &Wire)) {
    Serial.println("HDC302x not found!");
    while (true) {
      delay(1000);
    }
  }

  Serial.println("HDC302x connected.");
  hdc.setAutoMode(AUTO_MEASUREMENT_1MPS_LP0);

  connectWiFi();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  double temp, hum;
  
  if (hdc.readAutoTempRH(temp, hum)) {
    Serial.println("------");
    Serial.print("Temperature (C): ");
    Serial.println(temp);
    Serial.print("Humidity (%): ");
    Serial.println(hum);

    HTTPClient http;
    http.begin(API_URL);
    http.addHeader("Content-Type", "application/json");

    String payload = "{";
    payload += "\"device_id\":\"" + String(DEVICE_ID) + "\",";
    payload += "\"temperature_c\":" + String(temp, 2) + ",";
    payload += "\"humidity_pct\":" + String(hum, 2);
    payload += "}";

    int httpCode = http.POST(payload);
    String response = http.getString();

    Serial.print("HTTP code: ");
    Serial.println(httpCode);
    Serial.print("Response: ");
    Serial.println(response);

    http.end();
  } else {
    Serial.println("Failed to read sensor data");
  }

  delay(2000);  // Send data every 2 seconds
}
