#include <M5StickCPlus.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME680.h>
#include <WiFi.h>
#include <bsec.h>

//I2C
#define SDA2    17
#define SCL2    16
#define I2C_BME_HEX     0x77
#define I2C_TVOC_HEX    0x58