#include <params.h>

// Functions
void m5_setup();
bool wifi_connect(char *ssid, char *password);
void setup_ap();
bool is_valid_string(char *data, int max_length);
void mqtt_connect();
void send_mqtt_data();
void set_topics();
void bme_setup();
void bme_displaydata();
void bme_sendmqtt();
void vcnl_setup();
void vcnl_displaydata();
void vcnl_sendmqtt();
void i2c_scan(int kanal);

// Access Point (AP) konfigurieren
const char AP_SSID[] = "M5Stick";
const char AP_PASSWORD[] = "setupm5stick";
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
const char *CLIENT_ID = "m5";
const char *TOPIC_COMMAND = "command";
char *SUBSCRIBE_TOPIC;
char *PUBLISH_TOPIC;
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
// i2c
TwoWire i2cScan = TwoWire(1);
// BME680
Adafruit_BME680 bme_sensor;
// VCNL4040
Adafruit_VCNL4040 vcnl4040 = Adafruit_VCNL4040();

/*Wird beim Empfang der MQTT-Nachricht aufgerufen*/
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

void setup()
{
  Serial.begin(115200);
  Serial.println("START");
  Wire.begin();
  m5_setup();
  // clear_eeprom();
  //
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
    Serial.println("STRING VALID");
    if (wifi_connect(eeprom_ssid, eeprom_password))
    {
      i2cScan.begin(SDA2, SCL2, 400000);
      mqtt_connect();
    }
    else
    {
      setup_ap();
    }
    vcnl_setup();
    bme_setup();
  }
  else
  { // keine WLAN-DAten gefunden
    setup_ap();
  }
}

void loop()
{
  // i2c_scan(1);

  delay(500);
  Serial.println("LOOP");
  if (WiFi.status() != WL_CONNECTED)
  {
    setup_ap();
    // Reconnect to WiFi with credentials from EEPROM
    EEPROM.begin(128);
    char eeprom_ssid[MAX_SSID_LENGTH] = {0};
    char eeprom_password[MAX_PASSWORD_LENGTH] = {0};
    EEPROM.get(0, eeprom_ssid);
    EEPROM.get(32, eeprom_password);
    EEPROM.end();
    // Daten gefunden
    if (is_valid_string(eeprom_ssid, MAX_SSID_LENGTH) && is_valid_string(eeprom_password, MAX_PASSWORD_LENGTH))
      wifi_connect(eeprom_ssid, eeprom_password);
  }
  else if (!mqttClient.connected())
  {
    mqtt_connect();
  }
  bme_displaydata();
  vcnl_displaydata();
  if (mqttClient.connected())
    send_mqtt_data();
  delay(1000);
}

void m5_setup()
{
  M5.begin();
  delay(100);
  M5.Lcd.setTextColor(TFT_WHITE, TFT_BLACK);
  M5.Lcd.setRotation(1);
  M5.Lcd.setTextSize(2);
  M5.Lcd.setCursor(0, 0);
}

