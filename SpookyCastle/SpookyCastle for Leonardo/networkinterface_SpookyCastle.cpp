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
const char Gazebo_SlaveData[] = "x0,SpookyCastle for Arduino I/O board,1,,8,25000,An I/O board letting the computer control the i/o of the arduino,{}";

/**This must return byte X of the 16 Byte Unique Identifier for this device*/
unsigned char GetByteOfUUID(const unsigned char bytenumber)
{
  return Gazebo_DeviceUUID[bytenumber];
}

//Declare this extern here so the struct can see it
extern void PinModeHandler(unsigned char*,unsigned char);
extern void DigitalWriteHandler(unsigned char*,unsigned char);
extern void DigitalReadHandler(unsigned char *);
extern void AnalogReadHandler(unsigned char *);
extern void AnalogWriteHandler(unsigned char*,unsigned char);
extern void RavenHandler(unsigned char *);
extern void ChaosCauldronHandler(unsigned char*);
extern unsigned char entropystrength;



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
 * flags should be the OR of al that apply of FLAG_READ,FLAG_WRITE,and FLAG_SIMPLE
 * for a simple parameter, set flag simple, and set variable to the address of the variable you want to expose.
 * otherwise you can use the getter and setter. Getter will be passed a pointer to the read argument data prefixed by length
 *setter(uint8 *, uint8) will be passed the data to be written to the parameter prefixed by length, and a second argument that will be 0 if
 * the slave requests no response and 1 otherwise.
 * 
 *the min and max length should both be equalto the fixed len for a simple param(e.g. 4 for a float, 2 for a uint16, etc) but for a getter annd setter param
 *will be used to sanity check any data the master tries to write.
 * 
 *The descriptor is a string as described in the Gazebo Protocol Specfication
 */

const struct Parameter Gazebo_Parameters[]=
{
  /*Variable(or unused),Getter (or unused),Setter(or unused), Length Min, Length Max, Flags
   Descriptor*/

  {
    0,0000,PinModeHandler,   2,         2 ,         (FLAG_WRITE)
      ,"PinMode,uint8;enum{input|input_pullup|output},pinnumber;state,[],ris,none,none,none,Writing a (pinnumber,state) tuple configures a pin to be input or output.,{}"
    }
    ,
  {
    0,0,DigitalWriteHandler,   2,         2 ,         (FLAG_WRITE)
      ,"DigitalWrite,uint8;enum{low;high},pinnumber;value,[],ris,none,none,none,Writing a (pinnumber;value) tuple writes a value to a digital pin.,{}"
    }
    ,

  {
    0,DigitalReadHandler,0,   2,         2 ,         (FLAG_READ)
      ,"DigitalRead,uint8,boolean,[[pin;uint8;pinnumber]],ri,none,none,none,Read the digital state of a pin,{}"
    }
    ,


  {
    0,AnalogReadHandler,0000,   2,         2 ,         (FLAG_READ)
      ,"AnalogRead,uint16,Volts*204.8,[[pin;uint8;pinnumber]],ri,none,none,none,Read the analog voltage of the given analog pin.,{}"
    }
    ,

  {
    0,0000,AnalogWriteHandler,   2,         2 ,         (FLAG_READ)
      ,"AnalogWrite,uint8;uint8,pinnumber;duty*255,[],ris,none,none,none, Writing a (pinnumber;duty) tuple uses ~460Hz PWM to write an analog value to a pin.,{}"
    }
    ,

  {
    0,RavenHandler,0000,   0,         0 ,         (FLAG_READ)
      ,"TheRaven,UTF-8[0:80],GrimUngainlyGhastlyGauntAndOminousBirdOfYore,[],ri,none,none,none,Just an easter egg!,{}"
    }
    ,
  {
    0,ChaosCauldronHandler,0000,   0,         0 ,         (FLAG_READ)
      ,"ChaosCauldron,uint8[0:200],entropy,[],rsb,randomstream,entropy1,ChaosCauldronWhitener,buffer of random data created by whitening the temperature sensor.,{}"
    }
    ,
  {
    &entropystrength,0000,0000,   1,         1 ,         (FLAG_READ|FLAG_WRITE)
      ,"EntropyStrength,uint8,entropy,[],rsb,minchanges,entropy1,ChaosCauldronWhitener,How many times the temperature reading must change per byte of entropy.,{}"
    }
  };

  /**This indicates the number of parameters*/
  const unsigned char Gazebo_Parameters_Length = 8;





