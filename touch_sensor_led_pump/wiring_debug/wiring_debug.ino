/*
 * ESP32 MOSFET Wiring Debug
 * 
 * This will help verify the wiring step-by-step
 */

#define PUMP_PIN 5
#define LED_PIN 19  // We know LED works, use it as reference

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n========================================");
  Serial.println("ESP32 MOSFET Wiring Debug");
  Serial.println("========================================\n");
  
  pinMode(PUMP_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  
  // Start with everything OFF
  digitalWrite(PUMP_PIN, LOW);
  digitalWrite(LED_PIN, LOW);
  
  Serial.println("Step 1: Verify LED works (we know this works)");
  Serial.println("----------------------------------------");
}

void loop() {
  // Test 1: LED only
  Serial.println("\n>>> TEST 1: LED ON, Pump OFF");
  Serial.println("    LED should light up");
  Serial.println("    Pump should be OFF");
  digitalWrite(LED_PIN, HIGH);
  digitalWrite(PUMP_PIN, LOW);
  delay(3000);
  
  digitalWrite(LED_PIN, LOW);
  Serial.println("    LED OFF");
  delay(2000);
  
  // Test 2: Pump only
  Serial.println("\n>>> TEST 2: LED OFF, Pump ON");
  Serial.println("    LED should be OFF");
  Serial.println("    Pump should turn ON");
  Serial.println("    ** LISTEN FOR PUMP MOTOR **");
  digitalWrite(LED_PIN, LOW);
  digitalWrite(PUMP_PIN, HIGH);
  delay(5000);  // 5 seconds to listen
  
  digitalWrite(PUMP_PIN, LOW);
  Serial.println("    Pump OFF");
  delay(2000);
  
  // Test 3: Both ON
  Serial.println("\n>>> TEST 3: LED ON, Pump ON");
  Serial.println("    Both LED and Pump should be ON");
  Serial.println("    ** LISTEN FOR PUMP MOTOR **");
  digitalWrite(LED_PIN, HIGH);
  digitalWrite(PUMP_PIN, HIGH);
  delay(5000);
  
  digitalWrite(LED_PIN, LOW);
  digitalWrite(PUMP_PIN, LOW);
  Serial.println("    Both OFF");
  delay(2000);
  
  // Test 4: Rapid toggle
  Serial.println("\n>>> TEST 4: Rapid Toggle (5 times)");
  Serial.println("    Quick ON/OFF cycles");
  for (int i = 0; i < 5; i++) {
    Serial.print("    Cycle ");
    Serial.print(i + 1);
    Serial.println(": ON");
    digitalWrite(PUMP_PIN, HIGH);
    digitalWrite(LED_PIN, HIGH);
    delay(500);
    
    Serial.print("    Cycle ");
    Serial.print(i + 1);
    Serial.println(": OFF");
    digitalWrite(PUMP_PIN, LOW);
    digitalWrite(LED_PIN, LOW);
    delay(500);
  }
  
  Serial.println("\n========================================");
  Serial.println("Test cycle complete. Repeating in 5 seconds...");
  Serial.println("========================================");
  delay(5000);
}
