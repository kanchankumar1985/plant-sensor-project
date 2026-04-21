/*
 * ESP32 GPIO Pin Voltage Test
 * 
 * This will help verify if GPIO 5 is actually outputting voltage
 * Measure with a multimeter between GPIO 5 and GND
 */

#define PUMP_PIN 5

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n========================================");
  Serial.println("ESP32 GPIO 5 Voltage Test");
  Serial.println("========================================");
  Serial.println("Use a multimeter to measure:");
  Serial.println("  RED probe  → GPIO 5 pin");
  Serial.println("  BLACK probe → GND pin");
  Serial.println("========================================\n");
  
  pinMode(PUMP_PIN, OUTPUT);
}

void loop() {
  Serial.println("\n>>> Setting GPIO 5 = HIGH");
  Serial.println("    Multimeter should read ~3.3V");
  Serial.println("    Waiting 10 seconds...");
  digitalWrite(PUMP_PIN, HIGH);
  delay(10000);
  
  Serial.println("\n<<< Setting GPIO 5 = LOW");
  Serial.println("    Multimeter should read ~0V");
  Serial.println("    Waiting 10 seconds...");
  digitalWrite(PUMP_PIN, LOW);
  delay(10000);
}
