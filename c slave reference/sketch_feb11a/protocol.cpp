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

/**
@file main.c
@author Daniel Black
*/


#include <stdio.h>
#include <stdlib.h>
#include <stdio.h>
#include "machine.h"
#include "protocol.h"



/**This is a pseudofunction to get byte X of multi-byte variable data
@param x The byte index into data
@param data Any variable
@returns Byte x of data
*/
#define GetByteOf(x,data) (((unsigned char*)&(data))[(x)])
#define HashUpdate(data) baicheva00(data)



/**A variable to hold how many milliseconds it takes to send one byte*/
unsigned short CurrentTimeOut = 10;
/**True if a message is being recieved, False if idle or sending*/
unsigned char RecievingMessage = 0;
/**A pointer into RecieveBuffer that says where to put the next byte we get*/
unsigned char RecievePointer = 0;
/**A buffer for recieveing serial data*/
unsigned char RecieveBuffer[256];
/**The curent state of the CRC computation. Global because of the number of helper functions that mustbe a part of
one CRC calculation*/
unsigned short HashState = 0;

/**A list of addresses where the first element is the device's address and all other
elements are group adresses or zeros*/
unsigned short Adresses[5] = {0,0,0,0,0};
/**True if this packet has been determined to be irrelevant and bytes should be ignored until it's end*/
unsigned char IgnoringThisPacket =0;

static const short crctable[256] = {
    0x0000U,0xC86CU,0x58B4U,0x90D8U,0xB168U,0x7904U,0xE9DCU,0x21B0U,
    0xAABCU,0x62D0U,0xF208U,0x3A64U,0x1BD4U,0xD3B8U,0x4360U,0x8B0CU,
    0x9D14U,0x5578U,0xC5A0U,0x0DCCU,0x2C7CU,0xE410U,0x74C8U,0xBCA4U,
    0x37A8U,0xFFC4U,0x6F1CU,0xA770U,0x86C0U,0x4EACU,0xDE74U,0x1618U,
    0xF244U,0x3A28U,0xAAF0U,0x629CU,0x432CU,0x8B40U,0x1B98U,0xD3F4U,
    0x58F8U,0x9094U,0x004CU,0xC820U,0xE990U,0x21FCU,0xB124U,0x7948U,
    0x6F50U,0xA73CU,0x37E4U,0xFF88U,0xDE38U,0x1654U,0x868CU,0x4EE0U,
    0xC5ECU,0x0D80U,0x9D58U,0x5534U,0x7484U,0xBCE8U,0x2C30U,0xE45CU,
    0x2CE4U,0xE488U,0x7450U,0xBC3CU,0x9D8CU,0x55E0U,0xC538U,0x0D54U,
    0x8658U,0x4E34U,0xDEECU,0x1680U,0x3730U,0xFF5CU,0x6F84U,0xA7E8U,
    0xB1F0U,0x799CU,0xE944U,0x2128U,0x0098U,0xC8F4U,0x582CU,0x9040U,
    0x1B4CU,0xD320U,0x43F8U,0x8B94U,0xAA24U,0x6248U,0xF290U,0x3AFCU,
    0xDEA0U,0x16CCU,0x8614U,0x4E78U,0x6FC8U,0xA7A4U,0x377CU,0xFF10U,
    0x741CU,0xBC70U,0x2CA8U,0xE4C4U,0xC574U,0x0D18U,0x9DC0U,0x55ACU,
    0x43B4U,0x8BD8U,0x1B00U,0xD36CU,0xF2DCU,0x3AB0U,0xAA68U,0x6204U,
    0xE908U,0x2164U,0xB1BCU,0x79D0U,0x5860U,0x900CU,0x00D4U,0xC8B8U,
    0x59C8U,0x91A4U,0x017CU,0xC910U,0xE8A0U,0x20CCU,0xB014U,0x7878U,
    0xF374U,0x3B18U,0xABC0U,0x63ACU,0x421CU,0x8A70U,0x1AA8U,0xD2C4U,
    0xC4DCU,0x0CB0U,0x9C68U,0x5404U,0x75B4U,0xBDD8U,0x2D00U,0xE56CU,
    0x6E60U,0xA60CU,0x36D4U,0xFEB8U,0xDF08U,0x1764U,0x87BCU,0x4FD0U,
    0xAB8CU,0x63E0U,0xF338U,0x3B54U,0x1AE4U,0xD288U,0x4250U,0x8A3CU,
    0x0130U,0xC95CU,0x5984U,0x91E8U,0xB058U,0x7834U,0xE8ECU,0x2080U,
    0x3698U,0xFEF4U,0x6E2CU,0xA640U,0x87F0U,0x4F9CU,0xDF44U,0x1728U,
    0x9C24U,0x5448U,0xC490U,0x0CFCU,0x2D4CU,0xE520U,0x75F8U,0xBD94U,
    0x752CU,0xBD40U,0x2D98U,0xE5F4U,0xC444U,0x0C28U,0x9CF0U,0x549CU,
    0xDF90U,0x17FCU,0x8724U,0x4F48U,0x6EF8U,0xA694U,0x364CU,0xFE20U,
    0xE838U,0x2054U,0xB08CU,0x78E0U,0x5950U,0x913CU,0x01E4U,0xC988U,
    0x4284U,0x8AE8U,0x1A30U,0xD25CU,0xF3ECU,0x3B80U,0xAB58U,0x6334U,
    0x8768U,0x4F04U,0xDFDCU,0x17B0U,0x3600U,0xFE6CU,0x6EB4U,0xA6D8U,
    0x2DD4U,0xE5B8U,0x7560U,0xBD0CU,0x9CBCU,0x54D0U,0xC408U,0x0C64U,
    0x1A7CU,0xD210U,0x42C8U,0x8AA4U,0xAB14U,0x6378U,0xF3A0U,0x3BCCU,
    0xB0C0U,0x78ACU,0xE874U,0x2018U,0x01A8U,0xC9C4U,0x591CU,0x9170U,
    };




