#include <WiFi.h>
#include <HTTPClient.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <LoRa.h>
#include <SPI.h>
#include <Wire.h>
#include "mbedtls/aes.h"
#include <ArduinoJson.h>

#include <WiFiUdp.h>

// ================= CONFIG =================
const char* ssid = "WIFI_SSID";
const char* password = "WIFI_PASSWORD";

WiFiUDP udp;
String backend_ip = "";
String dynamic_backend_url = "";

unsigned char midway_key[32] = {'M','I','D','W','A','Y','K','E','Y','A','E','S','1','2','3','4','5','6','7','8','9','0','A','B','C','D','E','F','1','2','3','4'};
unsigned char aes_iv[16]     = {0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f};

// Node Keys database mapped by OrigID
unsigned char key_wrist[32] = {'W','R','I','S','T','B','A','N','D','K','E','Y','1','2','3','4','5','6','7','8','9','0','1','2','3','4','5','6','7','8','9','0'};
unsigned char key_nodeA[32] = {'N','O','D','E','A','K','E','Y','A','E','S','1','2','3','4','5','6','7','8','9','0','A','B','C','D','E','F','1','2','3','4','5'};
unsigned char key_nodeB[32] = {'N','O','D','E','B','K','E','Y','A','E','S','1','2','3','4','5','6','7','8','9','0','A','B','C','D','E','F','1','2','3','4','5'};
unsigned char key_nodeC[32] = {'N','O','D','E','C','K','E','Y','A','E','S','1','2','3','4','5','6','7','8','9','0','A','B','C','D','E','F','1','2','3','4','5'};

// Status LEDs
#define LED_RED 27
#define LED_YELLOW 25
#define LED_GREEN 33
unsigned long redLedOffTime = 0;

// LoRa & OLED
#define LORA_SS 5
#define LORA_RST 14
#define LORA_DIO0 26
#define OLED_SDA 4
#define OLED_SCL 15
Adafruit_SSD1306 display(128, 64, &Wire, -1);

String recentMsgIDs[30];
int msgIdx = 0;

const char* DEVICE_API_KEY = "antigravity_secret_123";

bool isMsgSeen(String mid) {
  for(int i=0; i<30; i++) {
    if(recentMsgIDs[i] == mid) return true;
  }
  return false;
}
void addMsgSeen(String mid) {
  recentMsgIDs[msgIdx] = mid;
  msgIdx = (msgIdx + 1) % 30;
}

byte hexCharToByte(char c) {
  if (c >= '0' && c <= '9') return c - '0';
  if (c >= 'A' && c <= 'F') return c - 'A' + 10;
  if (c >= 'a' && c <= 'f') return c - 'a' + 10;
  return 0;
}

void hexStringToBytes(String hex, unsigned char* outBytes, int outLen) {
  for(int i=0; i<outLen; i++) {
    outBytes[i] = (hexCharToByte(hex[i*2]) << 4) | hexCharToByte(hex[i*2 + 1]);
  }
}

String decryptHex(String hexMsg, unsigned char* key) {
  int len = hexMsg.length() / 2;
  unsigned char encrypted[len];
  hexStringToBytes(hexMsg, encrypted, len);

  unsigned char decrypted[len];
  unsigned char iv_copy[16];
  memcpy(iv_copy, aes_iv, 16);

  mbedtls_aes_context aes;
  mbedtls_aes_init(&aes);
  mbedtls_aes_setkey_dec(&aes, key, 256);
  mbedtls_aes_crypt_cbc(&aes, MBEDTLS_AES_DECRYPT, len, iv_copy, encrypted, decrypted);
  mbedtls_aes_free(&aes);

  uint8_t pad = decrypted[len - 1];
  int clearLen = len - pad;
  if (clearLen < 0 || clearLen > len) clearLen = len;

  String clearText = "";
  for(int i=0; i<clearLen; i++) clearText += (char)decrypted[i];
  return clearText;
}

