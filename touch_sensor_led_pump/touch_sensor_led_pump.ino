/*
 * ESP32 Touch Sensor + LED + Pump Controller
 * 
 * Hardware connections:
 * - Touch Sensor: VCC→3.3V, GND→GND, S→GPIO4
 * - LED Module:   VCC→3.3V, GND→GND, S→GPIO19
 * - MOSFET Pump:  GND→GND, TRIG→GPIO5, VIN±→Pump Power
 * 
 * Behavior:
 * - Touch detected → LED ON + Pump ON
 * - Touch released → LED OFF + Pump OFF
 * 
 * Troubleshooting:
 * - If LED/Pump behavior is inverted, change ACTIVE_HIGH flags below
 * - Some modules are active-LOW (turn on with LOW signal)
 * - Check Serial Monitor at 115200 baud for detailed logs
 */

// ============================================================================
// PIN DEFINITIONS
// ============================================================================
#define TOUCH_PIN 4   // Touch sensor signal pin
#define LED_PIN   19  // LED module signal pin (changed from GPIO18)
#define PUMP_PIN  5   // MOSFET pump control pin

// ============================================================================
// LOGIC CONFIGURATION (CHANGE THESE IF BEHAVIOR IS INVERTED)
// ============================================================================
// Set to true if module turns ON with HIGH signal
// Set to false if module turns ON with LOW signal (active-LOW)
const bool LED_ACTIVE_HIGH = true;   // Change to false if LED is inverted
const bool PUMP_ACTIVE_HIGH = true;  // Change to false if pump is inverted

// ============================================================================
// DEBOUNCE & TIMING
// ============================================================================
const unsigned long DEBOUNCE_DELAY = 50;  // milliseconds to wait for stable reading
unsigned long lastDebounceTime = 0;
int lastTouchState = LOW;
int touchState = LOW;
bool currentOutputState = false;  // false = OFF, true = ON

// ============================================================================
// SETUP
// ============================================================================
void setup() {
  // Initialize Serial for debugging
  Serial.begin(115200);
  delay(1000);  // Give Serial time to initialize
  
  Serial.println("\n\n========================================");
  Serial.println("ESP32 Touch + LED + Pump Controller");
  Serial.println("========================================");
  Serial.println("Hardware:");
  Serial.println("  Touch Sensor → GPIO 4");
  Serial.println("  LED Module   → GPIO 19");
  Serial.println("  Pump MOSFET  → GPIO 5");
  Serial.println();
  Serial.println("Logic Configuration:");
  Serial.print("  LED is active-");
  Serial.println(LED_ACTIVE_HIGH ? "HIGH" : "LOW");
  Serial.print("  Pump is active-");
  Serial.println(PUMP_ACTIVE_HIGH ? "HIGH" : "LOW");
  Serial.println("========================================\n");
  
  // Configure pins
  pinMode(TOUCH_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  pinMode(PUMP_PIN, OUTPUT);
  
  // Initialize outputs to OFF state
  setOutputs(false);
  
  Serial.println("✓ Pins configured");
  Serial.println("✓ Outputs initialized to OFF");
  Serial.println("✓ Ready! Touch the sensor to test.\n");
}

// ============================================================================
// MAIN LOOP
// ============================================================================
void loop() {
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
      
      // Determine if we should turn outputs ON or OFF
      bool shouldBeOn = (touchState == HIGH);
      
      // Only change outputs if state actually changed
      if (shouldBeOn != currentOutputState) {
        currentOutputState = shouldBeOn;
        setOutputs(currentOutputState);
        
        // Print detailed status
        printStatus(currentOutputState);
      }
    }
  }
  
  // Save the reading for next iteration
  lastTouchState = reading;
  
  // Small delay to prevent excessive CPU usage
  delay(10);
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Set LED and Pump outputs to ON or OFF
 * Handles active-HIGH and active-LOW logic automatically
 */
void setOutputs(bool turnOn) {
  // LED control
  if (LED_ACTIVE_HIGH) {
    digitalWrite(LED_PIN, turnOn ? HIGH : LOW);
  } else {
    digitalWrite(LED_PIN, turnOn ? LOW : HIGH);  // Inverted for active-LOW
  }
  
  // Pump control
  if (PUMP_ACTIVE_HIGH) {
    digitalWrite(PUMP_PIN, turnOn ? HIGH : LOW);
  } else {
    digitalWrite(PUMP_PIN, turnOn ? LOW : HIGH);  // Inverted for active-LOW
  }
}

/**
 * Print detailed status to Serial Monitor
 */
void printStatus(bool isOn) {
  Serial.println("----------------------------------------");
  Serial.print("Touch State: ");
  Serial.println(isOn ? "TOUCHED" : "NOT TOUCHED");
  Serial.println();
  
  if (isOn) {
    Serial.println("✓ LED:  ON");
    Serial.println("✓ PUMP: ON");
    Serial.print("  (LED pin ");
    Serial.print(LED_PIN);
    Serial.print(" = ");
    Serial.print(LED_ACTIVE_HIGH ? "HIGH" : "LOW");
    Serial.println(")");
    Serial.print("  (Pump pin ");
    Serial.print(PUMP_PIN);
    Serial.print(" = ");
    Serial.print(PUMP_ACTIVE_HIGH ? "HIGH" : "LOW");
    Serial.println(")");
  } else {
    Serial.println("✗ LED:  OFF");
    Serial.println("✗ PUMP: OFF");
    Serial.print("  (LED pin ");
    Serial.print(LED_PIN);
    Serial.print(" = ");
    Serial.print(LED_ACTIVE_HIGH ? "LOW" : "HIGH");
    Serial.println(")");
    Serial.print("  (Pump pin ");
    Serial.print(PUMP_PIN);
    Serial.print(" = ");
    Serial.print(PUMP_ACTIVE_HIGH ? "LOW" : "HIGH");
    Serial.println(")");
  }
  
  Serial.println("----------------------------------------\n");
}

/*
 * ============================================================================
 * TROUBLESHOOTING GUIDE
 * ============================================================================
 * 
 * PROBLEM: LED doesn't turn on when touched
 * SOLUTION: Change LED_ACTIVE_HIGH to false (line 26)
 * 
 * PROBLEM: LED is always on, turns off when touched
 * SOLUTION: Change LED_ACTIVE_HIGH to false (line 26)
 * 
 * PROBLEM: Pump doesn't turn on when touched
 * SOLUTION: Change PUMP_ACTIVE_HIGH to false (line 27)
 * 
 * PROBLEM: Pump is always on, turns off when touched
 * SOLUTION: Change PUMP_ACTIVE_HIGH to false (line 27)
 * 
 * PROBLEM: Touch sensor is too sensitive or not sensitive enough
 * SOLUTION: Adjust DEBOUNCE_DELAY (line 31) - increase for less sensitivity
 * 
 * PROBLEM: No Serial output
 * SOLUTION: 
 *   1. Check Serial Monitor is set to 115200 baud
 *   2. Make sure USB cable is connected
 *   3. Select correct COM port in Arduino IDE
 * 
 * PROBLEM: LED/Pump flickers
 * SOLUTION: Increase DEBOUNCE_DELAY to 100 or 200 milliseconds
 * 
 * TESTING STEPS:
 * 1. Upload code to ESP32
 * 2. Open Serial Monitor (Tools → Serial Monitor, set to 115200 baud)
 * 3. Touch the sensor - you should see "TOUCHED" message
 * 4. Release - you should see "NOT TOUCHED" message
 * 5. Check LED and pump behavior
 * 6. If inverted, change ACTIVE_HIGH flags and re-upload
 * 
 * ============================================================================
 */