/*===WIFI===*/
bool wifi_connect(char *ssid, char *password)
{
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  for (uint8_t i = 0; i < wifi_repeat; i++)
  {
    if (WiFi.status() == WL_CONNECTED)
    {
      Serial.println(WiFi.localIP());
      M5.Lcd.fillRect(0, 0, M5.Lcd.width(), 20, TFT_BLACK);
      M5.Lcd.setCursor(X_OFFSET, 0);
      M5.Lcd.println("WIFI OK");
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

  M5.Lcd.fillRect(0, 0, M5.Lcd.width(), M5.Lcd.height(), TFT_RED);
  M5.Lcd.setCursor(X_OFFSET, 0);
  M5.Lcd.println("SET UP WIFI ");
  M5.Lcd.setCursor(X_OFFSET, 20);
  M5.Lcd.println("GO TO 10.0.0.1");
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
void mqtt_connect()
{
  set_topics();
  mqttClient.setServer(WiFi.gatewayIP(), MQTT_PORT);
  mqttClient.setCallback(callback);
  // Loop bis verbunden
  while (!mqttClient.connected())
  {
    Serial.print(".");
    M5.Lcd.setCursor(X_OFFSET, 20);
    M5.Lcd.println("CONNECTING MQTT");
    if (mqttClient.connect(CLIENT_ID))
    {
      // Serial.println("Verbunden mit dem Broker");
      mqttClient.subscribe(SUBSCRIBE_TOPIC);
      M5.Lcd.setCursor(X_OFFSET, 20);
      M5.Lcd.fillRect(0, 20, M5.Lcd.width(), 20, TFT_BLACK);
      M5.Lcd.println("MQTT OK");
      Serial.println("MQTT CONNECTED");
      // Serial.print("\nSubscribed: ");
      // Serial.print(SUBSCRIBE_TOPIC);
    }
    else
    {
      delay(1000);
    }
  }
}

void set_topics()
{
  SUBSCRIBE_TOPIC = (char *)malloc(strlen(TOPIC_COMMAND) + strlen(DEVICE_ID) + 2);
  // PUBLISH_TOPIC = (char *)malloc(strlen("data") + strlen(DEVICE_ID) + 2);
  PUBLISH_TOPIC = (char *)malloc(strlen("data") + strlen(DEVICE_ID) + 2);
  if (SUBSCRIBE_TOPIC == NULL)
  {
    // Serial.print("Konnte nicht abonnieren. Default topic");
    // SUBSCRIBE_TOPIC = "command/m5bmevcnl#";
  }
  else
  {
    strcpy(SUBSCRIBE_TOPIC, TOPIC_COMMAND);
    strcat(SUBSCRIBE_TOPIC, "/");
    strcat(SUBSCRIBE_TOPIC, DEVICE_ID);

    strcpy(PUBLISH_TOPIC, "data");
    strcat(PUBLISH_TOPIC, "/");
    strcat(PUBLISH_TOPIC, DEVICE_ID);
  }
}

void send_mqtt_data()
{
  if (!bme_sensor.performReading())
  {
    Serial.println("Failed to perform reading!");
    return;
  }

  char json[256]; // Buffer JSON
  JsonDocument sensor_data;
  // Sensor data
  // BME
  float temperature = round(bme_sensor.temperature * 10) / 10;
  float humidity = round(bme_sensor.humidity);
  float pressure = bme_sensor.pressure;
  float gas_resistance = bme_sensor.gas_resistance;
  // VCNL
  float proximity = vcnl4040.getProximity();
  float ambient = vcnl4040.getLux();
  float white_light = vcnl4040.getWhiteLight();

  sensor_data["temperature"] = temperature;
  sensor_data["humidity"] = humidity;
  sensor_data["pressure"] = pressure;
  sensor_data["gas_resistance"] = gas_resistance;
  sensor_data["proximity"] = proximity;
  sensor_data["ambient"] = ambient;
  sensor_data["white_light"] = white_light;
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
  }
  bme_sensor.setTemperatureOversampling(BME680_OS_8X);
  bme_sensor.setHumidityOversampling(BME680_OS_2X);
  bme_sensor.setPressureOversampling(BME680_OS_4X);
  bme_sensor.setIIRFilterSize(BME680_FILTER_SIZE_3);
  bme_sensor.setGasHeater(320, 150); // 320°C for 150ms
}

void bme_displaydata()
{
  if (!bme_sensor.performReading())
  {
    Serial.println("Failed to perform reading!");
    return;
  }

  M5.Lcd.fillRect(0, 40, M5.Lcd.width(), 20, TFT_BLUE);
  M5.Lcd.setCursor(X_OFFSET, 40);
  M5.Lcd.printf("Temperature %.1f", bme_sensor.temperature);
  /*
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
    */
}

void bme_sendmqtt()
{
  if (!bme_sensor.performReading())
  {
    Serial.println("Failed to perform reading!");
    return;
  }

  char json[128]; // Allocate a buffer for the JSON string
  snprintf(
      json,
      sizeof(json),
      "{\"id\":\"BME\", \"temperature\":%.1f,\"humidity\":%.2f,\"pressure\":%.2f}",
      bme_sensor.temperature, bme_sensor.humidity, bme_sensor.pressure / 100);

  if (mqttClient.connected())
  {
    mqttClient.publish(PUBLISH_TOPIC, json);
    Serial.println("\nMQTT SENT:");
  }
  else
    Serial.println("\nNO MQTT SENT:");
  Serial.print(json);
}

/*===VCNL===*/
void vcnl_setup()
{
  if (!vcnl4040.begin(I2C_VCNL_HEX))
  {
    Serial.println("ERROR: VCNL NOT FOUND");
    M5.Lcd.print("ERROR: VCNL NOT FOUND");
  }
  Serial.println("VCNL FOUND");
  // vcnl4040.setProximityLEDCurrent(VCNL4040_LED_CURRENT_200MA);
  Serial.print("Proximity LED current set to: ");
  switch (vcnl4040.getProximityLEDCurrent())
  {
  case VCNL4040_LED_CURRENT_50MA:
    Serial.println("50 mA");
    break;
  case VCNL4040_LED_CURRENT_75MA:
    Serial.println("75 mA");
    break;
  case VCNL4040_LED_CURRENT_100MA:
    Serial.println("100 mA");
    break;
  case VCNL4040_LED_CURRENT_120MA:
    Serial.println("120 mA");
    break;
  case VCNL4040_LED_CURRENT_140MA:
    Serial.println("140 mA");
    break;
  case VCNL4040_LED_CURRENT_160MA:
    Serial.println("160 mA");
    break;
  case VCNL4040_LED_CURRENT_180MA:
    Serial.println("180 mA");
    break;
  case VCNL4040_LED_CURRENT_200MA:
    Serial.println("200 mA");
    break;
  }

  Serial.print("Proximity LED duty cycle set to: ");
  switch (vcnl4040.getProximityLEDDutyCycle())
  {
  case VCNL4040_LED_DUTY_1_40:
    Serial.println("1/40");
    break;
  case VCNL4040_LED_DUTY_1_80:
    Serial.println("1/80");
    break;
  case VCNL4040_LED_DUTY_1_160:
    Serial.println("1/160");
    break;
  case VCNL4040_LED_DUTY_1_320:
    Serial.println("1/320");
    break;
  }

  // vcnl4040.setAmbientIntegrationTime(VCNL4040_AMBIENT_INTEGRATION_TIME_80MS);
  Serial.print("Ambient light integration time set to: ");
  switch (vcnl4040.getAmbientIntegrationTime())
  {
  case VCNL4040_AMBIENT_INTEGRATION_TIME_80MS:
    Serial.println("80 ms");
    break;
  case VCNL4040_AMBIENT_INTEGRATION_TIME_160MS:
    Serial.println("160 ms");
    break;
  case VCNL4040_AMBIENT_INTEGRATION_TIME_320MS:
    Serial.println("320 ms");
    break;
  case VCNL4040_AMBIENT_INTEGRATION_TIME_640MS:
    Serial.println("640 ms");
    break;
  }

  // vcnl4040.setProximityIntegrationTime(VCNL4040_PROXIMITY_INTEGRATION_TIME_8T);
  Serial.print("Proximity integration time set to: ");
  switch (vcnl4040.getProximityIntegrationTime())
  {
  case VCNL4040_PROXIMITY_INTEGRATION_TIME_1T:
    Serial.println("1T");
    break;
  case VCNL4040_PROXIMITY_INTEGRATION_TIME_1_5T:
    Serial.println("1.5T");
    break;
  case VCNL4040_PROXIMITY_INTEGRATION_TIME_2T:
    Serial.println("2T");
    break;
  case VCNL4040_PROXIMITY_INTEGRATION_TIME_2_5T:
    Serial.println("2.5T");
    break;
  case VCNL4040_PROXIMITY_INTEGRATION_TIME_3T:
    Serial.println("3T");
    break;
  case VCNL4040_PROXIMITY_INTEGRATION_TIME_3_5T:
    Serial.println("3.5T");
    break;
  case VCNL4040_PROXIMITY_INTEGRATION_TIME_4T:
    Serial.println("4T");
    break;
  case VCNL4040_PROXIMITY_INTEGRATION_TIME_8T:
    Serial.println("8T");
    break;
  }

  // vcnl4040.setProximityHighResolution(false);
  Serial.print("Proximity measurement high resolution? ");
  Serial.println(vcnl4040.getProximityHighResolution() ? "True" : "False");

  Serial.println("");
}

void vcnl_displaydata()
{
  uint8_t ambient = vcnl4040.getAmbientLight();
  uint8_t white_light = vcnl4040.getWhiteLight();
  M5.Lcd.fillRect(0, 60, M5.Lcd.width(), 40, TFT_GREEN);
  M5.Lcd.setCursor(X_OFFSET, 60);
  M5.Lcd.printf("Ambient Light %d", ambient);
  M5.Lcd.setCursor(X_OFFSET, 80);
  M5.Lcd.printf("White Light %d", white_light);
}

void vcnl_sendmqtt()
{
  float prox = vcnl4040.getProximity();
  float ambient = vcnl4040.getLux();
  float white_light = vcnl4040.getWhiteLight();
  char json[128]; // Allocate a buffer for the JSON string
  snprintf(json,
           sizeof(json),
           "{\"id\":\"vcnl\",\"proximity\":%.1f,\"ambient\":%.1f,\"white\":%.1f}",
           prox, ambient, white_light);
  if (mqttClient.connected())
  {
    mqttClient.publish(PUBLISH_TOPIC, json);
    Serial.println("\nMQTT SENT:");
  }
  else
    Serial.println("\nNO MQTT SENT:");
  Serial.print(json);
}

/*===SCANNER===*/
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
      // Serial.print("0x");
      // if (i < 16)
      //   Serial.print("0");
      // Serial.print(i,HEX);
      // Serial.print(" ");
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