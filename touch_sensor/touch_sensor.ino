// Touch Sensor Integration for Plant Monitor
// Hardware: TTP223 / Keyes Touch Module + LED Module
// Wiring: 
//   Touch Sensor: VCC->3.3V, GND->GND, S->GPIO4
//   LED Module: VCC->3.3V, GND->GND, S->GPIO23

#include <Wire.h>
#include <Adafruit_HDC302x.h>
#include <Adafruit_Sensor.h>

bool hdcReady = false;
uint8_t hdc_addr_current = 0x44;
unsigned long lastReinitAttempt = 0;

bool initHDC302x();
void i2cScan();

// Touch sensor configuration
const int TOUCH_PIN = 4;  // GPIO4 (D4)
const int DEBOUNCE_DELAY = 50;  // 50ms debounce

// LED configuration
const int TOUCH_LED_PIN = 23;  // GPIO23 - LED controlled by touch sensor
const int TEMP_LED_PIN = 18;   // GPIO18 - LED controlled by temperature

// Sensor configuration
Adafruit_HDC302x hdc = Adafruit_HDC302x();
const char* DEVICE_ID = "plant-esp32-01";

// Temperature thresholds
const float TEMP_LOW = 24.0;
const float TEMP_HIGH = 25.0;

// Touch state tracking
bool lastTouchState = LOW;
bool currentTouchState = LOW;
unsigned long lastDebounceTime = 0;
bool touchStateChanged = false;

void i2cScan() {
  byte count = 0;
  for (byte addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      Serial.print("I2C device found at 0x");
      Serial.println(addr, HEX);
      count++;
    }
    delay(2);
  }
  if (count == 0) {
    Serial.println("I2C scan: no devices found");
  }
}

bool initHDC302x() {
  uint8_t candidates[2] = {0x44, 0x45};
  for (uint8_t i = 0; i < 2; i++) {
    uint8_t addr = candidates[i];
    for (uint8_t attempt = 0; attempt < 5; attempt++) {
      if (hdc.begin(addr, &Wire)) {
        hdc_addr_current = addr;
        hdc.setAutoMode(AUTO_MEASUREMENT_1MPS_LP0);
        Serial.print("HDC302x detected at 0x");
        Serial.println(addr, HEX);
        hdcReady = true;
        return true;
      }
      delay(50);
    }
  }
  Serial.println("ERROR: HDC302x sensor not found!");
  i2cScan();
  hdcReady = false;
  return false;
}

void setup() {
  Serial.begin(115200);
  delay(2000);
  
  // Initialize touch sensor pin with internal pull-down resistor
  pinMode(TOUCH_PIN, INPUT_PULLDOWN);
  
  // Initialize LED pins
  pinMode(TOUCH_LED_PIN, OUTPUT);
  pinMode(TEMP_LED_PIN, OUTPUT);
  digitalWrite(TOUCH_LED_PIN, LOW);
  digitalWrite(TEMP_LED_PIN, LOW);
  
  // Initialize I2C for HDC302x
  Wire.begin(21, 22);
  Wire.setClock(100000);
  
  hdcReady = initHDC302x();
  if (!hdcReady) {
    Serial.println("READY: Touch sensor active (sensor-less mode)");
  } else {
    Serial.println("READY: Plant sensor with touch detection initialized");
  }
  
  Serial.println("INFO: Touch sensor on GPIO4");
  Serial.println("INFO: Touch LED on GPIO23");
  Serial.println("INFO: Temperature LED on GPIO18");
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
      
      // Control touch LED based on touch state
      if (currentTouchState == HIGH) {
        digitalWrite(TOUCH_LED_PIN, HIGH);  // Turn LED ON when touched
        Serial.println("TOUCHED");  // For serial_touch_listener.py
        Serial.println("TOUCH_EVENT:TOUCHED");
        Serial.println("✓ Touched → LED ON");
      } else {
        digitalWrite(TOUCH_LED_PIN, LOW);   // Turn LED OFF when not touched
        Serial.println("TOUCH_EVENT:NOT_TOUCHED");
        Serial.println("○ Not touched → LED OFF");
      }
    }
  }
  
  lastTouchState = reading;
  
  // Read and send sensor data every 2 seconds
  static unsigned long lastSensorRead = 0;
  static uint8_t sensorFailCount = 0;
  if (millis() - lastSensorRead >= 2000) {
    lastSensorRead = millis();
    
    double temp, hum;
    bool sensorRead = false;
    if (hdcReady) {
      sensorRead = hdc.readAutoTempRH(temp, hum);
    }
    
    if (sensorRead) {
      sensorFailCount = 0;
      // Temperature LED Control Logic
      if (temp < TEMP_LOW) {
        digitalWrite(TEMP_LED_PIN, LOW);
      } else if (temp > TEMP_HIGH) {
        digitalWrite(TEMP_LED_PIN, HIGH);
      }
      
      // Output sensor data JSON
      Serial.print("{\"device_id\":\"");
      Serial.print(DEVICE_ID);
      Serial.print("\",\"temperature_c\":");
      Serial.print(temp, 2);
      Serial.print(",\"humidity_pct\":");
      Serial.print(hum, 2);
      Serial.print(",\"led_state\":");
      Serial.print(digitalRead(TEMP_LED_PIN));
      Serial.print(",\"touch_state\":\"");
      Serial.print(currentTouchState == HIGH ? "TOUCHED" : "NOT_TOUCHED");
      Serial.print("\",\"touch_led_state\":");
      Serial.print(digitalRead(TOUCH_LED_PIN));
      Serial.println("}");
    } else {
      sensorFailCount++;
      if (!hdcReady || sensorFailCount >= 5) {
        hdcReady = false;
        if (millis() - lastReinitAttempt >= 5000) {
          lastReinitAttempt = millis();
          initHDC302x();
        }
      }
      // Sensor not available - send touch state only
      Serial.print("{\"device_id\":\"");
      Serial.print(DEVICE_ID);
      Serial.print("\",\"touch_state\":\"");
      Serial.print(currentTouchState == HIGH ? "TOUCHED" : "NOT_TOUCHED");
      Serial.print("\",\"touch_led_state\":");
      Serial.print(digitalRead(TOUCH_LED_PIN));
      Serial.println("}");
    }
  }
  
  delay(10);  // Small delay for stability
}
