/***
 * 
 * 
 * Copyright 2013 Daniel Dunn
 * 
 *  This file is part of the Gazebo Protocol Project.
 * 
 * The Gazebo Protocol Project is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * Gazebo Protocol Project is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU Lesser General Public License
 * along with The Gazebo Protocol Project.  If not, see <http://www.gnu.org/licenses/>.
 * 
 **/

/**
 * @file machine.h
 * @author Daniel Black
 * @date January 2013
 * @license GPLv3
 * 
 * This file must contain all machine specific drivers for the Gazebo Protocol.
 * 
 */

#include "Arduino.h"
#include "protocol.h"
#include "machine.h"
/**Do whatever this platform needs to get set up.*/
long LastByteTime;

/**This is a table of all of the baud rates defined in the specification*/
unsigned long BaudRates[11] = 
{
  100,
  300,
  1200,
  2400,
  4800,
  9600,
  38400,
  57600,
  250000,
  500000,
  1000000
};


extern void setupUUIDIfNotAlreadySetUp();

void Gazebo_Initialize()
{
  Serial.begin(100000);
}





/**
 * BaudRate mst be a index into the Gazebo Baud Rate Table defined in the standard.
 * Must return 1 on sucess and 0 on invalid baud rate.
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
 * Must return the number of milliseconds since the last byte was recieved
 * @return Time since last byte in milliseconds
 */
unsigned short TimeSinceLastByteWasRecieved()
{
  return (millis()-LastByteTime);
}



