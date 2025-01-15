
// Include-Dateien
#include "pinout.h"
#include <stdio.h>
#include <Keypad.h>
#include <EEPROM.h>

// MQTT-Topics
#define TOPIC_ALARM "alarm"
#define TOPIC_PIN "pin"

// MQTT-Nachrichten
#define PIN_WRONG "pin_wrong"
#define PIN_CORRECT "pin_correct"
#define PIN_CHANGE_START "pin_change_start"
#define PIN_CHANGE_STOP "pin_change_stop"
#define PIN_CHANGE_SUC "pin_change_suc"
#define FIRE_START "fire_start"
#define FIRE_GO "fire_go"
#define FIRE_STOP "fire_stop"
#define GAS_START "gas_start"
#define GAS_GO "gas_go"
#define GAS_STOP "gas_stop"
#define PIR_MOVE "pir_move"

// Globale Variablen
volatile unsigned long int event = 0;
static const uint16_t gasSens = 300; // Wert ab dem Gas erkannt wird
static const uint16_t pirSens = 500; // Wert ad dem Bewegung erkannt wird
static bool changePas = false;
// Zustandsvariablen
static uint16_t motionDelay = 0;    // in Sekunden
static uint16_t pirDelay = 10;      // Verzögerung von Bewegungsmelder in Sekunden
static uint8_t pirStateNow = LOW;   // PIR Zustand aktualisiert LOW default
static uint8_t pirStateSaved = LOW; // PIR Zustand gespeichert LOW default
static uint8_t flameRead;           // Flame Zustand jetzt
static uint8_t flameState = LOW;    // Flame Zustand gespeichert LOW default
static uint16_t gasRead;            // Gaswerte vom Analogeingang
static uint8_t gasState = LOW;
static bool lock = true;                // Zustands des Schlosses true zu, false auf.
static const uint8_t lockOpen = 2;      // Zeit in Sekunden wie lange das Schloss geoeffnet wird
static uint8_t lockOpenTimeCounter = 0; // Zählt wie lange der Schloss auf ist in Takte (1/16 Sekunde)
static bool alarm_free = false;
// Keypad
static const int8_t pinInputDelay = 5;   // Zeit in Sekunden fuer die Eingabe naechstes Zeichens
static const int8_t pinChangeDelay = 10; // Zeit in Sekunden fuer das Wechseln der PIN
static int8_t pinInputTimeCounter = 0;
static int8_t pinChangeTimeCounter = 0;
static const int passLength = 4;
static bool passCorrect = false;
static bool checkOldPin = false;
static char password[passLength] = {1, 2, 3, 4};
static char passInput[passLength] = {0, 0, 0, 0};

static const uint8_t row_num = 4;
static const uint8_t col_num = 3;

char keys[row_num][col_num] = {
    {'1', '2', '3'},
    {'4', '5', '6'},
    {'7', '8', '9'},
    {'*', '0', '#'}};

// R1-R4 & C1-C3 sind digitale Eingänge am Arduino
byte pin_row[row_num] = {R1, R2, R3, R4};
byte pin_col[col_num] = {C1, C2, C3};

Keypad keypad = Keypad(makeKeymap(keys), pin_row, pin_col, row_num, col_num);

// Interrupt Service Routine
ISR(INT0_vect)
{
  // External Interrupt (INT0) Port PD2 (D2)
  event++;
}

void send_mqtt_message(String topic, String text)
{
  String message = topic + ":" + text;
  // message an ESP senden
  Serial.println(message);
}