/**Get the length of a string.
@param str The string to be measured
@return The length of the string including the null-terminator*/
unsigned char strlenwithnull(const char *str)
{
    unsigned char i;
    for(i=0; i<=255; i++)
    {

        if  (str[i]==0)
        {
            return (i);
        }
    }

}

/**Handle an information broadcast message from the master*/
void HandleInformationBroadcast(unsigned char *packet)
{
printf("information Broadcast has been recieved");
}


/**Send a slave data response packet. You only need to give it the data, it will handle framing.
@param data A pointer to the start of the data to be sent
@data_length The length of the data to be sent
*/
void SendSlaveDataResponse(const unsigned char *data, const unsigned char data_length)
{

    //Initialize the CRC state
    HashState = 0;

    //We hash every byte we send but NOT the preamble because it is
    //not part of the packet data.
    //preamble
    BufferedSerialWrite(PACKET_PREAMBLE);
    //Send the packet type code,
    BufferedSerialWrite(TYPE_SLAVE_DATA_RESPONSE);
    HashUpdate(TYPE_SLAVE_DATA_RESPONSE);
	
    BufferedSerialWrite(0x01);
    HashUpdate(0x01);
	
	
    BufferedSerialWrite(0x00);
    HashUpdate(0x00);

    //Calculate what the length field will be because
    //The length field is not the same as the length of the actual data.
    BufferedSerialWrite(data_length +PACKET_OVERHEAD);
    HashUpdate(data_length+PACKET_OVERHEAD);

    //Send each character of the actual data and hash it
    unsigned char i;
    for(i=0; i<data_length; i++)
    {
        BufferedSerialWrite(data[i]);
        HashUpdate(data[i]);
    }

    BufferedSerialWrite(GetByteOf(1,HashState));
    BufferedSerialWrite(GetByteOf(0,HashState));
}

/**Handle an incoming request from the master to join a group
@param Pointer to the first char in the group join packet to handle
*/
void HandleGroupJoinRequest(unsigned char *packet)
{
    unsigned char i;
    //Check if we are already a member of the group or if that is our native adress(??)
    for(i=0; i<5; i++)
    {
        if(Adresses[i]==  *(unsigned short*)(packet+DATA_OFFSET))
        {
            //Send ACK anyway even if we are already in the group
            BufferedSerialWrite(ACKNOWLEDGE);
            return;
        }
    }

    //Check if we have a free Address slot availible
    //And if so, put the data in there.
    for(i=1; i<5; i++)
    {
        if (Adresses[i] == 0)
        {
            Adresses[i] = *((unsigned short*)(packet+DATA_OFFSET));
            BufferedSerialWrite(ACKNOWLEDGE);
            return;
        }
    }

    //If we have made it this far the request was unseucessful and most likely we could
    //not find a free group slot.
    SendSlaveError(ERROR_TOO_MANY_GROUPS,"");
}

