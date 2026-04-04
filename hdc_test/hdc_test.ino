#include <Wire.h>
#include <Adafruit_HDC302x.h>
#include <Adafruit_Sensor.h>

Adafruit_HDC302x hdc = Adafruit_HDC302x();

void setup() {
  Serial.begin(115200);
  delay(1000);

  Wire.begin(21, 22);  // SDA, SCL on ESP32

  Serial.println("Starting HDC302x test...");

  if (!hdc.begin(0x44, &Wire)) {
    Serial.println("HDC302x not found! Check wiring.");
    while (1) {
      delay(10);
    }
  }

  Serial.println("HDC302x connected.");
  
  // Set auto measurement mode
  hdc.setAutoMode(AUTO_MEASUREMENT_1MPS_LP0);
}

void loop() {
  double temp, hum;
  
  if (hdc.readAutoTempRH(temp, hum)) {
    Serial.println("------");
    Serial.print("Temperature (C): ");
    Serial.println(temp);

    Serial.print("Humidity (%): ");
    Serial.println(hum);
    
    // Check if temperature is above 25°C
    if (temp > 25.0) {
      Serial.println("*** ALERT: Temperature is above 25°C! ***");
    }
  } else {
    Serial.println("Failed to read sensor data");
  }

  delay(2000);
}
