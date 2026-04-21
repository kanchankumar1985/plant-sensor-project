/*
 * ESP32 Unified Plant Monitor
 * 
 * Features:
 * - Touch Sensor control for LED and Pump
 * - HDC302X Temperature/Humidity monitoring
 * - JSON output for Python listener
 * - Touch event detection
 * - Pump state logging
 * 
 * Hardware connections:
 * - Touch Sensor: VCC→3.3V, GND→GND, S→GPIO4
 * - LED Module:   VCC→3.3V, GND→GND, S→GPIO19
 * - MOSFET Pump:  GND→GND, TRIG→GPIO5, VIN±→External 5V USB
 * - HDC302X:      VCC→3.3V, GND→GND, SDA→GPIO21, SCL→GPIO22
 */

#include <Wire.h>
#include <Adafruit_HDC302x.h>
#include <Adafruit_Sensor.h>
#include <ArduinoJson.h>

// ============================================================================
// PIN DEFINITIONS
// ============================================================================
#define TOUCH_PIN 4   // Touch sensor signal pin
#define LED_PIN   19  // LED module signal pin
#define PUMP_PIN  5   // MOSFET pump control pin
#define SDA_PIN   21  // I2C SDA for HDC302X
#define SCL_PIN   22  // I2C SCL for HDC302X

// ============================================================================
// LOGIC CONFIGURATION
// ============================================================================
const bool LED_ACTIVE_HIGH = true;   // LED turns ON with HIGH signal
const bool PUMP_ACTIVE_HIGH = true;  // Pump turns ON with HIGH signal

// ============================================================================
// TIMING CONFIGURATION
// ============================================================================
const unsigned long DEBOUNCE_DELAY = 50;        // Touch debounce (ms)
const unsigned long SENSOR_READ_INTERVAL = 2000; // Read temp/humidity every 2 seconds
const unsigned long PUMP_DURATION = 2000;        // Pump runs for 2 seconds
const unsigned long PUMP_COOLDOWN = 60000;       // 60 second (1 minute) cooldown between pump runs
const char* DEVICE_ID = "ESP32_PLANT_01";       // Device identifier

// ============================================================================
// GLOBAL VARIABLES
// ============================================================================
Adafruit_HDC302x hdc = Adafruit_HDC302x();

// Touch sensor state
unsigned long lastDebounceTime = 0;
int lastTouchState = LOW;
int touchState = LOW;

// Sensor reading timing
unsigned long lastSensorRead = 0;

// Temperature/Humidity values
double temperature = 0.0;
double humidity = 0.0;
bool sensorAvailable = false;

// Pump control state
bool pumpRunning = false;
unsigned long pumpStartTime = 0;
unsigned long lastPumpRunTime = 0;
bool temperatureTriggered = false;

// ============================================================================
// SETUP
// ============================================================================
void setup() {
  // Initialize Serial
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n\n========================================");
  Serial.println("ESP32 Unified Plant Monitor");
  Serial.println("========================================");
  Serial.println("Hardware:");
  Serial.println("  Touch Sensor → GPIO 4");
  Serial.println("  LED Module   → GPIO 19");
  Serial.println("  Pump MOSFET  → GPIO 5");
  Serial.println("  HDC302X      → I2C (SDA:21, SCL:22)");
  Serial.println();
  
  // Configure GPIO pins
  pinMode(TOUCH_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  pinMode(PUMP_PIN, OUTPUT);
  
  // Initialize outputs to OFF
  if (PUMP_ACTIVE_HIGH) {
    digitalWrite(PUMP_PIN, LOW);
  } else {
    digitalWrite(PUMP_PIN, HIGH);
  }
  
  if (LED_ACTIVE_HIGH) {
    digitalWrite(LED_PIN, LOW);
  } else {
    digitalWrite(LED_PIN, HIGH);
  }
  
  Serial.println("✓ GPIO pins configured");
  
  // Initialize I2C for HDC302X
  Wire.begin(SDA_PIN, SCL_PIN);
  
  // Initialize HDC302X sensor
  if (hdc.begin(0x44, &Wire)) {
    Serial.println("✓ HDC302X sensor connected");
    hdc.setAutoMode(AUTO_MEASUREMENT_1MPS_LP0);
    sensorAvailable = true;
  } else {
    Serial.println("⚠️  HDC302X sensor not found - continuing without temp/humidity");
    sensorAvailable = false;
  }
  
  Serial.println("✓ System ready!");
  Serial.println("========================================\n");
  
  // Send initial sensor reading
  readAndSendSensorData();
}

// ============================================================================
// MAIN LOOP
// ============================================================================
void loop() {
  unsigned long currentMillis = millis();
  
  // Handle touch sensor input
  handleTouchSensor();
  
  // Check for commands from Python
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command == "PUMP_ON_YELLOW_LEAVES") {
      if (!pumpRunning && (currentMillis - lastPumpRunTime >= PUMP_COOLDOWN)) {
        runPump("YELLOW LEAVES DETECTED");
      } else if (pumpRunning) {
        Serial.println("Pump already running");
      } else {
        unsigned long remainingCooldown = PUMP_COOLDOWN - (currentMillis - lastPumpRunTime);
        Serial.print("Cooldown active (");
        Serial.print(remainingCooldown / 1000);
        Serial.println(" seconds remaining)");
      }
    }
  }
  
  // Check if pump should auto-stop
  if (pumpRunning && (currentMillis - pumpStartTime >= PUMP_DURATION)) {
    stopPump();
  }
  
  // Read and send sensor data periodically
  if (currentMillis - lastSensorRead >= SENSOR_READ_INTERVAL) {
    readAndSendSensorData();
    lastSensorRead = currentMillis;
  }
  
  delay(10);
}

