void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("ESP32 Basic Test - Starting...");
  Serial.println("If you see this, ESP32 serial communication is working!");
}

void loop() {
  Serial.println("ESP32 is alive! Uptime: " + String(millis()/1000) + " seconds");
  delay(2000);
}
