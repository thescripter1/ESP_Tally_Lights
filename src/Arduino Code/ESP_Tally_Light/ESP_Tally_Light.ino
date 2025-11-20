#include <ESP8266WiFi.h>
#include <PubSubClient.h>


#include <FastLED.h>

#define LED_PIN D4
#define NUM_LEDS 4
#define BRIGHTNESS 5
#define LED_TYPE WS2812B
#define COLOR_ORDER GRB

unsigned long lastHeartbeat = 0;       // Zeitpunkt der letzten Nachricht
const unsigned long heartbeatInterval = 10000; // 10 Sekunden

CRGB leds[NUM_LEDS];
uint8_t gHue = 0; // Globale Farbabstufung (Hue)

#define character "A"


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
  Serial.println();
  Serial.print("Verbinde mit WLAN: ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    fill_solid(leds, NUM_LEDS, CRGB(0, 0, 255));
    FastLED.show();
    delay(1000);
    Serial.print(".");
    fill_solid(leds, NUM_LEDS, CRGB::Black);
    FastLED.show();
    delay(1000);
  }

  Serial.println("");
  Serial.println("WLAN verbunden!");
  fill_solid(leds, NUM_LEDS, CRGB(0, 255, 0));
  FastLED.show();
  Serial.println("IP-Adresse: ");
  Serial.println(WiFi.localIP());
}

void callback(char* topic, byte* payload, unsigned int length) {
  if(length == 0) return; // Sicherheit
  
  // Nur das erste Byte interpretieren
  char val = (char)payload[0];
  Serial.println(val);

  switch(val) {
    case '0': fill_solid(leds, NUM_LEDS, CRGB::Black); break;
    case '1': fill_solid(leds, NUM_LEDS, CRGB(255,0,0)); break;
    case '5': fill_solid(leds, NUM_LEDS, CRGB(255,0,255)); break;
    default: return; // unbekannter Code
  }
  FastLED.show();
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Verbindung zu MQTT Broker...");
    if (client.connect("D1MiniTallyA")) {
      Serial.println("Verbunden!");
      client.subscribe("tally/lights/A");
    } else {
      Serial.print("Fehler, rc=");
      Serial.print(client.state());
      Serial.println(" versuche erneut in 5 Sekunden");
      delay(5000);
    }
  }
}

void setup() {

  Serial.println(topic);  // Ausgabe: tally/lights/C

  FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS);
  FastLED.setBrightness(BRIGHTNESS);

  Serial.begin(115200);
  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    reconnect();
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