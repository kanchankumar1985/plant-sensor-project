#include <Wire.h>
#include <U8g2lib.h>

// OLED display configuration for 1.3" SH1106 (128x64)
// Hardware I2C: SDA=21, SCL=22 (ESP32 default)
U8G2_SH1106_128X64_NONAME_F_HW_I2C display(U8G2_R0, /* reset=*/ U8X8_PIN_NONE);

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n========== 1.3\" OLED Display Test ==========");
  
  // Initialize I2C
  Wire.begin(21, 22);  // SDA=21, SCL=22 (ESP32 default)
  
  // Initialize display
  display.begin();
  Serial.println("✓ OLED initialized successfully!");
  
  // Clear display
  display.clearBuffer();
  display.sendBuffer();
  delay(500);
  
  // Run tests
  testText();
  delay(2000);
  
  testShapes();
  delay(2000);
  
  testAnimation();
  delay(2000);
  
  testSensorDisplay();
}

void loop() {
  // Cycle through different displays
  static int screen = 0;
  static unsigned long lastUpdate = 0;
  
  if (millis() - lastUpdate > 3000) {
    lastUpdate = millis();
    
    switch(screen) {
      case 0:
        showWelcome();
        break;
      case 1:
        showTemperature(25.5, 60.2);
        break;
      case 2:
        showGraph();
        break;
      case 3:
        showStatus();
        break;
    }
    
    screen = (screen + 1) % 4;
  }
}

void testText() {
  Serial.println("Test 1: Text Display");
  
  display.clearBuffer();
  display.setFont(u8g2_font_ncenB08_tr);
  display.drawStr(0, 10, "1.3\" OLED Test");
  display.setFont(u8g2_font_ncenB14_tr);
  display.drawStr(20, 35, "Hello!");
  display.setFont(u8g2_font_ncenB08_tr);
  display.drawStr(10, 50, "ESP32 Plant");
  display.drawStr(20, 62, "Monitor");
  display.sendBuffer();
}

void testShapes() {
  Serial.println("Test 2: Shapes");
  
  display.clearBuffer();
  
  // Draw rectangles
  display.drawFrame(0, 0, 40, 30);
  display.drawBox(45, 0, 40, 30);
  
  // Draw circles
  display.drawCircle(20, 50, 10);
  display.drawDisc(65, 50, 10);
  
  // Draw triangles
  display.drawTriangle(90, 10, 100, 30, 110, 10);
  display.drawTriangle(90, 40, 100, 60, 110, 40);
  
  display.sendBuffer();
}

void testAnimation() {
  Serial.println("Test 3: Animation");
  
  for(int i = 0; i < 128; i += 4) {
    display.clearBuffer();
    display.drawDisc(i, 32, 8);
    display.sendBuffer();
    delay(20);
  }
}

void testSensorDisplay() {
  Serial.println("Test 4: Sensor Display");
  
  display.clearBuffer();
  display.setFont(u8g2_font_ncenB08_tr);
  display.drawStr(15, 10, "Plant Monitor");
  display.drawLine(0, 12, 128, 12);
  
  display.drawStr(0, 25, "Temp:");
  display.setFont(u8g2_font_ncenB14_tr);
  display.drawStr(45, 25, "25.5");
  display.setFont(u8g2_font_ncenB08_tr);
  display.drawStr(95, 25, "C");
  
  display.drawStr(0, 45, "Hum:");
  display.setFont(u8g2_font_ncenB14_tr);
  display.drawStr(45, 45, "60.2");
  display.setFont(u8g2_font_ncenB08_tr);
  display.drawStr(95, 45, "%");
  
  display.drawStr(20, 62, "Status: OK");
  
  display.sendBuffer();
}

void showWelcome() {
  display.clearBuffer();
  display.setFont(u8g2_font_ncenB18_tr);
  display.drawStr(20, 25, "Plant");
  display.drawStr(10, 45, "Monitor");
  display.setFont(u8g2_font_ncenB08_tr);
  display.drawStr(45, 62, "v1.0");
  display.sendBuffer();
}

void showTemperature(float temp, float hum) {
  display.clearBuffer();
  
  // Temperature
  display.setFont(u8g2_font_ncenB08_tr);
  display.drawStr(10, 10, "TEMPERATURE");
  display.setFont(u8g2_font_ncenB24_tr);
  char tempStr[8];
  dtostrf(temp, 4, 1, tempStr);
  display.drawStr(15, 40, tempStr);
  display.setFont(u8g2_font_ncenB10_tr);
  display.drawStr(100, 40, "C");
  
  // Humidity
  display.setFont(u8g2_font_ncenB08_tr);
  char humStr[16];
  sprintf(humStr, "Humidity: %.1f%%", hum);
  display.drawStr(5, 62, humStr);
  
  display.sendBuffer();
}

void showGraph() {
  display.clearBuffer();
  display.setFont(u8g2_font_ncenB08_tr);
  display.drawStr(5, 10, "Temperature Graph");
  
  // Draw axes
  display.drawLine(10, 15, 10, 60);
  display.drawLine(10, 60, 120, 60);
  
  // Draw sample data
  int data[] = {50, 48, 52, 55, 53, 58, 60, 57, 59, 62};
  for(int i = 0; i < 9; i++) {
    int x1 = 15 + i * 11;
    int y1 = 60 - (data[i] - 40);
    int x2 = 15 + (i + 1) * 11;
    int y2 = 60 - (data[i + 1] - 40);
    display.drawLine(x1, y1, x2, y2);
  }
  
  display.sendBuffer();
}

void showStatus() {
  display.clearBuffer();
  display.setFont(u8g2_font_ncenB08_tr);
  display.drawStr(15, 10, "System Status");
  display.drawLine(0, 12, 128, 12);
  
  display.drawStr(0, 25, "Sensor:  OK");
  display.drawStr(0, 37, "Display: OK");
  display.drawStr(0, 49, "USB:     Connected");
  
  char uptimeStr[20];
  sprintf(uptimeStr, "Uptime:  %lus", millis() / 1000);
  display.drawStr(0, 62, uptimeStr);
  
  display.sendBuffer();
}