void pinEingabe()
{
  // Eingabe eines Zeichens vom Keypad
  char key = keypad.getKey();
  if (key)
  {
    tone(BUZ, 100);
    pinInputTimeCounter = 1;
    switch (key)
    {
    case '#':
      passCorrect = true;                  // wird auf false gesetzt, wenn die eingegebene PIN falsch war
      for (int i = 0; i < passLength; i++) // pruefen, ob alle char in passInput mit password uebereinstimmen
      {
        if (password[i] != passInput[i])
          passCorrect = false;
      }
      if (passCorrect)
      {
        // PIN wechseln
        if (changePas && !checkOldPin)
        {
          checkOldPin = true;
          pinChangeTimeCounter = 1;
          // Serial.print("\nSie haben jetzt ");
          // Serial.print(pinChangeDelay);
          // Serial.print(" Sekunden um Ihre neue PIN einzugeben");
          // Serial.print("\nDie neue PIN muss genau ");
          // Serial.print(passLength);
          // Serial.print(" Zeichen lang sein \nBitte neue PIN eingeben und mit * bestaetigen: ");
          for (int i = 0; i < passLength; i++) // passInput leeren
            passInput[i] = -1;
        }
        // PIN-Aenderung unterbrochen
        else if (changePas && checkOldPin)
        {
          send_mqtt_message(TOPIC_PIN, PIN_CHANGE_STOP);
          // Serial.println("Aenderung der PIN unterbrochen");
          changePas = false;
          checkOldPin = false;
          for (int i = 0; i < passLength; i++) // passInput leeren
            passInput[i] = -1;
        }
        // PIN richtig, Schloss oeffnen
        else
        {
          // Serial.print("\nDas Schloss wird fuer ");
          // Serial.print(lockOpen);
          // Serial.print(" Sekunden geoeffnet \n");
          lock = false; // Schloss oeffnen
          send_mqtt_message(TOPIC_PIN, PIN_CORRECT);
        }
        for (int i = 0; i < passLength; i++) // passInput leeren
          passInput[i] = -1;
      }
      else if (changePas) // die neue PIN wurde mit # bestaetigt ==> ABBRUCH
      {
        // Serial.println("\nPIN-Aenderung unterbrochen \nDie neue PIN muss mit * bestaetigt werden!");
        pinChangeTimeCounter = 0;
        changePas = false;
        checkOldPin = false;
        for (int i = 0; i < passLength; i++)
          passInput[i] = -1; // passInput leeren
      }
      else
      {
        // Serial.println("Falsches PIN! Versuchen Sie es nochmal!");
        send_mqtt_message(TOPIC_PIN, PIN_WRONG);
        changePas = false;
        pinChangeTimeCounter = 0;
        for (int i = 0; i < passLength; i++)
          passInput[i] = -1; // passInput leeren
      }
      break;
    case '*':
      // Pin wechseln
      pinChangeTimeCounter = 1;
      if (!changePas)
      {
        // Serial.print("\nGeben Sie die alte PIN ein und bestaetigen mit # ");
        send_mqtt_message(TOPIC_PIN, PIN_CHANGE_START);
        changePas = true;
      }
      else if (changePas && checkOldPin)
      {
        checkOldPin = false;
        bool inputFull = true;
        for (int i = 0; i < passLength; i++) // Pruefen ob die neue eingegebene PIN genau passLength Zeichen hat
        {
          if (passInput[i] == -1)
          {
            inputFull = false;
            // Serial.print("\nDie neue PIN passt nicht der Anforderungen! \n PIN-Aenderung abgebrochen");
            pinChangeTimeCounter = 0;
            for (int i = 0; i < passLength; i++)
              passInput[i] = -1;
            break;
          }
        }
        if (inputFull)
        {
          // Serial.print("\n Die Neue PIN ist:");
          for (int i = 0; i < passLength; i++)
          {
            // Serial.print(passInput[i]);
            EEPROM.put(i, passInput[i]);  // neue PIN in EEPROM speichern
            password[i] = EEPROM.read(i); // neue PIN aus EEPROM laden
            passInput[i] = -1;
          }
          // Serial.println("In EEPROM gespeichert ");
          send_mqtt_message(TOPIC_PIN, PIN_CHANGE_SUC);
        }
        pinChangeTimeCounter = 0;
        changePas = false;
        checkOldPin = false;
      }
      else
      {
        // Serial.println("\nPIN-Aenderung unterbrochen");
        send_mqtt_message(TOPIC_PIN, PIN_CHANGE_STOP);
        pinChangeTimeCounter = 0;
        changePas = false;
        checkOldPin = false;
        for (int i = 0; i < passLength; i++)
        {
          passInput[i] = -1; // passInput leeren
        }
      }
      break;
    default:
      if (passInput[passLength - 1] != -1) // passInput wird geleert, wenn die letzte Zahl + 1 eingegeben wurde
        for (int i = 0; i < passLength; i++)
          passInput[i] = -1;
      for (int i = 0; i < passLength; i++)
        if (passInput[i] == -1) // neues Key auf freien Platz setzen
        {
          passInput[i] = key;
          break;
        }
      for (int i = 0; i < passLength; i++)
        // Serial.print(passInput[i]);
        break;
    }
    noTone(BUZ);
  }

  if (pinInputTimeCounter != 0)
  {
    pinInputTimeCounter++;
    if (pinInputTimeCounter > pinInputDelay * 16)
    {
      pinInputTimeCounter = 0;
      changePas = false;
      // Serial.print("\npinInput leer");
      for (int i = 0; i < passLength; i++)
        passInput[i] = -1;
    }
  }
  if (pinChangeTimeCounter != 0)
  {
    pinChangeTimeCounter++;
    if (pinChangeTimeCounter > pinChangeDelay * 16) // pinChangeDelay in Sekunden
    {
      pinChangeTimeCounter = 0;
      // Serial.print("PIN Wechsel ABBRUCH");
      changePas = false;
      for (int i = 0; i < passLength; i++)
        passInput[i] = -1;
    }
  }
}

