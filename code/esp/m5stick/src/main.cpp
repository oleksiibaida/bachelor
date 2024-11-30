#include <params.h>

void wifi_connect();
void m5_setup();
void i2c_scan(int kanal);
void bme_setup();
void bme_printdata();

// wifi
const char *WIFI_SSID = "";
const char *WIFI_PASSWORD = "";
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
  // bme_setup();
  i2cScan.begin(SDA2, SCL2, 400000);
}

void loop()
{
  i2c_scan(1);
  
  // bme_printdata();
  // delay(1000);
}

void wifi_connect()
{
  while (WiFi.status() != WL_CONNECTED)
  {
  }
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
    } else{
      Serial.print("0x");
      if (i < 16)
        Serial.print("0");
      Serial.print(i,HEX);
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