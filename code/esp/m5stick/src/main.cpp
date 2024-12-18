#include <params.h>
#include <PubSubClient.h>

void wifi_connect();
void m5_setup();
void i2c_scan(int kanal);
void bme_setup();
void bme_printdata();
void mqtt_connect();
void set_subscribe_topic();
void publish_json();
// wifi
const char *WIFI_SSID = "RaspEsp";
const char *WIFI_PASSWORD = "mqtt1234";
// MQTT
const char MQTT_BROKER_ADRRESS[] = "192.168.1.10"; // IP von Raspberry
const int MQTT_PORT = 1883;
const char *CLIENT_ID = "m5";
const char *TOPIC_COMMAND = "command";
char *SUBSCRIBE_TOPIC;
const char *PUBLISH_TOPIC = "status/m5";
const char *TOPIC_TEMP = "status/m5/temp";
const char *TOPIC_HUM = "status/m5/hum";
const char *TOPIC_PRES = "status/m5/pres";
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
// i2c
TwoWire i2cScan = TwoWire(1);
// BME680
Adafruit_BME680 bme_sensor;

void setup()
{
  Serial.begin(115200);
  Serial.println("Starting M5Stick");
  Wire.begin();
  m5_setup();
  wifi_connect();
  mqtt_connect();
  bme_setup();
  i2cScan.begin(SDA2, SCL2, 400000);
}

void loop()
{
  // i2c_scan(1);
  delay(500);
  bme_printdata();
  // delay(1000);
}

void wifi_connect()
{
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
  }
  Serial.println(WiFi.localIP());
  M5.Lcd.print("\nConnected with IP: ");
  M5.Lcd.print(WiFi.localIP());
}

void set_subscribe_topic()
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

void mqtt_connect()
{
  set_subscribe_topic();
  mqttClient.setServer(WiFi.gatewayIP(), MQTT_PORT);
  mqttClient.setCallback(callback);
  // Loop bis verbunden
  while (!mqttClient.connected())
  {
    Serial.print(".");
    if (mqttClient.connect(CLIENT_ID))
    {
      // Serial.println("Verbunden mit dem Broker");
      mqttClient.subscribe(SUBSCRIBE_TOPIC);
      // Serial.print("\nSubscribed: ");
      // Serial.print(SUBSCRIBE_TOPIC);
    }
    else
    {
      delay(1000);
    }
  }
  Serial.println("MQTT CONNECTED");
  M5.Lcd.println("MQTT CONNECTED");
}

void publish_json(float temp, float hum, float pres) {
    char json[64]; // Allocate a buffer for the JSON string
    snprintf(json, sizeof(json), "{\"temperature\":%.1f,\"humidity\":%.2f,\"pressure\":%.2f}", temp, hum, pres);

    // Publish the JSON string via MQTT
    mqttClient.publish(PUBLISH_TOPIC, json);
    Serial.println("\nMQTT SENT:");
    Serial.print(json);
}

void m5_setup()
{
  M5.begin();
  M5.Lcd.setTextColor(TFT_WHITE, TFT_BLACK);
  M5.Lcd.setRotation(1);
  M5.Lcd.setTextSize(2);
  M5.Lcd.setCursor(0, 0);
  M5.Lcd.print("STARTING");
}

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

void bme_printdata()
{
  if (!bme_sensor.performReading())
  {
    Serial.println("Failed to perform reading!");
    return;
  }

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

  publish_json(bme_sensor.temperature, bme_sensor.humidity, bme_sensor.pressure/100);
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