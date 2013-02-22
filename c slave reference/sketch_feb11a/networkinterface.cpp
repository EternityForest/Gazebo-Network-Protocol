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


const unsigned char Gazebo_DeviceUUID[16] = "THISISATESTUUID";

/**A string representing data about the slave that can be requested by the master*/
const char Gazebo_SlaveData[] = "x0,Test Device,1,,3,25000,A basic test device,{}";

/**This must return byte X of the 16 Byte Unique Identifier for this device*/
unsigned char GetByteOfUUID(const unsigned char bytenumber)
{
  return Gazebo_DeviceUUID[bytenumber];
}

//Declare this extern here so the struct can see it
extern unsigned char myvariable;
extern void AddHandler(unsigned char*);
extern unsigned char colors[19];

/**Handle an information broadcast message from the master. Will recieve the entire packet*/
void HandleInformationBroadcast(unsigned char *packet)
{
  if (CheckInformationBroadcastKey("settemp",packet))
  {
    myvariable = packet[IndexOfFirstByteOfDataInInformationBroadcast];
  }
}

extern void DoEEPROMWriting();
/**Handle an information broadcast message from the master*/
void HandleNonvolatileSave()
{
  DoEEPROMWriting();
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
   
   
   //Here we say there is a readable and writable simple parameter called TestVar linked to variable myvariable. The n in riwIn means it can be saved to flash.
  {
    &myvariable,0,0,   1,         1 ,         (FLAG_SIMPLE|FLAG_READ|FLAG_WRITE)
      ,"TestVar,uint8,temp,[[]],riwIn,none,none,none,A test var,{}"
    },
    
    //There is a paraemeter called Add, the varible field is unused as this is an advaced parameter, it is not writeable, and the getter is addhandler.
    //In the string we see it takes two arguments, both uint8 interpreted as number.
     {
      0,AddHandler,0,   1,         1 ,         (FLAG_READ)
      ,"Add,uint8,temp,[[a;uint8;number];[b;uint8;number]],ri,none,none,none,Add two numbers together,{}"
    }
    ,
     
     //There is a simple nested array to be interpreted as RGB that we can only read from, linked to color
     {
    &colors,0000,0000,   18,         1 ,         (FLAG_SIMPLE|FLAG_READ)
      ,"colors,uint8[3][6],RGB,[],ri,none,none,none,A database of RGB values for the rainbow,{}"
    }
  };

  /**This indicates the number of parameters*/
  const unsigned char Gazebo_Parameters_Length = 3;