// Magnetschloss
void magnetSchloss()
{
  if (!lock && lockOpenTimeCounter <= lockOpen * 16) // lockOpen in Sekunden
  {
    lockOpenTimeCounter++;
    digitalWrite(REL, HIGH);
  }
  else if (lockOpenTimeCounter > lockOpen * 16)
  {
    lockOpenTimeCounter = 0;
    lock = true;
    digitalWrite(REL, LOW);
  }
}

// Gasmelder
void gasMelder()
{
  gasRead = analogRead(GAS);
  if (gasRead >= gasSens && !gasState)
  {
    // Erste Erkennung des Gases
    gasState = HIGH;
    send_mqtt_message(TOPIC_ALARM, GAS_START);
    alarm_free = true;
    // Serial.println("Gas erkannt!");
  }
  else if (gasState && gasRead < gasSens)
  {
    send_mqtt_message(TOPIC_ALARM, GAS_STOP);
    gasState = LOW;
    // Serial.println("Gas ist weg");
  }
}

// Feuermelder
void feuerMelder()
{
  flameRead = digitalRead(FLAME); // Zustand pruefen
  if (flameRead && !flameState)   // Sensor gibt HIGH aus => Feuer erkannt
  {
    flameState = HIGH;
    send_mqtt_message(TOPIC_ALARM, FIRE_START);
    alarm_free = true;
    // Serial.println("Feuer erkannt!");
  }
  else if (flameState && !flameRead) // kein Feuer mehr erkannt
  {
    flameState = LOW;
    send_mqtt_message(TOPIC_ALARM, FIRE_STOP);
    // Serial.println("Feuer geloescht!");
    noTone(BUZ);
  }
}

// Bewegungsmelder
void bewegungsMelder()
{
  pirStateSaved = pirStateNow;
  pirStateNow = digitalRead(PIR);
  if (!pirStateSaved && pirStateNow) // Erkennung einer Bewegung
  {
    // Serial.println("Bewegung erkannt!");
    send_mqtt_message(TOPIC_ALARM, PIR_MOVE);
    digitalWrite(LED_DOOR, HIGH); // Diode einschalten
    motionDelay = 0;
  }
  else if (pirStateSaved && pirStateNow) // Bewegung geht weiter
  {
    motionDelay = 0;
  }
  else if (pirStateSaved && !pirStateNow) // Bewegung stoppt
  {
    // Serial.println("Bewegung stoppt => Verzoegerung");
    pirStateSaved = pirStateNow;
    motionDelay = 1; // start der Verzoegerung
  }
  // Verzoegerung
  if (motionDelay != 0)
  {
    if (motionDelay <= pirDelay * 16) // pirDelay ist in Sekunden eingegeben
    {
      motionDelay++;
      if (motionDelay % 2 == 0) // Diode blinkt
      {
        digitalWrite(LED_DOOR, HIGH);
      }
      else
      {
        digitalWrite(LED_DOOR, LOW);
      }
    }
    else
    {
      // Serial.println("Verzoegerung stoppt");
      digitalWrite(LED_DOOR, LOW);
      motionDelay = 0;
    }
  }
}

