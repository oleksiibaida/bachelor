#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ESPAsyncWebServer.h>
#include <EEPROM.h>

// Access Point (AP) konfigurieren
const char AP_SSID[] = "ESP8266";
const char AP_PASSWORD[] = "setupesp";
IPAddress ap_ip(10, 0, 0, 1);
IPAddress ap_gateway(10, 0, 0, 1);
IPAddress ap_subnet(255, 255, 255, 0);
AsyncWebServer server(80);
// maximale Laenge fuer WLAN-Zugangsdaten
const uint8_t MAX_SSID_LENGTH = 32;
const uint8_t MAX_PASSWORD_LENGTH = 32;
const uint8_t wifi_repeat = 10; // Anzahl der Versuche bis WLAN-Verbindung abgebrochen wird
const String html_page = R"rawliteral(
    <html>
    <body>
      <h2>Wi-Fi Configuration</h2>
      <form action="/save" method="POST">
        SSID:<br>
        <input type="text" name="ssid" required><br>
        Password:<br>
        <input type="password" name="password" required><br><br>
        <input type="submit" value="Submit">
      </form>
    </body>
    </html>
  )rawliteral";

const char MQTT_BROKER_ADRRESS[] = "192.144.1.1"; // IP von MQTT-Broker
const int MQTT_PORT = 1883;
const int buss_serial = 512; // Buffer Groesse fuer UAR-Verbindung
const char *CLIENT_ID = "DT04";
const char *TOPIC_COMMAND = "command";
char *SUBSCRIBE_TOPIC;
char *PUBLISH_TOPIC;

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
unsigned long lastMsg = 0;
#define MSG_BUFFER_SIZE (50)
char msg[MSG_BUFFER_SIZE];
int value = 0;

void setup_subscribe()
{
  SUBSCRIBE_TOPIC = (char *)malloc(strlen(TOPIC_COMMAND) + strlen(CLIENT_ID) + 2);
  if (SUBSCRIBE_TOPIC == NULL)
  {
    // Serial.print("Konnte nicht abonnieren. Default topic");
    SUBSCRIBE_TOPIC = "command/#";
  }
  else
  {
    strcpy(SUBSCRIBE_TOPIC, TOPIC_COMMAND);
    strcat(SUBSCRIBE_TOPIC, "/");
    strcat(SUBSCRIBE_TOPIC, CLIENT_ID);
  }
}

boolean connect_wifi(char *ssid, char *password)
{
  delay(10);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  for (uint8_t i = 0; i < wifi_repeat; i++)
  {
    if (WiFi.status() == WL_CONNECTED)
    {
      Serial.print("\nCONNECTED WIFI");
      Serial.print(WiFi.localIP());
      return true;
    }
    delay(1000);
  }
  return false;
}

void setup_ap()
{
  WiFi.mode(WIFI_AP);
  WiFi.softAP(AP_SSID, AP_PASSWORD);
  WiFi.softAPConfig(ap_ip, ap_gateway, ap_subnet);

  server.on("/", HTTP_GET, [](AsyncWebServerRequest *request)
            { request->send(200, "text/html", html_page); });

  server.on("/save", HTTP_POST, [](AsyncWebServerRequest *request)
            {
              // get input data
              String ssid = request->getParam("ssid", true)->value();
              String password = request->getParam("password", true)->value();
              if (ssid.length() > MAX_SSID_LENGTH - 1 || password.length() > MAX_PASSWORD_LENGTH - 1)
              {
                return;
              }
              Serial.print("\nGOT WIFI DATA");
              Serial.print(ssid);
              Serial.print(password);
              // String in char[]
              char new_ssid[MAX_SSID_LENGTH] = {0};
              strncpy(new_ssid, ssid.c_str(), MAX_SSID_LENGTH - 1);
              char new_password[MAX_PASSWORD_LENGTH] = {0};
              strncpy(new_password, password.c_str(), MAX_PASSWORD_LENGTH - 1);

              // in EEPROM speichern
              EEPROM.begin(128);
              // TODO clear EEPROM
              EEPROM.put(0, new_ssid);
              EEPROM.put(32, new_password);
              EEPROM.commit();
              EEPROM.end();

              request->send(200, "text/html", "WiFi saved. Rebooting...");
              ESP.restart(); });

  server.begin();
}

void callback(char *topic, byte *payload, unsigned int length)
{
  String id = String(topic).substring(String(topic).indexOf('/') + 1);
  if (id == CLIENT_ID)
  {
    String text = "";
    for (int i = 0; i < length; i++)
    {
      text += (char)payload[i];
    }
    text.trim();
    // Print in Arduino
    Serial.println(text);
  }
}

