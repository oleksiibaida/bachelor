#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <MycilaEasyDisplay.h>
#include <ESPAsyncWebServer.h>
#include <EEPROM.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Adafruit_BME680.h>

#define SDA2 17
#define SCL2 16
#define I2C_DISPLAY_HEX 0x3C
#define I2C_BME_HEX 0x77
#define I2C_VCNL_HEX 0x60
#define DEVICE_ID "esp32display"

const uint8_t display_font_size = 18;

// Access Point (AP) konfigurieren
const char AP_SSID[] = "ESP32";
const char AP_PASSWORD[] = "setupesp32";
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

// MQTT
const char MQTT_BROKER_ADRRESS[] = "192.168.1.10"; // IP von MQTT-BROKER
const int MQTT_PORT = 1883;
const char *TOPIC_COMMAND = "command";
char *SUBSCRIBE_TOPIC;
char *PUBLISH_TOPIC;

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
TwoWire i2cScan = TwoWire(1);
Mycila::EasyDisplay display;
// BME680
Adafruit_BME680 bme_sensor;

/*===WIFI===*/
bool wifi_connect(char *ssid, char *password)
{
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  WiFi.setAutoReconnect(true);
  for (uint8_t i = 0; i < wifi_repeat; i++)
  {
    if (WiFi.status() == WL_CONNECTED)
    {
      Serial.println(WiFi.localIP());

      return true;
    }
    delay(500);
  }
  return false;
}

void setup_ap()
{
  WiFi.mode(WIFI_AP);
  WiFi.softAP(AP_SSID, AP_PASSWORD);
  WiFi.softAPConfig(ap_ip, ap_gateway, ap_subnet);

  // M5.Lcd.fillRect(0, 0, M5.Lcd.width(), M5.Lcd.height(), TFT_RED);
  // M5.Lcd.setCursor(X_OFFSET, 0);
  // M5.Lcd.println("SET UP WIFI ");
  // M5.Lcd.setCursor(X_OFFSET, 20);
  // M5.Lcd.println("GO TO 10.0.0.1");
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
              delay(1000);
              ESP.restart(); });

  server.begin();
}