/**Handle an incoming request from the master to guit a group
@param Pointer to the first char in the group quit packet to handle
*/
void HandleGroupQuitRequest(unsigned char *packet)
{
    unsigned char i;

    //Start i at 1 instead of zero because Addresses[0] is
    //Our main address and we don't want to change that except by an
    //Address Set Request
    for(i=1; i<5; i++)
    {
        if(Adresses[i] ==  *(unsigned short*)(packet+DATA_OFFSET))
        {
            //Set the group to zero because we use zero to mean empty.
            Adresses[1] = 0;
        }
    }

    //I can't think of any case where this would fail.
    SendAcknowledgment();
}

/**Given a Parameter Request packet, send the appropriate reponse.
@param packet A pointer to the start of the packet to handle
*/
void HandleParameterRequest(unsigned char *packet)
{
    struct Parameter parameter;
    if (packet[DATA_OFFSET] >= Gazebo_Parameters_Length)
    {
        SendSlaveError(ERROR_NONEXISTANT_PARAMETER,"");
        return;
    }
    parameter = Gazebo_Parameters[packet[DATA_OFFSET]];

    //TODO support advanced propereties
    //If the parameter is a simple fixed length exposed variable
    //Then we just output it

    if (parameter.flags&FLAG_SIMPLE)
    {

        SendSlaveDataResponse((unsigned char*)parameter.getter,parameter.minlength);
    }
}

/**Send a slave error packet
@param error The error code. Error codes are defined in the header file.
@param description Pointer to a null-terminated string of additional data about the error
*/
void SendSlaveError(unsigned char error, char *description)
{
    HashState=0;
    //Send the preamble
    BufferedSerialWrite(0x55);

    BufferedSerialWrite(TYPE_SLAVE_EXCEPTION);
    HashUpdate(TYPE_SLAVE_EXCEPTION);
    //Adress to master
    BufferedSerialWrite(1);
    HashUpdate(1);
    BufferedSerialWrite(0);
    HashUpdate(0);
    BufferedSerialWrite(PACKET_OVERHEAD + 1);
    HashUpdate(PACKET_OVERHEAD+1);
    BufferedSerialWrite(error);
    HashUpdate(error);
    BufferedSerialWrite(GetByteOf(1,HashState));
    BufferedSerialWrite(GetByteOf(0,HashState));
    //
}

/**Given a Parameter Information Request packet, return the appropriate response.
@param packet A pointer to the packet to handle
*/
void HandleParameterInformationRequest(unsigned char *packet)
{
    if (packet[DATA_OFFSET] >= Gazebo_Parameters_Length)
    {

        SendSlaveError(ERROR_NONEXISTANT_PARAMETER,"");
        return;
    }

    //Cast to avoid warnings
    SendSlaveDataResponse((unsigned char*) Gazebo_Parameters[packet[DATA_OFFSET]].descriptor,
                          strlenwithnull(Gazebo_Parameters[packet[DATA_OFFSET]].descriptor));
}
/**Handle a request for slave metadata
@param packet A pointer to th he packet to handle.
*/
void HandleMetaDataRequest(unsigned char *packet)
{
    SendSlaveDataResponse((const unsigned char*)Gazebo_SlaveData,strlenwithnull(Gazebo_SlaveData));
}

/**Handle a command from the master to change this device's temporary address.
@param packet A pointer to the packet to handle.
*/
void HandleSlaveAddressSetCommand(unsigned char *packet)
{
    if (!(packet[LENGTH_OFFSET] == PACKET_OVERHEAD+18))
    {
        SendSlaveError(0,"");
    }

    unsigned char i = 0;
    packet += DATA_OFFSET;
    for (i=0; i<16; i++)
    {
        if(!( packet[i]==Gazebo_DeviceUUID[i]))
        {
            return;
        }
    }

    GetByteOf(0,Adresses[0]) = packet[16];
    GetByteOf(1,Adresses[0]) = packet[17];
    SendAcknowledgment();
}

