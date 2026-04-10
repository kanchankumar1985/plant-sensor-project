// Touch Sensor Integration for Plant Monitor
// Hardware: TTP223 / Keyes Touch Module
// Wiring: VCC->3.3V, GND->GND, S->GPIO4

#include <Wire.h>
#include <Adafruit_HDC302x.h>
#include <Adafruit_Sensor.h>

// Touch sensor configuration
const int TOUCH_PIN = 4;  // GPIO4 (D4)
const int DEBOUNCE_DELAY = 50;  // 50ms debounce

// Sensor configuration
Adafruit_HDC302x hdc = Adafruit_HDC302x();
const char* DEVICE_ID = "plant-esp32-01";
const int LED_PIN = 18;

// Temperature thresholds
const float TEMP_LOW = 24.0;
const float TEMP_HIGH = 25.0;

// Touch state tracking
bool lastTouchState = LOW;
bool currentTouchState = LOW;
unsigned long lastDebounceTime = 0;
bool touchStateChanged = false;

void setup() {
  Serial.begin(115200);
  delay(2000);
  
  // Initialize touch sensor pin with internal pull-down resistor
  pinMode(TOUCH_PIN, INPUT_PULLDOWN);
  
  // Initialize LED pin
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  
  // Initialize I2C for HDC302x
  Wire.begin(21, 22);
  
  if (!hdc.begin(0x44, &Wire)) {
    Serial.println("ERROR: HDC302x sensor not found!");
    Serial.println("READY: Touch sensor active (sensor-less mode)");
  } else {
    Serial.println("READY: Plant sensor with touch detection initialized");
    hdc.setAutoMode(AUTO_MEASUREMENT_1MPS_LP0);
  }
  
  Serial.println("INFO: Touch sensor on GPIO4");
}

void loop() {
  // Read touch sensor with debounce
  int reading = digitalRead(TOUCH_PIN);
  
  // Debug: Print raw reading every 5 seconds
  static unsigned long lastDebugPrint = 0;
  if (millis() - lastDebugPrint >= 5000) {
    lastDebugPrint = millis();
    Serial.print("DEBUG: GPIO4 raw reading = ");
    Serial.print(reading);
    Serial.print(", current state = ");
    Serial.println(currentTouchState == HIGH ? "TOUCHED" : "NOT_TOUCHED");
  }
  
  if (reading != lastTouchState) {
    lastDebounceTime = millis();
    Serial.print("DEBUG: Pin changed to ");
    Serial.println(reading);
  }
  
  if ((millis() - lastDebounceTime) > DEBOUNCE_DELAY) {
    if (reading != currentTouchState) {
      currentTouchState = reading;
      touchStateChanged = true;
      
      // Output touch event immediately (INVERTED: LOW = TOUCHED)
      if (currentTouchState == LOW) {
        Serial.println("TOUCH_EVENT:TOUCHED");
      } else {
        Serial.println("TOUCH_EVENT:NOT_TOUCHED");
      }
    }
  }
  
  lastTouchState = reading;
  
  // Read and send sensor data every 2 seconds
  static unsigned long lastSensorRead = 0;
  if (millis() - lastSensorRead >= 2000) {
    lastSensorRead = millis();
    
    double temp, hum;
    bool sensorRead = hdc.readAutoTempRH(temp, hum);
    
    if (sensorRead) {
      // LED Control Logic
      if (temp < TEMP_LOW) {
        digitalWrite(LED_PIN, LOW);
      } else if (temp > TEMP_HIGH) {
        digitalWrite(LED_PIN, HIGH);
      }
      
      // Output sensor data JSON
      Serial.print("{\"device_id\":\"");
      Serial.print(DEVICE_ID);
      Serial.print("\",\"temperature_c\":");
      Serial.print(temp, 2);
      Serial.print(",\"humidity_pct\":");
      Serial.print(hum, 2);
      Serial.print(",\"led_state\":");
      Serial.print(digitalRead(LED_PIN));
      Serial.print(",\"touch_state\":\"");
      Serial.print(currentTouchState == LOW ? "TOUCHED" : "NOT_TOUCHED");
      Serial.println("\"}");
    } else {
      // Sensor not available - send touch state only
      Serial.print("{\"device_id\":\"");
      Serial.print(DEVICE_ID);
      Serial.print("\",\"touch_state\":\"");
      Serial.print(currentTouchState == LOW ? "TOUCHED" : "NOT_TOUCHED");
      Serial.println("\"}");
    }
  }
  
  delay(10);  // Small delay for stability
}