void display_connection()
{
  display.home.clear();
  if (WiFi.status() == WL_CONNECTED)
  {
    display.home.print("WIFI OK ");
    if (mqttClient.connected())
    {
      display.home.print("| MQTT OK\n");
    }
    else
    {
      display.home.print("| MQTT ERROR\n");
    }
  }
  else
  {
    display.home.printf("WIFI ERROR!\nCONNECT TO SSID:%s \nPASS:%s\nGO TO 10.0.0.1\n", AP_SSID, AP_PASSWORD);
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

/*===MQTT===*/
/*Wird beim Empfang der MQTT-Nachricht aufgerufen*/
void callback(char *topic, byte *payload, unsigned int length)
{
  // Serial.print("Nacricht erhalten. Topic: ");
  // Serial.print(topic);
  // Serial.print(" Text: ");
  String id = String(topic).substring(String(topic).indexOf('/') + 1);
  if (id == DEVICE_ID)
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

void set_topics()
{
  SUBSCRIBE_TOPIC = (char *)malloc(strlen(TOPIC_COMMAND) + strlen(DEVICE_ID) + 2);
  // PUBLISH_TOPIC = (char *)malloc(strlen("data") + strlen(DEVICE_ID) + 2);
  PUBLISH_TOPIC = (char *)malloc(strlen("data") + strlen(DEVICE_ID) + 2);

  strcpy(SUBSCRIBE_TOPIC, TOPIC_COMMAND);
  strcat(SUBSCRIBE_TOPIC, "/");
  strcat(SUBSCRIBE_TOPIC, DEVICE_ID);

  strcpy(PUBLISH_TOPIC, "data");
  strcat(PUBLISH_TOPIC, "/");
  strcat(PUBLISH_TOPIC, DEVICE_ID);
}

void mqtt_connect()
{
  set_topics();
  mqttClient.setServer(WiFi.gatewayIP(), MQTT_PORT);
  mqttClient.setCallback(callback);
  // Verbinden mit dem MQTT-Broker
  for (int i = 0; i < wifi_repeat; i++)
  {
    if (mqttClient.connect(DEVICE_ID))
    {
      mqttClient.subscribe(SUBSCRIBE_TOPIC);
      Serial.println("MQTT CONNECTED");
    }
    else
    {
      delay(1000);
    }
  }
  display_connection();
}

void send_mqtt_sensor_data()
{
  if (!bme_sensor.performReading())
  {
    Serial.println("Failed to perform reading!");
    return;
  }

  char json[256];
  JsonDocument sensor_data;
  float temperature = round(bme_sensor.temperature * 10) / 10;
  float humidity = round(bme_sensor.humidity);
  float pressure = bme_sensor.pressure;
  float gas_resistance = bme_sensor.gas_resistance;

  sensor_data["temperature"] = temperature;
  sensor_data["humidity"] = humidity;
  sensor_data["pressure"] = pressure;
  sensor_data["gas_resistance"] = gas_resistance;

  serializeJson(sensor_data, json, sizeof(json));

  if (mqttClient.connected())
  {
    mqttClient.publish(PUBLISH_TOPIC, json);
    Serial.println("\nMQTT SENT:");
  }
  else
    Serial.println("\nNO MQTT SENT:");
  Serial.print(json);
}

/*===BME===*/
void bme_setup()
{
  while (!bme_sensor.begin(I2C_BME_HEX))
  {
    Serial.println("ERROR: SETUP BME NOT FOUND");
    display.home.println("NO SENSOR DATA");
    return;
  }
  bme_sensor.setTemperatureOversampling(BME680_OS_8X);
  bme_sensor.setHumidityOversampling(BME680_OS_2X);
  bme_sensor.setPressureOversampling(BME680_OS_4X);
  bme_sensor.setIIRFilterSize(BME680_FILTER_SIZE_3);
  bme_sensor.setGasHeater(320, 150); // 320°C for 150ms
}

void bme_displaydata()
{
  display_connection();
  if (!bme_sensor.performReading())
  {
    Serial.println("Failed to perform reading!");
    display.home.print("\nNO SENSOR DATA");
    return;
  }

  display.home.printf("Temperature: %.1f C\n", bme_sensor.temperature);
  display.home.printf("Humidity: %.1f%\n", bme_sensor.humidity);
  // Print sensor readings
  Serial.print("Temperature: ");
  Serial.print(bme_sensor.temperature);
  Serial.println(" °C");
  char temp[5];
  // mqttClient.publish(PUBLISH_TOPIC, temp);

  Serial.print("Humidity: ");
  Serial.print(bme_sensor.humidity);
  Serial.println(" %");

  Serial.print("Pressure: ");
  Serial.print(bme_sensor.pressure / 100.0); // Convert Pa to hPa
  Serial.println(" hPa");

  Serial.print("Gas Resistance: ");
  Serial.print(bme_sensor.gas_resistance / 1000.0); // Convert Ohms to kOhms
  Serial.println(" kOhms");
  Serial.println();
}

void i2c_scan(int kanal)
{
  int nDevices = 0;
  byte error;
  for (int i = 0; i < 128; i++)
  {
    if (kanal == 1)
    {
      Wire.beginTransmission(i);
      error = Wire.endTransmission(true);
    }
    else
    {
      i2cScan.beginTransmission(i);
      error = i2cScan.endTransmission(true);
    }
    if (error == 0)
    {
      Serial.print("I2C-Gerät an Adresse 0x");
      if (i < 16)
        Serial.print("0");
      Serial.println(i, HEX);
      nDevices++;
    }
    else
    {
      Serial.print("0x");
      if (i < 16)
        Serial.print("0");
      Serial.print(i, HEX);
      Serial.print(" ");
    }
  }

  if (nDevices == 0)
  {
    Serial.println("Kein I2C-Gerät gefunden\n");
  }
  else
  {
    Serial.println("Ende \n");
  }
  return;
}

void setup()
{
  Serial.begin(9600);
  i2cScan.begin(SDA2, SCL2, 400000);
  display.begin(Mycila::EasyDisplayType::SH1107, 22, 23, 360);

  display.setActive(true);
  display.home.print("Loading...");
  display.display();
  bme_setup();

  // GET WiFi Daten aus EEPROM
  EEPROM.begin(128);
  char eeprom_ssid[MAX_SSID_LENGTH] = {0};
  char eeprom_password[MAX_PASSWORD_LENGTH] = {0};
  EEPROM.get(0, eeprom_ssid);
  EEPROM.get(32, eeprom_password);
  EEPROM.end();
  Serial.print("\nREAD FROM EEPROM");
  for (int i = 0; i < 128; i++)
  {
    byte value = EEPROM.read(i); // Read each byte
    Serial.print(value, HEX);    // Print in hexadecimal format
    Serial.print(" ");
    if ((i + 1) % 16 == 0)
    { // Format: new line every 16 bytes
      Serial.println();
    }
  }
  Serial.print(eeprom_ssid);
  Serial.print(eeprom_password);
  // Daten gefunden
  if (is_valid_string(eeprom_ssid, MAX_SSID_LENGTH) && is_valid_string(eeprom_password, MAX_PASSWORD_LENGTH))
  {
    Serial.println("STRING VALID");
    if (wifi_connect(eeprom_ssid, eeprom_password)) // verbinden mit WLAN
    {
      i2cScan.begin(SDA2, SCL2, 400000);
      mqtt_connect();
    }
    else // die Verbindung is schiefgelaufen
    {
      setup_ap();
    }
  }
  else
  { // keine WLAN-Daten gefunden
    setup_ap();
  }
}
int counter = 0;
void loop()
{
  delay(500);
  Serial.println("LOOP");
  counter++;
  display.display();
  bme_displaydata();
  if (mqttClient.connected())
  {
    send_mqtt_sensor_data();
  }
}