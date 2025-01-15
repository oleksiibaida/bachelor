#ifndef _gp2_1_BASIS_H_
#define _gp2_1_BASIS_H_

#include "Arduino.h"
#include "syncloop.h"

// Information zur Software
#define VERSIONLANG ("Projekt " __FILE__ " erstellt am " __DATE__ " um " __TIME__ " Uhr")

// Hauptschleifenzähler
#define MAX_COUNT 255 // MAX_COUNT = T*16-1 (hier mit T = 16 Sekunden)
#define SEC_COUNT 15  // SEC_COUNT = T*16-1 (hier mit T = 1 Sekunde)

// Eingänge
#define ECHO 2 // Echo-Anschluss des Sensors (externer Interrupt)

// Ausgänge
#define TRIG 4 // Trigger-Anschluss des Sensors

#define PIR 11 // Anschluss Bewegungssensor

#define FLAME 10 // Feuersensor

#define GAS A0 // Gassensor

#define BUZ A3 // Piezo

#define REL 2  // Relais

#define LED_DOOR 12 // Rote Diode

// Keypad
#define R1 9
#define R2 8
#define R3 7
#define R4 6
#define C1 5
#define C2 4
#define C3 3

#endif /* _gp2_1_BASIS_H_ */
