#include <M5StickCPlus.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME680.h>
#include <WiFi.h>
#include <bsec.h>
#include <PubSubClient.h>
#include <Adafruit_VCNL4040.h>
#include <ArduinoJson.h>
#include <ESPAsyncWebServer.h>
#include <EEPROM.h>
#define DEVICE_ID "m5bmevcnl"

//I2C
#define SDA2    17
#define SCL2    16
#define I2C_BME_HEX     0x77
#define I2C_TVOC_HEX    0x58
#define I2C_VCNL_HEX    0x60

// M5.Lcd
#define X_OFFSET 10

// M5.Buttons
#define BTN_RESET 32