void connect_mqtt()
{
  // Loop bis verbunden
  while (!mqttClient.connected())
  {
    if (mqttClient.connect(CLIENT_ID))
    {
      // Serial.println("Verbunden mit dem Broker");
      mqttClient.subscribe(SUBSCRIBE_TOPIC);
      // Serial.print("\nSubscribed: ");
      // Serial.print(SUBSCRIBE_TOPIC);
    }
    else
    {
      // Serial.print("\nFehler beid der Verbindung. Status: ");
      // Serial.print(mqttClient.state()); // Status des CLients ausgeben
      delay(1000);
    }
  }
}

// Format topic:message
void readSerialData()
{
  if (Serial.available() > 0)
  {
    String readString = "";
    // Lese Daten aus Serial als String ab
    readString = Serial.readStringUntil('\n');
    // Serial.print("\nReceived SERIAL: ");
    // Serial.print(readString);
    if (sizeof(readString) > buss_serial)
    {
      // Serial.print("Message too long!");
      return;
    }
    // Serial.print("\nConvert String to char: ");
    // String in char - Feld konvertieren
    char readSerialChar[readString.length() + 1];
    readString.toCharArray(readSerialChar, readString.length() + 1);
    for (unsigned int i = 0; i < sizeof readSerialChar; i++)
    {
      // Serial.print(readSerialChar[i]);
    }

    // Suche Position von ':'
    char *delim_pos = strchr(readSerialChar, ':');
    if (delim_pos != NULL)
    {
      size_t topic_length = delim_pos - readSerialChar;
      char topic[topic_length + 1];
      strncpy(topic, readSerialChar, topic_length);
      topic[topic_length] = '\0';
      char *message = delim_pos + 1;
      PUBLISH_TOPIC = (char *)malloc(strlen(CLIENT_ID) + strlen(topic) + 2);
      if (PUBLISH_TOPIC == NULL)
      {
        // Serial.print("PUBLISH_TOPIC wurde nicht erstellt");
        PUBLISH_TOPIC = topic;
      }
      else
      {
        strcpy(PUBLISH_TOPIC, topic);
        strcat(PUBLISH_TOPIC, "/");
        strcat(PUBLISH_TOPIC, CLIENT_ID);
      }
      // Serial.print("\nPublish Topic: ");
      // Serial.print(PUBLISH_TOPIC);
      // Serial.print(" Nachricht:" );
      // Serial.print(message);
      // MQTT-Nachricht senden
      mqttClient.publish(PUBLISH_TOPIC, message);
    }
    else // kein : gefunden
    {
      // Serial.print("FALSCHES FORMAT");
      return;
    }
  }
}

bool is_valid_string(char *data, int max_length)
{
  if (strlen(data) == 0 or strlen(data) > max_length)
    return false;
  for (int i = 0; i < max_length; i++)
  {
    if (data[i] == '\0')
      return true; // End of valid String
    if (data[i] == 0xFF)
      return false;
  }
  return false;
}

void setup()
{
  Serial.begin(9600);
  // turn on LED while setting up
  pinMode(1, OUTPUT);
  digitalWrite(1, LOW);
  setup_subscribe();
  // clear_eeprom();
  // GET WiFi Daten aus EEPROM
  EEPROM.begin(128);
  char eeprom_ssid[MAX_SSID_LENGTH] = {0};
  char eeprom_password[MAX_PASSWORD_LENGTH] = {0};
  EEPROM.get(0, eeprom_ssid);
  EEPROM.get(32, eeprom_password);
  EEPROM.end();
  Serial.print("\nREAD FROM EEPROM");
  Serial.print(eeprom_ssid);
  Serial.print(eeprom_password);
  // Daten gefunden
  if (is_valid_string(eeprom_ssid, MAX_SSID_LENGTH) && is_valid_string(eeprom_password, MAX_PASSWORD_LENGTH))
  {
    if (connect_wifi(eeprom_ssid, eeprom_password))
    {
      mqttClient.setServer(WiFi.gatewayIP(), MQTT_PORT);
      mqttClient.setCallback(callback);
      connect_mqtt();
      digitalWrite(1, HIGH);
    }
    else
    {
      setup_ap();
    }
  }
  else
  { // keine WLAN-DAten gefunden
    setup_ap();
    // digitalWrite(2, LOW);
  }
}

void loop()
{
  if (WiFi.status() != WL_CONNECTED)
  {
    // connect_wifi();
  }
  if (!mqttClient.connected())
  {
    connect_mqtt();
  }
  mqttClient.loop();
  readSerialData();
}