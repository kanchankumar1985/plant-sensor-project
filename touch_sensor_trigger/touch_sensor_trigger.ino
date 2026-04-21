/*
 * Touch Sensor Trigger for Plant Monitor
 * Sends "TOUCHED" event when sensor is activated
 * 
 * Hardware:
 * - Touch Sensor S → GPIO4
 * - Touch Sensor VCC → 3.3V
 * - Touch Sensor GND → GND
 */

const int TOUCH_PIN = 4;
const int DEBOUNCE_DELAY = 50;  // 50ms debounce

int lastTouchState = LOW;
int currentTouchState = LOW;
unsigned long lastDebounceTime = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  pinMode(TOUCH_PIN, INPUT_PULLDOWN);
  
  Serial.println("READY");
  Serial.println("Touch sensor initialized on GPIO4");
}

void loop() {
  int reading = digitalRead(TOUCH_PIN);
  
  // Debounce logic
  if (reading != lastTouchState) {
    lastDebounceTime = millis();
  }
  
  if ((millis() - lastDebounceTime) > DEBOUNCE_DELAY) {
    // State has been stable
    if (reading != currentTouchState) {
      currentTouchState = reading;
      
      // Only send event on RISING edge (touch detected)
      if (currentTouchState == HIGH) {
        Serial.println("TOUCHED");
      }
    }
  }
  
  lastTouchState = reading;
  delay(10);
}
