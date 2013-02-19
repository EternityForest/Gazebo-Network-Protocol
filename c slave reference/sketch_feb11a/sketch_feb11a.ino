#include "protocol.h"
#include "machine.h"
#include "Arduino.h"

//this packet requests parameter 1. checksum is wrong
unsigned char testrequestpacket[7] = {0x08,0x00,0x06,0x01,   0x00,  0x00,0x00};
unsigned char testparameterinforequestpacket[7] = {0x06,0x00,0x06,0x01,   0x00,  0x00,0x00};
unsigned char testwritepacket[8] =   {10,0x00,0x06,8,   0x00,0x55,  0x00,0x00};
/**A variable used in unit tests for testing*/
unsigned char myvariable =  254;
extern unsigned long LastByteTime;
/**this is some unit tests.
*/

void setup()
{
  char Wave_a_chicken;
   Gazebo_Initialize();
}

void loop()
{
  if (Serial.available())
  {
  unsigned char x;
  x = Serial.read();
  OnByteRecieved(x);
  LastByteTime = millis();
  }
}


