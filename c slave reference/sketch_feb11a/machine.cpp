/**
@file machine.h
@author Daniel Black
@date January 2013
@license GPLv3

This file must contain all machine specific drivers for the Gazebo Protocol.

*/

#include "Arduino.h"
#include "protocol.h"
#include "machine.h"
/**Do whatever this platform needs to get set up.*/
long LastByteTime;

/**This is a table of all of the baud rates defined in the specification*/
unsigned long BaudRates[10] = 
{
100,
300,
1200,
2400,
4800,
9600,
100000,
250000,
500000,
1000000
};



void Gazebo_Initialize()
{
Serial.begin(100000);
}





/**
BaudRate mst be a index into the Gazebo Baud Rate Table defined in the standard.
Must return 1 on sucess and 0 on invalid baud rate.
*/
unsigned char Gazebo_SetBaudRate(unsigned char BaudRate)
{
Serial.begin(BaudRates[BaudRate]);
}

/**Place a byte into the output buffer however that is implemented on the current platform*/
void BufferedSerialWrite(unsigned char byte)
{

    Serial.write(byte);
}



/**
Must return the number of milliseconds since the last byte was recieved
@return Time since last byte in milliseconds
*/
unsigned short TimeSinceLastByteWasRecieved()
{
  return (millis()-LastByteTime);
}