String encryptToHex(String message, unsigned char* key) {
  int input_len = message.length();
  int padded_len = ((input_len / 16) + 1) * 16;
  unsigned char input[padded_len];
  uint8_t output[padded_len];
  memset(input, 0, padded_len);
  memcpy(input, message.c_str(), input_len);
  uint8_t pad_val = padded_len - input_len;
  for (int i = input_len; i < padded_len; i++) input[i] = pad_val;

  unsigned char iv_copy[16];
  memcpy(iv_copy, aes_iv, 16);

  mbedtls_aes_context aes;
  mbedtls_aes_init(&aes);
  mbedtls_aes_setkey_enc(&aes, key, 256);
  mbedtls_aes_crypt_cbc(&aes, MBEDTLS_AES_ENCRYPT, padded_len, iv_copy, input, output);
  mbedtls_aes_free(&aes);

  String hexStr = "";
  for(int i=0; i<padded_len; i++) {
    if(output[i] < 0x10) hexStr += "0";
    hexStr += String(output[i], HEX);
  }
  return hexStr;
}

bool parseDecryptedPayload(String origId, String decryptedPayload, float &lat, float &lon, int &pulse, bool &sos) {
  lat = 30.800000;
  lon = 76.850000;
  pulse = 75;
  sos = false;

  if (origId == "Node-A") { lat = 29.211372; lon = 77.017304; }
  else if (origId == "Node-B") { lat = 29.210347; lon = 77.015948; }
  else if (origId == "Node-C") { lat = 29.211414; lon = 77.016054; }

  if (decryptedPayload.startsWith("RNR")) {
    sos = true;
    return true;
  }

  int bpmIdx = decryptedPayload.indexOf("BPM:");
  int latIdx = decryptedPayload.indexOf("LAT:");
  int lonIdx = decryptedPayload.indexOf("LON:");
  int rnrIdx = decryptedPayload.indexOf("RNR:");

  if (bpmIdx >= 0 && latIdx >= 0 && lonIdx >= 0) {
    int bpmEnd = decryptedPayload.indexOf('|', bpmIdx);
    int latEnd = decryptedPayload.indexOf('|', latIdx);
    int lonEnd = decryptedPayload.indexOf('|', lonIdx);
    if (bpmEnd < 0) bpmEnd = decryptedPayload.length();
    if (latEnd < 0) latEnd = decryptedPayload.length();
    if (lonEnd < 0) lonEnd = decryptedPayload.length();

    pulse = decryptedPayload.substring(bpmIdx + 4, bpmEnd).toInt();
    lat = decryptedPayload.substring(latIdx + 4, latEnd).toFloat();
    lon = decryptedPayload.substring(lonIdx + 4, lonEnd).toFloat();

    if (rnrIdx >= 0) {
      int rnrEnd = decryptedPayload.indexOf('|', rnrIdx);
      if (rnrEnd < 0) rnrEnd = decryptedPayload.length();
      String rnrVal = decryptedPayload.substring(rnrIdx + 4, rnrEnd);
      sos = (rnrVal == "1");
    }
    return true;
  }

  // Unsupported payloads (e.g. CP:user_1) are ignored for telemetry ingest.
  return false;
}

