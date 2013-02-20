/***
 * 
 * 
 * Copyright 2013 Daniel Dunn
 
 *  This file is part of the Gazebo Protocol Project.

    The Gazebo Protocol Project is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Gazebo Protocol Project is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU Lesser General Public License
    along with The Gazebo Protocol Project.  If not, see <http://www.gnu.org/licenses/>.

**/

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


