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


const unsigned char Gazebo_DeviceUUID[16] = "gths4vlogfedxtf";

/**A string representing data about the slave that can be requested by the master*/
const char Gazebo_SlaveData[] = "x0,SpookyCastle for Arduino I/O board,1,,6,25000,An I/O board letting the computer control the i/o of the arduino,{}";

/**This must return byte X of the 16 Byte Unique Identifier for this device*/
unsigned char GetByteOfUUID(const unsigned char bytenumber)
{
  return Gazebo_DeviceUUID[bytenumber];
}

//Declare this extern here so the struct can see it
extern void PinModeHandler(unsigned char*);
extern void DigitalWriteHandler(unsigned char*);
extern void DigitalReadHandler(unsigned char *);
extern void AnalogReadHandler(unsigned char *);
extern void AnalogWriteHandler(unsigned char*);
extern void RavenHandler(unsigned char *);

/**Handle an information broadcast message from the master. Will recieve the entire packet*/
void HandleInformationBroadcast(unsigned char *packet)
{

}

extern void DoEEPROMWriting();
/**Handle an nvsave command from the master*/
void HandleNonvolatileSave()
{

}

/**
 * This must be array of structs with all of your parameters.
 * For a simple parameter getter should point to the variable and setter should be null.
 * For an advanced parameter the data of the write request or the get request
 * packet prefixed by the length of the data will be passed as a the first argument to the setter or getter method.
 * the setter must call SendAcknowledgement() on sucess or SendSlaveError(errorcode,string) on failure
 * The getter must call SendSlaveDataResponse(const unsigned char *data, const unsigned char data_length) to return the data or SendSlaveError(errorcode,string) on failure
 * Both of those are defined in protocol.h
 * Length min, and Length max apply to reads and writes both and are inclusive. Flags are defined in the defines."
 * 
 */

const struct Parameter Gazebo_Parameters[]=
{
  /*Variable(or unused),Getter (or unused),Setter(or unused), Length Min, Length Max, Flags
   Descriptor*/

  {
    0,PinModeHandler,0000,   2,         2 ,         (FLAG_READ)
      ,"PinMode,void,void,[[pin;uint8;number];[mode;enum{output|input|input_pullup};mode],ris,none,none,none,Use ~460Hz PWM to write an analog value to a pin.,{}"
    }
    ,
  {
    0,DigitalWriteHandler,0,   1,         1 ,         (FLAG_READ)
      ,"DigitalWrite,void,void,[[pin;uint8;IO pin number];[value;enum{high|low};Output state]],ris,none,none,none,Write a value to a digital pin.,{}"
    }
    ,

  {
    0,DigitalReadHandler,0,   1,         1 ,         (FLAG_READ)
      ,"DigitalRead,uint8,boolean,[[pin;uint8;number]],ri,none,none,none,Read the digital state of a pin,{}"
    }
    ,


  {
    0,AnalogReadHandler,0000,   2,         2 ,         (FLAG_READ)
      ,"AnalogRead,uint16,Volts*204.8,[[pin;uint8;number]],ri,none,none,none,Read the analog voltage of the given analog pin.,{}"
    }
    ,
 
  {
    0,AnalogWriteHandler,0000,   2,         2 ,         (FLAG_READ)
      ,"AnalogWrite,void,void,[[pin;uint8;number];[value;uint8;duty*255]],ris,none,none,none,Use ~460Hz PWM to write an analog value to a pin.,{}"
    }
    ,

  {
    0,RavenHandler,0000,   0,         0 ,         (FLAG_READ)
      ,"TheRaven,UTF-8[0:80],GrimUngainlyGhastlyGauntAndOminousBirdOfYore,[],ri,none,none,none,Just an easter egg!,{}"
    }
  };

  /**This indicates the number of parameters*/
  const unsigned char Gazebo_Parameters_Length = 6;