/**Given a Parameter Write packet, send the appropriate reponse and write the parameter if applicable.
@param packet A pointer to the packet to handle.
*/
void HandleParameterWrite(unsigned char *packet)
{
    struct Parameter parameter;
    unsigned char i = 0;
    unsigned char *temp;
    if (packet[DATA_OFFSET] >= Gazebo_Parameters_Length)
    {
        SendSlaveError(ERROR_NONEXISTANT_PARAMETER,"");
        return;
    }
    parameter = Gazebo_Parameters[packet[DATA_OFFSET]];

    //TODO support advanced propereties
    //If the parameter is a simple fixed length exposed variable
    //Then we just write to it after bounds checking

    //Handle bounds checking
    unsigned char datalen;
    //Get the length of data the packet wants to write by subtracting the overhead,
    //And subtracting one because the first data byte is to select the parameter.
    datalen = (packet[LENGTH_OFFSET] - PACKET_OVERHEAD)-1;
    if (datalen < parameter.minlength)
    {
        SendSlaveError(ERROR_TOO_SMALL_DATA_WRITE,"");
        //Just quit after sending the error
        return;
    }

    if (datalen > parameter.maxlength)
    {
        SendSlaveError(ERROR_TOO_LARGE_DATA_WRITE,"");
        return;
    }


    if (parameter.flags&FLAG_SIMPLE)
    {
        //getter is just a pointer to the variable.
        temp = (unsigned char*)parameter.getter;
        //Plus one because the first data byte is the parameter specifier and not actual data to be
        //written
        packet= packet+DATA_OFFSET+1;
        for(i=0; i<datalen; i++)
        {

            //Set each byte of the simple parameter
            *temp = *packet;
            temp++;
            packet++;
        }

        SendAcknowledgment();
    }
}

/**Check if a packet is adressed to us or if we can ignore it entirely.
@param packet a pointer to the packet to be checked
@return True if the packet is addressed to us, a group we are a member of, or the broadcast address.
*/
unsigned char CheckAddress(unsigned char *packet)
{
    unsigned char i = 0;
    for (i=0; i<5; i++)
    {

        //get a pointer to the first byte of the adress field then cast it to a short pointer
        //and dereference it and compare the result to the current adress being checked against;
        if(Adresses[i]==* (unsigned short*)(packet+ADDRESS_OFFSET))
        {
            return(1);
        }
    }

    //Check for broadcasts
    if (* (short*)(packet+ADDRESS_OFFSET)==0)
    {
        return(1);
    }

    //Return 0 if we got this far with no results
    return(0);
}




/**Given a packet buffer, respond appropriately to a Slave Presence Detect Request.
@param packet A pointer to the packet to handle
*/
void HandleSlavePresenceDetectRequest(unsigned char *packet)
{
    packet = packet + DATA_OFFSET;
    //The format of this is going to be UUID NETID UUIDBITMASK NETIDBITMASK
    unsigned char i = 0;


    for (i=0; i<16; i++)
    {
        //The bitmask comes 18 bytes after the UUID
        //We want to break if the difference is nonzero after being masked
        if(   ((Gazebo_DeviceUUID[i])^(packet[i])) & (packet[i+18]) )
        {
            return;

        }
    }

    i=0;
    if( (GetByteOf(i,Adresses[0])^packet[i+16]) &packet[i+34] )
    {
        return;
    }

    i++;
    if( (GetByteOf(i,Adresses[0])^packet[i+16]) &packet[i+34] )
    {
        return;
    }


    //Same thing but we are casting to short first ad doing the address

    BufferedSerialWrite(SLAVE_PRESENCE_CHAR);
    return;

}