// Alarmton
void alarm(uint8_t count)
{
  if (alarm_free == true)
  {
    if (flameState) // Feuer
    {
      // 1 Mal pro Sekunde MQTT-Nachricht senden
      // if (count == 0)
      //   send_mqtt_message(TOPIC_ALARM, FIRE_GO);
      if (count <= 8)
        tone(BUZ, 500);
      else
        tone(BUZ, 250);
    }

    else if (gasState) // Gas
    {
      // 1 Mal pro Sekunde MQTT-Nachricht senden
      // if (count == 0)
      // {
      //   send_mqtt_message(TOPIC_ALARM, GAS_GO);
      // }

      if (count % 4 == 0 && alarm_free)
        tone(BUZ, 100);
      else
        noTone(BUZ);
    }
    else
    {
      noTone(BUZ);
    }
  }
  else
  {
    noTone(BUZ);
  }
}

void readSerialData()
{
  if (Serial.available() > 0)
  {
    String readString = Serial.readStringUntil("\n");
    readString.trim();
    if (readString == "alarm_off")
    {
      alarm_free = false;
      noTone(BUZ);
    }
  }
}



// Initialisierung
void setup()
{
  SYNCINIT; // Initialisierung der Interrupt-Synchronisation
  // Interrupt für steigende und fallende Flanke konfigurieren
  // ISC01  ISC00     -> 01
  //     0      0     -> low level
  //     0      1     -> logical change
  //     1      0     -> falling edge
  //     1      1     -> rising edge
  // EICRA |= (1 << ISC01);
  EICRA &= ~(1 << ISC01);
  EICRA |= (1 << ISC00);
  // EICRA &= ~(1 << ISC00);
  EIMSK |= (1 << INT0);  // External Interrupt 0 (INT0) aktivieren
  __asm("SEI");          // Interrupts freigeben
  pinMode(ECHO, INPUT);  // Echo-Signal / Externer Interrupt
  pinMode(TRIG, OUTPUT); // Trigger-Signal für Sensor
  digitalWrite(TRIG, LOW);
  Serial.begin(9600); // Serielle Schnittstelle initialisieren
  // Serial.println(VERSIONLANG);

  // MEINE UNTEN
  char readPass[passLength];
  // Serial.print("ReadPass: ");
  for (int i = 0; i < passLength; i++) // passwort aus EEPROM ablesen
  {
    if (EEPROM.read(i) == NULL) // kein sinvoller Passwort in EEPROM gespeichert
    {
      for (int i = 0; i < passLength; i++)
      {
        readPass[i] = -1;
      }
      break;
    }
    else
    {
      readPass[i] = EEPROM.read(i);
      // Serial.print(readPass[i]);
    }
  }

  // abgelesene PIN in password speichern
  // dabei pruefen, ob  es sinnvoller Wert hat
  for (int i = 0; i < passLength; i++)
  {
    if (readPass[i] != -1)
    {
      password[i] = readPass[i];
    }
    else
    {
      for (int i = 0; i < passLength; i++)
        password[i] = i + 1; // Default PIN ist 1234 fuer passLength 4
      break;
    }
  }
  // Serial.print("PIN: ");
  for (int i = 0; i < passLength; i++)
  {
    // Serial.print(password[i]);
  }
  pinMode(PIR, INPUT);
  pinMode(FLAME, INPUT);
  pinMode(GAS, INPUT);
  pinMode(BUZ, OUTPUT);
  pinMode(REL, OUTPUT);
  pinMode(LED_DOOR, OUTPUT);
}

// Hauptschleife
void loop()
{
  // Serial.print(PIR);
  static uint8_t count = 0;
  static uint64_t seconds = 0;
  // Dieser Teil der Hauptscheife läuft unsynchronisiert

  SYNCLOOP;
  // Interrupt-Synchronisation der Hauptschleife
  // Dieser Teil der Hauptschleife startet alle 62,5 ms

  readSerialData();
  pinEingabe();
  magnetSchloss();
  gasMelder();
  feuerMelder();
  bewegungsMelder();
  alarm(count);

  // Schleifenzähler erhöhen (zählt von 0 bis 15 und wird dann wieder auf 0 gesetzt)
  if (++count > SEC_COUNT)
  {
    count = 0;
    seconds++;
  }
}