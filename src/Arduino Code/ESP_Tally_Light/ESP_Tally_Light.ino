#include <ESP8266WiFi.h>
#include <PubSubClient.h>


#include <FastLED.h>

#define LED_PIN D5
#define NUM_LEDS 4
#define BRIGHTNESS 5
#define LED_TYPE WS2812B
#define COLOR_ORDER GRB

unsigned long lastHeartbeat = 0;       // Zeitpunkt der letzten Nachricht
const unsigned long heartbeatInterval = 10000; // 10 Sekunden
unsigned long lastWifiReconnectAttempt = 0;
const unsigned long wifiReconnectInterval = 5000;
unsigned long lastMqttReconnectAttempt = 0;
const unsigned long mqttReconnectInterval = 5000;
bool wifiWasConnected = false;
bool mqttAttempted = false;

CRGB leds[NUM_LEDS];
uint8_t gHue = 0; // Globale Farbabstufung (Hue)

#define character "C"


// 🔧 Deine WLAN-Daten
const char* ssid = "Tally-Lights";
const char* password = "MeinSicheresPasswort";

// 🔧 MQTT Broker (Raspberry Pi)
const char* mqtt_server = "192.168.4.1";  // Pi-IP im Access-Point-Modus

WiFiClient espClient;
PubSubClient client(espClient);



// Topic für Antworten
const char* response_topic = "tally/lights/response";
String topic = String("tally/lights/") + character;


void setup_wifi() {
  delay(10);
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.persistent(false);
  Serial.println();
  Serial.print("Verbinde mit WLAN: ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  lastWifiReconnectAttempt = millis();
}

bool ensure_wifi() {
  if (WiFi.status() == WL_CONNECTED) {
    if (!wifiWasConnected) {
      wifiWasConnected = true;
      Serial.print("WLAN verbunden: ");
      Serial.println(WiFi.localIP());
    }
    return true;
  }

  if (wifiWasConnected) {
    wifiWasConnected = false;
    espClient.stop();
    mqttAttempted = false;
    Serial.println("WLAN getrennt");
    fill_solid(leds, NUM_LEDS, CRGB(0, 0, 255));
    FastLED.show();
  }

  unsigned long now = millis();
  if (now - lastWifiReconnectAttempt >= wifiReconnectInterval) {
    lastWifiReconnectAttempt = now;
    WiFi.reconnect();
  }
  return false;
}

void callback(char* topic, byte* payload, unsigned int length) {
  // Payload in String wandeln
  String msg;
  for (unsigned int i = 0; i < length; i++) {
    msg += (char)payload[i];
  }
  msg.trim(); // Leerzeichen entfernen
  Serial.print("Empfangen: ");
  Serial.println(msg);

  // 🎨 HEX-Farbcode? (#RRGGBB oder RRGGBB)
  if (msg.startsWith("#")) msg = msg.substring(1);
  if (msg.length() == 6) {
    long number = strtol(msg.c_str(), NULL, 16);
    uint8_t r = (number >> 16) & 0xFF;
    uint8_t g = (number >> 8) & 0xFF;
    uint8_t b = number & 0xFF;

    //fill_solid(leds, NUM_LEDS, CRGB(255, 0, 255));
    fill_solid(leds, NUM_LEDS, CRGB(r, g, b));
    FastLED.show();
  }
}

bool ensure_mqtt() {
  if (client.connected()) {
    return true;
  }

  unsigned long now = millis();
  if (mqttAttempted && now - lastMqttReconnectAttempt < mqttReconnectInterval) {
    return false;
  }
  mqttAttempted = true;
  lastMqttReconnectAttempt = now;
  Serial.println("Verbinde mit MQTT Broker...");
  if (!client.connect((String("D1MiniTally") + character).c_str())) {
    Serial.print("MQTT-Verbindung fehlgeschlagen, rc=");
    Serial.println(client.state());
    return false;
  }
  if (!client.subscribe(topic.c_str(), 1)) {
    client.disconnect();
    return false;
  }
  Serial.println("MQTT verbunden");
  lastHeartbeat = millis() - heartbeatInterval;
  return true;
}

void setup() {
  Serial.begin(115200);
  Serial.println(topic);  // Ausgabe: tally/lights/C

  FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS);
  FastLED.setBrightness(BRIGHTNESS);

  
  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
  client.setSocketTimeout(2);
}

void loop() {
  if (!ensure_wifi() || !ensure_mqtt()) {
    delay(100);
    return;
  }
  client.loop();

  // Heartbeat senden
  unsigned long now = millis();
  if (now - lastHeartbeat > heartbeatInterval) {
    lastHeartbeat = now;

    // Nachricht an Status-Topic senden
    String msg = String(character);  // ID des Geräts
    client.publish("tally/lights/status", msg.c_str());
    Serial.println("Heartbeat gesendet: " + msg);
  }
}