/**Given a packet, route it to the appropriate handler function.
@param packet The packet to be routed
*/
void HandleNewPacket(unsigned char *packet)
{
    //One big switch statement based on the packet type field.
    switch(packet[TYPE_OFFSET])
    {
    case TYPE_PARAMETER_READ:
        HandleParameterRequest(packet);
        break;
    case TYPE_SLAVE_PRESENCE_REQUEST_DETECT:
        HandleSlavePresenceDetectRequest(packet);
        break;
    case TYPE_PARAMETER_WRITE:
        HandleParameterWrite(packet);
        break;
    case TYPE_ADRESS_SET:
        HandleSlaveAddressSetCommand(packet);
        break;
    case TYPE_INFORMATION_REQUEST:
        HandleMetaDataRequest(packet);
        break;
    case TYPE_PARAMETER_INFORMATION_REQUEST:
        HandleParameterInformationRequest(packet);
        break;
    case TYPE_GROUP_QUIT:
        HandleGroupQuitRequest(packet);
        break;
    case TYPE_INFORMATION_BROADCAST:
        HandleInformationBroadcast(packet);
        break;
    }
}


/**Print a null terminated string to the serial port
Hash every character, but do not reset the hash state beforehand.
@param str A null terminated string to be sent.
*/
void PrintNstringAndHash(const unsigned char *str)
{
    unsigned char temp = 00;
    //This is just a counter to make sure we dont loop forever if no NUL is found
    unsigned char SafetyCounter =00;
    while(SafetyCounter<240)
    {
        temp = *str++;

        if (temp)
        {
            HashUpdate(temp);
            BufferedSerialWrite(temp) ;
        }
        else
        {
            break;
        }
        SafetyCounter++;
    }
}

/**This should get called every time a new byte is availible from the UART.
@param byte the new byte that just arrived.
*/
void OnByteRecieved(const unsigned char byte)
{
    //Check the interframe spacing.
    //If it has been more than that time it is either an error or a new packet.
    //also check if we arent recieving a message at all.
    //Either of these conditions indicate that this byte could be the start of a new character.
    if (((TimeSinceLastByteWasRecieved() >= CurrentTimeOut)) | !(RecievingMessage))

    {
        //A byte time of silence or more always delimits packets
        //So reset the recieve pointer to clear any garbage and reset the hash state.
        RecievePointer = 0;
        HashState = 0;


        //Consider this the start of a new packet ONLY if it matches the valid start code
        //And ONLY if the required interframe distance has been met or exceeded.
        //This lets us send one byte messages outside of a full packet
        if (byte == 0x55)
        {
            RecievingMessage = 1;
        }
        else
        {
            //If we don't see the valid start code we stay idle
            RecievingMessage = 0;
        }
        return;
    }

    //Only if a valid start code was detected at the start should we enter the byte in the buffer.
    else
    {
        RecieveBuffer[RecievePointer] = byte;
        RecievePointer++;
        //Update the checksum as we go so we don't have to do one huge batch of calculations
        //At the end, which would suck for realtime performance.

		//Also dont CRC the CRC because that would
		//not make sense unless we did that weird crc(message +crc)=0 thing
		if (!((RecievePointer >= (RecieveBuffer[LENGTH_OFFSET]-1)) &(RecievePointer>LENGTH_OFFSET)))
		{

			HashUpdate(byte);
		}



        //Not only check and see if we have as mny bytes as the length field says,
        //But also check that we even have the length field.
        if ((RecievePointer >= RecieveBuffer[LENGTH_OFFSET]) &(RecievePointer>LENGTH_OFFSET))
        {
            //If we have recieved a complete message, Check the checksum.
            //	DisableReciever(); //We must re enable this to be ready for the next packet.
            RecievingMessage = 0;
            //Do nothing with the packet if we have just been waiting for the end of it.

            if (CheckAddress(RecieveBuffer))
            {
                //Don't do anything with incorrect packets, they are bad.

                if (GetByteOf(0,HashState ) == RecieveBuffer[RecievePointer-1])
                {
					if(GetByteOf(1,HashState) == RecieveBuffer[RecievePointer-2])
					{
                    HandleNewPacket(RecieveBuffer);
					}
                }
            }

        }
    }
}


//Thic is the CRC with polynomial 0xc86c aka Baicheva00 with 0 initial value, no reversing, and no final XOR.
void baicheva00(const unsigned char data)
{


        HashState = crctable[data ^ (unsigned char)(HashState >> 8)] ^ (HashState << 8);

}

