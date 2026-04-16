// Touch Sensor → LED Control for ESP32
// Hardware: Touch sensor module + LED module
// Touch sensor: VCC->3.3V, GND->GND, S->GPIO4
// LED module: VCC->3.3V, GND->GND, S->GPIO23

// Pin definitions
const int TOUCH_PIN = 4;   // GPIO4 for touch sensor signal
const int LED_PIN = 23;    // GPIO23 for LED control

// Debounce variables
int lastTouchState = LOW;
int currentTouchState = LOW;
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 50;  // 50ms debounce

void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  delay(1000);
  
  // Configure pins
  pinMode(TOUCH_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  
  // Start with LED off
  digitalWrite(LED_PIN, LOW);
  
  Serial.println("=================================");
  Serial.println("Touch Sensor → LED Control");
  Serial.println("=================================");
  Serial.println("Touch sensor: GPIO4");
  Serial.println("LED control: GPIO23");
  Serial.println("Ready!");
  Serial.println("=================================\n");
}

void loop() {
  // Read touch sensor
  int reading = digitalRead(TOUCH_PIN);
  
  // Check if state changed (for debouncing)
  if (reading != lastTouchState) {
    lastDebounceTime = millis();
  }
  
  // If reading has been stable for debounce delay
  if ((millis() - lastDebounceTime) > debounceDelay) {
    // If the state has actually changed
    if (reading != currentTouchState) {
      currentTouchState = reading;
      
      // Control LED based on touch state
      if (currentTouchState == HIGH) {
        // Touched - turn LED ON
        digitalWrite(LED_PIN, HIGH);
        Serial.println("✓ Touched → LED ON");
      } else {
        // Not touched - turn LED OFF
        digitalWrite(LED_PIN, LOW);
        Serial.println("○ Not touched → LED OFF");
      }
    }
  }
  
  // Update last state
  lastTouchState = reading;
  
  // Small delay for stability
  delay(10);
}
