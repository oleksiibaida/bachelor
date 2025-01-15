#include <ESP8266WiFi.h>
#include <PubSubClient.h>

// Hotspot ist Raspberry PI
const char WIFI_SSID[] = "RaspEsp";
const char WIFI_PASSWORD[] = "mqtt1234";
const char MQTT_BROKER_ADRRESS[] = "192.144.1.1"; // IP von Raspberry
const int MQTT_PORT = 1883;
const int buss_serial = 50; // Buffer Groesse fuer UAR-Verbindung
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

void connect_wifi()
{
  delay(10);
  // We start by connecting to a WiFi network
  // Serial.println();
  // Serial.print("Connecting to ");
  // Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    // Serial.print(".");
  }

  // Serial.println("");
  // Serial.println("WiFi connected");
  // Serial.println("IP address: ");
  // Serial.println(WiFi.localIP());
}

void callback(char *topic, byte *payload, unsigned int length)
{
  // Serial.print("Nacricht erhalten. Topic: ");
  // Serial.print(topic);
  // Serial.print(" Text: ");
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

void setup()
{
  Serial.begin(9600);
  setup_subscribe();
  connect_wifi();
  mqttClient.setServer(WiFi.gatewayIP(), MQTT_PORT);
  mqttClient.setCallback(callback);
  connect_mqtt();
}

void loop()
{
  if (WiFi.status() != WL_CONNECTED)
  {
    connect_wifi();
  }
  if (!mqttClient.connected())
  {
    connect_mqtt();
  }
  mqttClient.loop();
  readSerialData();
}