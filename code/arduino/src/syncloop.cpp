#include "syncloop.h"

// Signalisierung des Overflow Interrupts von Timer 1
volatile boolean sysint = false;

// Überwachung der Systemlast
unsigned int  idlecnt = 0;
unsigned int  overloadcnt = 0;

// Interrupt Service Routine
ISR(TIMER1_COMPA_vect)
{
  sysint = true;
}

// Initialisierung von Timer 1 (62.5 ms System-Interrupt)
void initTimer1(void)
{
  __asm("CLI");             // Interrupts sperren
  TCCR1A = 0;               // Timer Control Register zurücksetzen
  TCCR1B = 0;               // Timer Control Register zurücksetzen
  TCCR1C = 0;               // Timer Control Register zurücksetzen
  TCNT1 = 0;                // Zählregister zurücksetzen
  OCR1A = SYS_TCMP;         // Vergleichsregister setzen
  TCCR1B |= (1 << WGM12);   // Vergleichsmodus aktivieren
  TCCR1B |= (1 << CS10);    // Prescaler 64 (Bit 10 und ...)
  TCCR1B |= (1 << CS11);    // Prescaler 64 (... Bit 11 setzen)
  TIMSK1 |= (1 << OCIE1A);  // Timer Compare Interrupt aktivieren
  __asm("SEI");             // Interrupts freigeben
}

// Synchronisierungsfunktion
boolean syncloop(void)
{
  static short int cnt = 0;

  // Schleifensynchronisierung
  if ( !sysint )
  {
    if ( idlecnt < SYS_IDLEMAX ) idlecnt++;
    return true;
  }
  sysint = false;

  // Systemtakt (62.5 ms)
  if ( !idlecnt ) overloadcnt++; // Systemüberlast!
  idlecnt = 0;

  // Takt-Zähler
  if ( cnt == SYS_CLKSEM ) clrLED;
  if ( ++cnt >= SYS_CLKSEC ) {cnt = 0; setLED;}

  return false;
}
