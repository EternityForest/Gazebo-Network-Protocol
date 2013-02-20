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

/**The 16 Byte Unique Identifier for this device*/
const unsigned char Gazebo_DeviceUUID[16] = "THISISATESTUUIDN";

/**A string representing data about the slave that can be requested by the master*/
const char Gazebo_SlaveData[] = "Test Device,x0,1,,test,1,25000,A basic test device,{}";


extern unsigned char myvariable;

/**
This must be array of structs with all of your parameters.
For a simple parameter getter should point to the variable and setter should be null.
For an advanced parameter the data of the write request or the get request
packet prefixed by the length of the data will be passed as a the first argument to the setter or getter method.
the setter must return unsigned char 1 on sucess and unsigned char 0 on failure.
The getter must return a length prefixed string to be sent as the response or a null pointer on failure.
Length min, and Length max apply to reads and writes both and are inclusive. Flags are defined in the defines."

*/

const struct Parameter Gazebo_Parameters[]=
{
    /*Getter    ,Setter, Length Min, Length Max, Flags
    Descriptor*/
    {
        &myvariable,00000000,   1,         1 ,         (FLAG_SIMPLE|FLAG_READ|FLAG_WRITE)
        ,"TestVar,uint8,temp,[[]],riwI,none,none,none,a test var,{}"
    }
};

/**This indicates the number of parameters*/
const unsigned char Gazebo_Parameters_Length = 1;
