#include <Wire.h>
#include <Adafruit_HDC302x.h>
#include <Adafruit_Sensor.h>

Adafruit_HDC302x hdc = Adafruit_HDC302x();

const char* DEVICE_ID = "plant-esp32-01";
const int LED_PIN = 18;  // GPIO18 for LED control

// Temperature thresholds
const float TEMP_LOW = 24.0;   // LED OFF when temp < 23°C
const float TEMP_HIGH = 25.0;  // LED ON when temp > 25°C

void setup() {
  Serial.begin(115200);
  delay(2000);

  // Initialize LED pin
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);  // Start with LED OFF

  Wire.begin(21, 22);

  if (!hdc.begin(0x44, &Wire)) {
    Serial.println("ERROR: HDC302x sensor not found!");
    while (true) {
      delay(1000);
    }
  }

  Serial.println("READY: Plant sensor initialized with LED control");
  hdc.setAutoMode(AUTO_MEASUREMENT_1MPS_LP0);
}

void loop() {
  double temp, hum;
  
  if (hdc.readAutoTempRH(temp, hum)) {
    // LED Control Logic
    if (temp < TEMP_LOW) {
      digitalWrite(LED_PIN, LOW);   // LED OFF when cold
    } else if (temp > TEMP_HIGH) {
      digitalWrite(LED_PIN, HIGH);  // LED ON when warm
    }
    // Between 23-25°C: LED stays in current state (hysteresis)
    
    // Output JSON format for easy parsing
    Serial.print("{\"device_id\":\"");
    Serial.print(DEVICE_ID);
    Serial.print("\",\"temperature_c\":");
    Serial.print(temp, 2);
    Serial.print(",\"humidity_pct\":");
    Serial.print(hum, 2);
    Serial.print(",\"led_state\":");
    Serial.print(digitalRead(LED_PIN));
    Serial.println("}");
  } else {
    Serial.println("ERROR: Failed to read sensor data");
  }

  delay(2000);  // Read every 2 seconds
}