void forwardToBackend(String origId, String decryptedPayload) {
  if(WiFi.status() != WL_CONNECTED || dynamic_backend_url == "") return;

  float lat = 0.0;
  float lon = 0.0;
  int pulse = 0;
  bool sos = false;

  if (!parseDecryptedPayload(origId, decryptedPayload, lat, lon, pulse, sos)) {
    Serial.println("Skipping unsupported payload: " + decryptedPayload);
    return;
  }

  HTTPClient http;
  http.begin(dynamic_backend_url);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("x-device-key", DEVICE_API_KEY);

  StaticJsonDocument<384> doc;
  doc["device_id"] = origId;
  doc["latitude"] = lat;
  doc["longitude"] = lon;
  doc["pulse"] = pulse;
  doc["battery"] = 100;
  doc["sos"] = sos;

  String requestBody;
  serializeJson(doc, requestBody);
  int httpResponseCode = http.POST(requestBody);
  String responseBody = http.getString();
  Serial.println("POST code: " + String(httpResponseCode));
  Serial.println("POST body: " + requestBody);
  Serial.println("RESP body: " + responseBody);
  http.end();
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_RED, OUTPUT);
  pinMode(LED_YELLOW, OUTPUT);
  pinMode(LED_GREEN, OUTPUT);

  digitalWrite(LED_YELLOW, HIGH); 

  Wire.begin(OLED_SDA, OLED_SCL);
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) while(1);
  display.clearDisplay(); display.setTextColor(WHITE); display.setCursor(0,0);
  display.println("MIDWAY INIT"); display.display();

  WiFi.begin(ssid, password);
  while(WiFi.status() != WL_CONNECTED) {
    delay(500); Serial.print(".");
  }
  digitalWrite(LED_GREEN, HIGH); 
  display.println("WIFI CONNECTED"); display.display();
  
  // Dynamic IP Discovery via UDP
  udp.begin(5005);
  display.clearDisplay(); display.setCursor(0,0);
  display.println("WAITING FOR BACKEND IP..."); display.display();

  while(backend_ip == "") {
    int packetSize = udp.parsePacket();
    if (packetSize) {
      char incomingPacket[255];
      int len = udp.read(incomingPacket, 255);
      if (len > 0) incomingPacket[len] = 0;
      
      String msg = String(incomingPacket);
      if (msg.startsWith("LIFE_LINK_IP:")) {
        backend_ip = msg.substring(13);
        backend_ip.trim();
        dynamic_backend_url = "http://" + backend_ip + ":8000/api/v1/telemetry";
        Serial.println("Found backend at: " + backend_ip);
        display.clearDisplay(); display.setCursor(0,0);
        display.println("FOUND SERVER:");
        display.println(backend_ip); display.display();
      }
    }
    digitalWrite(LED_YELLOW, (millis() / 200) % 2); // blink Yellow while scanning
    delay(10);
  }
  digitalWrite(LED_YELLOW, HIGH); 
  delay(1000);

  SPI.begin(18, 19, 23, -1);
  LoRa.setPins(LORA_SS, LORA_RST, LORA_DIO0);
  if (!LoRa.begin(433E6)) while(1);
  LoRa.setSyncWord(0x34);
}

void loop() {
  if (millis() > redLedOffTime) {
    digitalWrite(LED_RED, LOW);
  } else {
    digitalWrite(LED_RED, (millis() / 200) % 2); // blink continuously
  }

  int packetSize = LoRa.parsePacket();
  if (packetSize) {
    String incoming = "";
    while(LoRa.available()) incoming += (char)LoRa.read();
    
    int firstColon = incoming.indexOf(':');
    int secondColon = incoming.indexOf(':', firstColon + 1);

    if(firstColon > 0 && secondColon > firstColon) {
      String msgId = incoming.substring(0, firstColon);
      String origId = incoming.substring(firstColon + 1, secondColon);
      String hexData = incoming.substring(secondColon + 1);

      if(!isMsgSeen(msgId)) {
        addMsgSeen(msgId);
        Serial.println("Midway Rcvd: " + origId);

        unsigned char* targetKey = NULL;
        if(origId == "Wristband") targetKey = key_wrist;
        else if(origId == "Node-A") targetKey = key_nodeA;
        else if(origId == "Node-B") targetKey = key_nodeB;
        else if(origId == "Node-C") targetKey = key_nodeC;

        if (targetKey != NULL) {
          String decrypted = decryptHex(hexData, targetKey);
          Serial.println("Decrypted: " + decrypted);

          if(decrypted.indexOf("RNR") >= 0 || decrypted.indexOf("BPM:") >= 0) {
              if (decrypted.indexOf("RNR:1") >= 0 || decrypted == "RNR") {
                 redLedOffTime = millis() + 2000;
              }
          }

          display.clearDisplay(); display.setCursor(0,0);
          display.println("PAYLOAD: " + origId);
          display.display();

          forwardToBackend(origId, decrypted);
        }
      }
    }
  }
}
