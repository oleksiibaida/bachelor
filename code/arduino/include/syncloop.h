#ifndef SYNCLOOP_H_
#define SYNCLOOP_H_

#include "Arduino.h"

// System-Konstanten
#define SYS_TCMP       15624   //  TCMP = T*F/P-1 = 62,5 ms mit F = 16 MHz und P = 64
#define SYS_SLOTS         16   //  16 Zeitschlitze im Sekundentakt verfügbar
#define SYS_IDLEMAX   0xFFFF   //  Zähler zur Überwachung der Systemlast

// Abgeleitete System-Konstanten
#define SYS_CLKSEM         8   //   Systemtakte pro halbe Sekunde (entspricht SYS_TASKSLOTS/2)
#define SYS_CLKSEC        16   //   Systemtakte pro Sekunde (entspricht SYS_TASKSLOTS)
#define SYS_CLKMIN       960   //   Systemtakte pro Minute (entspricht 60*SYS_CLKMIN)

// Signalisierung-LED (On-Board_LED Pin D13)
#define LEDPIN    13
// Direkter Registerzugriff auf Pin D13 (speziel für Uno / ATmega328P)
// Pin D13 <-> PB5 (On-Board LED) [Bit 5 in den Registern DDRB und PORTB]
#define iniLED PORTB&=0xDF;DDRB|=0x20;PORTB&=0xDF;
#define setLED PORTB|=0x20;
#define clrLED PORTB&=0xDF;

// Definitionen zur Schleifensynchronisation
#define SYNCINIT initTimer1();iniLED;
#define SYNCLOOP if ( syncloop() ) return;

// Prototypen
void initTimer1(void);
boolean syncloop(void);

#endif /* SYNCLOOP_H_ */
