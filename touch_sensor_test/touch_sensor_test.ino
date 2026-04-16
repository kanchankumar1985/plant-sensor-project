#define TOUCH_PIN 4

int lastStableState = LOW;
int lastReadState = LOW;
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 50;

void setup() {
  Serial.begin(115200);
  pinMode(TOUCH_PIN, INPUT);
  Serial.println("Touch sensor test started");
}

void loop() {
  int reading = digitalRead(TOUCH_PIN);

  if (reading != lastReadState) {
    lastDebounceTime = millis();
    lastReadState = reading;
  }

  if ((millis() - lastDebounceTime) > debounceDelay) {
    if (reading != lastStableState) {
      lastStableState = reading;

      if (lastStableState == HIGH) {
        Serial.println("TOUCHED");
      } else {
        Serial.println("NOT_TOUCHED");
      }
    }
  }
}