// ============================================================================
// TOUCH SENSOR HANDLING
// ============================================================================
void handleTouchSensor() {
  // Read current touch sensor state
  int reading = digitalRead(TOUCH_PIN);
  
  // Check if touch state changed (for debouncing)
  if (reading != lastTouchState) {
    lastDebounceTime = millis();
  }
  
  // Only update if reading has been stable for DEBOUNCE_DELAY
  if ((millis() - lastDebounceTime) > DEBOUNCE_DELAY) {
    // If touch state actually changed
    if (reading != touchState) {
      touchState = reading;
      
      // Send touch event to Python for VLM analysis
      if (touchState == HIGH) {
        Serial.println("TOUCHED");
        Serial.println("VLM_ANALYSIS_REQUESTED");
      }
    }
  }
  
  // Save the reading for next iteration
  lastTouchState = reading;
}

// ============================================================================
// SENSOR DATA READING AND JSON OUTPUT
// ============================================================================
void readAndSendSensorData() {
  // Read temperature and humidity if sensor is available
  if (sensorAvailable) {
    if (!hdc.readAutoTempRH(temperature, humidity)) {
      Serial.println("⚠️  Failed to read HDC302X sensor");
      temperature = 0.0;
      humidity = 0.0;
    } else {
      // Print temperature reading
      Serial.print("Temperature: ");
      Serial.print(temperature, 1);
      Serial.println(" °C");
    }
  }
  
  // Create JSON document
  StaticJsonDocument<256> doc;
  
  doc["device_id"] = DEVICE_ID;
  doc["temperature_c"] = temperature;
  doc["humidity_pct"] = humidity;
  doc["led_state"] = pumpRunning ? 1 : 0;
  doc["pump_state"] = pumpRunning ? 1 : 0;
  doc["timestamp"] = millis();
  
  // Serialize and send JSON
  serializeJson(doc, Serial);
  Serial.println();
}

// ============================================================================
// PUMP CONTROL FUNCTIONS
// ============================================================================
void runPump(const char* reason) {
  Serial.println("========================================");
  Serial.print("🚰 Pump ON due to: ");
  Serial.println(reason);
  Serial.println("========================================");
  
  // Turn on pump
  if (PUMP_ACTIVE_HIGH) {
    digitalWrite(PUMP_PIN, HIGH);
  } else {
    digitalWrite(PUMP_PIN, LOW);
  }
  
  // Turn on LED
  if (LED_ACTIVE_HIGH) {
    digitalWrite(LED_PIN, HIGH);
  } else {
    digitalWrite(LED_PIN, LOW);
  }
  
  pumpRunning = true;
  pumpStartTime = millis();
  
  Serial.print("✓ Pump will run for ");
  Serial.print(PUMP_DURATION / 1000);
  Serial.println(" seconds");
  Serial.println();
}

void stopPump() {
  Serial.println("========================================");
  Serial.println("🛑 Pump OFF");
  Serial.println("========================================\n");
  
  // Turn off pump
  if (PUMP_ACTIVE_HIGH) {
    digitalWrite(PUMP_PIN, LOW);
  } else {
    digitalWrite(PUMP_PIN, HIGH);
  }
  
  // Turn off LED
  if (LED_ACTIVE_HIGH) {
    digitalWrite(LED_PIN, LOW);
  } else {
    digitalWrite(LED_PIN, HIGH);
  }
  
  pumpRunning = false;
  lastPumpRunTime = millis();
}
