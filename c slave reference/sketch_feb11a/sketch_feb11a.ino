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

#include "protocol.h"
#include "machine.h"
#include "Arduino.h"
#include <EEPROM.h>



/**A variable used in unit tests for testing*/
unsigned char myvariable =  254;

/**The computer connected to device will see this as colors[3][7]*/
unsigned char colors[18] = { 255,0,0,255,127,0,127,127,0,0,255,0,0,0,255,0,255,255};

extern unsigned long LastByteTime;
/**this is some unit tests.
 */

void setup()
{
  char Wave_a_chicken;
  Gazebo_Initialize();

  myvariable = EEPROM.read(17); 
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


//A demo of nonvolatile parameters
void DoEEPROMWriting()
{
  EEPROM.write(17, myvariable);
}




/*A demo of the function call system. This is the getter for the parameter Add(uint8,uint8).
 Demonstrates function calls and runtime error validation.
 
 */

void AddHandler(unsigned char* packet)
{
  unsigned char temp;
  //Test that there is exactly two data bytes supplied.(the first byte is the length of the arguments)
  if (*packet ==2)
  {
    //If there is the correct number of arguments add them and return the answer
    temp = packet[1]+packet[2];
    SendSlaveDataResponse(&temp,1);
  }
  else
  {
    if (*packet>2)
    {
      SendSlaveError(ERROR_TOO_MANY_ARGUMENTS,"");
    }
    else
    {
      SendSlaveError(ERROR_TOO_FEW_ARGUMENTS,"");
    }
  }
}

