/*
 * ESP32 Pump Test - Direct Control
 * 
 * This sketch tests the pump directly without the touch sensor
 * to verify the MOSFET and pump hardware are working correctly.
 * 
 * The pump will turn ON for 3 seconds, then OFF for 3 seconds, repeatedly.
 */

#define PUMP_PIN 5  // MOSFET pump control pin

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n========================================");
  Serial.println("ESP32 Pump Hardware Test");
  Serial.println("========================================");
  Serial.println("Testing pump on GPIO 5");
  Serial.println("Pump will cycle: 3s ON, 3s OFF");
  Serial.println("========================================\n");
  
  pinMode(PUMP_PIN, OUTPUT);
  digitalWrite(PUMP_PIN, LOW);  // Start with pump OFF
  
  Serial.println("✓ Pin configured");
  Serial.println("✓ Starting test cycle...\n");
}

void loop() {
  // Turn pump ON
  Serial.println(">>> PUMP ON (GPIO 5 = HIGH)");
  Serial.println("    Check if pump motor is running!");
  Serial.println("    You should hear motor sound or see water moving");
  digitalWrite(PUMP_PIN, HIGH);
  
  // Wait 3 seconds
  for (int i = 3; i > 0; i--) {
    Serial.print("    ");
    Serial.print(i);
    Serial.println(" seconds remaining...");
    delay(1000);
  }
  
  // Turn pump OFF
  Serial.println("\n<<< PUMP OFF (GPIO 5 = LOW)");
  Serial.println("    Pump should stop now");
  digitalWrite(PUMP_PIN, LOW);
  
  // Wait 3 seconds
  for (int i = 3; i > 0; i--) {
    Serial.print("    ");
    Serial.print(i);
    Serial.println(" seconds until next cycle...");
    delay(1000);
  }
  
  Serial.println("\n----------------------------------------\n");
}
