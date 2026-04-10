// Simple USB serial test - sends fake sensor data without requiring HDC302x
// This is for testing the serial_reader.py and database connection

const char* DEVICE_ID = "plant-esp32-01";

void setup() {
  Serial.begin(115200);
  delay(2000);
  Serial.println("READY: USB test mode - sending fake sensor data");
}

void loop() {
  // Generate fake temperature and humidity data
  float temp = 24.0 + (random(0, 40) / 10.0);  // 24.0 to 28.0°C
  float hum = 50.0 + (random(0, 200) / 10.0);  // 50.0 to 70.0%
  
  // Output JSON format (same as usb_sensor.ino)
  Serial.print("{\"device_id\":\"");
  Serial.print(DEVICE_ID);
  Serial.print("\",\"temperature_c\":");
  Serial.print(temp, 2);
  Serial.print(",\"humidity_pct\":");
  Serial.print(hum, 2);
  Serial.println("}");
  
  delay(2000);  // Send every 2 seconds
}
