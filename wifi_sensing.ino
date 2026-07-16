#include "WiFi.h"
#include "esp_wifi.h"
#include "wifi_credential.h"
#include <WiFiUdp.h>

const char* ssid = SSID;
const char* password = PASS;

WiFiUDP udp;
unsigned long lastPing = 0;
const int PING_INTERVAL_MS = 50;
bool wifiConnected = false;
unsigned long connectionTimeChecked = 0;

void wifi_csi_callback(void *ctx, wifi_csi_info_t *data) {
  wifi_csi_info_t d = *data;
  Serial.print("CSI_DATA,");
  Serial.print(millis());
  Serial.print(",");
  Serial.print(d.rx_ctrl.rssi);
  Serial.print(",");
  Serial.print(d.rx_ctrl.channel);
  Serial.print(",");
  Serial.print(d.len);
  Serial.print(",");
  for (int i = 0; i < d.len; i++) {
    Serial.print((int)d.buf[i]);
    Serial.print(" ");
  }
  Serial.println();
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  udp.begin(12345);

  wifi_csi_config_t configuration_csi;
  configuration_csi.lltf_en = true;
  configuration_csi.htltf_en = true;
  configuration_csi.stbc_htltf2_en = true;
  configuration_csi.ltf_merge_en = true;
  configuration_csi.channel_filter_en = false;
  configuration_csi.manu_scale = false;

  esp_wifi_set_csi_config(&configuration_csi);
  esp_wifi_set_csi_rx_cb(&wifi_csi_callback, NULL);
  esp_wifi_set_csi(true);

  Serial.println("CSI collection started...");
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    wifiConnected = false;
  } else {
    wifiConnected = true;
  }
  
  if (millis() - connectionTimeChecked >= 5000 && !wifiConnected) {
    connectionTimeChecked = millis();
    Serial.println("Wifi not connected. Attempting to reconnect...");
    WiFi.begin(ssid, password);
  }
  if (millis() - lastPing >= PING_INTERVAL_MS) {
    lastPing = millis();
    udp.beginPacket(WiFi.gatewayIP(), 9);
    udp.write((uint8_t)0);
    udp.endPacket();
  }
}
