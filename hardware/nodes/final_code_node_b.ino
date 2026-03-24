#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <LoRa.h>
#include <MFRC522.h>
#include <SPI.h>
#include <Wire.h>
#include "mbedtls/aes.h"

// ================= DEVICE & MESH CONFIG =================
const char *NODE_ID = "Node-B";
unsigned char aes_key[32] = {'N','O','D','E','B','K','E','Y','A','E','S','1','2','3','4','5','6','7','8','9','0','A','B','C','D','E','F','1','2','3','4','5'};
unsigned char aes_iv[16]  = {0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f};

// Mesh loop prevention
String recentMsgIDs[15];
int msgIdx = 0;

// ================= PINS =================
#define LORA_SS 5
#define LORA_RST 14
#define LORA_DIO0 26
#define OLED_SDA 4
#define OLED_SCL 15
Adafruit_SSD1306 display(128, 64, &Wire, -1);
#define SOS_BUTTON 32
#define RFID_SS 21
#define RFID_RST 27
MFRC522 rfid(RFID_SS, RFID_RST);

bool isMsgSeen(String mid) {
  for(int i=0; i<15; i++) {
    if(recentMsgIDs[i] == mid) return true;
  }
  return false;
}

bool isButtonPressed() {
  if (digitalRead(SOS_BUTTON) != LOW) return false;
  delay(30);
  return digitalRead(SOS_BUTTON) == LOW;
}
void addMsgSeen(String mid) {
  recentMsgIDs[msgIdx] = mid;
  msgIdx = (msgIdx + 1) % 15;
}

void forwardMeshPacket(String packet) {
  LoRa.beginPacket();
  LoRa.print(packet);
  LoRa.endPacket();
}

String encryptToHex(String message) {
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
  mbedtls_aes_setkey_enc(&aes, aes_key, 256);
  mbedtls_aes_crypt_cbc(&aes, MBEDTLS_AES_ENCRYPT, padded_len, iv_copy, input, output);
  mbedtls_aes_free(&aes);

  String hexStr = "";
  for(int i=0; i<padded_len; i++) {
    if(output[i] < 0x10) hexStr += "0";
    hexStr += String(output[i], HEX);
  }
  return hexStr;
}

void generateOrigPacketAndSend(String payload) {
  String mid = "M" + String(random(10000, 99999));
  addMsgSeen(mid);
  String hexStr = encryptToHex(payload);
  String packet = mid + ":" + String(NODE_ID) + ":" + hexStr;
  Serial.println("Originated: " + packet);
  
  display.clearDisplay(); display.setCursor(0,0);
  display.print("TX: " + payload); display.display();
  
  forwardMeshPacket(packet);
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Wire.begin(OLED_SDA, OLED_SCL);
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) while(1);
  display.clearDisplay(); display.setTextColor(WHITE); display.setCursor(0,0);
  display.print("NODE: "); display.println(NODE_ID); display.display();

  pinMode(LORA_SS, OUTPUT); pinMode(RFID_SS, OUTPUT);
  digitalWrite(LORA_SS, HIGH); digitalWrite(RFID_SS, HIGH);
  SPI.begin(18, 19, 23, -1);
  LoRa.setPins(LORA_SS, LORA_RST, LORA_DIO0);
  if (!LoRa.begin(433E6)) {
      display.println("LORA FAILED"); display.display();
      while(1);
  }
  LoRa.setSyncWord(0x34);
  
  pinMode(SOS_BUTTON, INPUT_PULLUP);
  rfid.PCD_Init();
  randomSeed(analogRead(0));
  display.println("Mesh Ready."); display.display();
}

void loop() {
  if (isButtonPressed()) {
    generateOrigPacketAndSend("RNR:1");
    delay(2000);
  }

  if (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) {
    generateOrigPacketAndSend("CP:user_1:Node-B");
    rfid.PICC_HaltA();
    rfid.PCD_StopCrypto1();
    delay(2000);
  }

  int packetSize = LoRa.parsePacket();
  if (packetSize) {
    String incoming = "";
    while(LoRa.available()) incoming += (char)LoRa.read();
    
    int firstColon = incoming.indexOf(':');
    if(firstColon > 0) {
      String msgId = incoming.substring(0, firstColon);
      if(!isMsgSeen(msgId)) {
        addMsgSeen(msgId);
        Serial.println("Forwarding: " + incoming);
        display.clearDisplay(); display.setCursor(0,0); display.println("FWD: " + msgId); display.display();
        // PASS-THROUGH NO DECRYPTION
        forwardMeshPacket(incoming); 
      }
    }
  }
}
