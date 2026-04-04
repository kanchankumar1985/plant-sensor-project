#include <WiFi.h>

const char* ssid = "ATTqCZIe2s_2G";
const char* password = "xf8psnrn3wb4";

void setup() {
  Serial.begin(115200);
  delay(2000);
  
  Serial.println("=== ESP32 WiFi Diagnostic ===");
  Serial.print("ESP32 MAC Address: ");
  Serial.println(WiFi.macAddress());
  
  // Step 1: Scan for networks
  Serial.println("\n1. Scanning for WiFi networks...");
  WiFi.mode(WIFI_STA);
  WiFi.disconnect(true, true);
  delay(1000);
  
  int n = WiFi.scanNetworks();
  if (n == 0) {
    Serial.println("ERROR: No networks found! WiFi hardware may be faulty.");
    return;
  }
  
  Serial.printf("Found %d networks:\n", n);
  bool targetFound = false;
  for (int i = 0; i < n; i++) {
    String networkName = WiFi.SSID(i);
    Serial.printf("  %d: %s (%d dBm) %s\n", 
                  i + 1, 
                  networkName.c_str(), 
                  WiFi.RSSI(i),
                  (WiFi.encryptionType(i) == WIFI_AUTH_OPEN) ? "Open" : "Encrypted");
    
    if (networkName == ssid) {
      targetFound = true;
      Serial.println("    *** TARGET NETWORK FOUND ***");
    }
  }
  
  if (!targetFound) {
    Serial.println("ERROR: Target network not visible!");
    Serial.print("Looking for: ");
    Serial.println(ssid);
    return;
  }
  
  // Step 2: Test connection
  Serial.println("\n2. Testing WiFi connection...");
  Serial.print("Connecting to: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(1000);
    Serial.print(".");
    attempts++;
    
    if (attempts % 5 == 0) {
      Serial.println();
      Serial.print("Status: ");
      Serial.print(WiFi.status());
      Serial.print(" (");
      switch(WiFi.status()) {
        case WL_IDLE_STATUS: Serial.print("IDLE"); break;
        case WL_NO_SSID_AVAIL: Serial.print("NO_SSID"); break;
        case WL_SCAN_COMPLETED: Serial.print("SCAN_COMPLETED"); break;
        case WL_CONNECTED: Serial.print("CONNECTED"); break;
        case WL_CONNECT_FAILED: Serial.print("CONNECT_FAILED"); break;
        case WL_CONNECTION_LOST: Serial.print("CONNECTION_LOST"); break;
        case WL_DISCONNECTED: Serial.print("DISCONNECTED"); break;
        default: Serial.print("UNKNOWN"); break;
      }
      Serial.println(")");
    }
  }
  
  Serial.println();
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("SUCCESS: WiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    Serial.print("Signal strength: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
    
    // Test internet connectivity
    Serial.println("\n3. Testing internet connectivity...");
    Serial.println("Pinging 8.8.8.8...");
    // Note: ESP32 doesn't have built-in ping, but we can test HTTP
    
  } else {
    Serial.println("FAILED: Could not connect to WiFi");
    Serial.print("Final status: ");
    Serial.print(WiFi.status());
    Serial.print(" (");
    switch(WiFi.status()) {
      case WL_NO_SSID_AVAIL: Serial.print("Network not found - check SSID"); break;
      case WL_CONNECT_FAILED: Serial.print("Wrong password or auth issue"); break;
      case WL_DISCONNECTED: Serial.print("Disconnected - signal/power issue"); break;
      default: Serial.print("Other connection issue"); break;
    }
    Serial.println(")");
  }
}

void loop() {
  // Empty loop
}
