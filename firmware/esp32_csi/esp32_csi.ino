/* WiFi Human Detection - ESP32 CSI Collector
 * Hardware-specific CSI configuration is intentionally left as a TODO until
 * the exact ESP32 model is known. Expected serial output:
 * timestamp,csi_0,csi_1,...,csi_N
 */
#include <Arduino.h>
#include <WiFi.h>
const char* WIFI_SSID="YOUR_WIFI_SSID";
const char* WIFI_PASSWORD="YOUR_WIFI_PASSWORD";
void setup(){
  Serial.begin(115200); delay(1000); WiFi.mode(WIFI_STA); WiFi.begin(WIFI_SSID,WIFI_PASSWORD);
  while(WiFi.status()!=WL_CONNECTED){delay(500);Serial.print(".");}
  Serial.println("\nWiFi connected: "+WiFi.localIP().toString());
  // TODO: configure CSI, register callback, enable CSI for your ESP32 model.
}
void loop(){ delay(100); }
