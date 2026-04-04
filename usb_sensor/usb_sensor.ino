#include <Wire.h>
#include <Adafruit_HDC302x.h>
#include <Adafruit_Sensor.h>

Adafruit_HDC302x hdc = Adafruit_HDC302x();

const char* DEVICE_ID = "plant-esp32-01";

void setup() {
  Serial.begin(115200);
  delay(2000);

  Wire.begin(21, 22);

  if (!hdc.begin(0x44, &Wire)) {
    Serial.println("ERROR: HDC302x sensor not found!");
    while (true) {
      delay(1000);
    }
  }

  Serial.println("READY: Plant sensor initialized");
  hdc.setAutoMode(AUTO_MEASUREMENT_1MPS_LP0);
}

void loop() {
  double temp, hum;
  
  if (hdc.readAutoTempRH(temp, hum)) {
    // Output JSON format for easy parsing
    Serial.print("{\"device_id\":\"");
    Serial.print(DEVICE_ID);
    Serial.print("\",\"temperature_c\":");
    Serial.print(temp, 2);
    Serial.print(",\"humidity_pct\":");
    Serial.print(hum, 2);
    Serial.println("}");
  } else {
    Serial.println("ERROR: Failed to read sensor data");
  }

  delay(2000);  // Read every 2 seconds
}
