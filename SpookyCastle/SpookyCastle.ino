
#include "protocol.h"
#include "machine.h"

void setup()
{
  Gazebo_Initialize(); 
}


extern long LastByteTime; //this should stay in machine.h but i hear the interrupt driven serial fails for the leonardo
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


void PinModeHandler(unsigned char *packet)
{
  if (SendErrorIfArgumentStringOutOfBounds(*packet,2,2))
  {
    return;
  }	
  packet += 1;//get rid of length prefix
  if (packet[1] == 0)
  {
    pinMode(*packet,INPUT);

  }

  if (packet[1] == 1)
  {
    pinMode(*packet,OUTPUT);
  }

  if (packet[1] == 2)
  {
    pinMode(*packet,INPUT_PULLUP);
  }

  if (packet[1]>1)
  {
    SendSlaveError(0,"Mode value out of range");
  }
  else
  {
SendAcknowledgment();
  }
}

void DigitalWriteHandler(unsigned char *packet)
{
  if (SendErrorIfArgumentStringOutOfBounds(*packet,2,2))
  {
    return;
  }	
  packet += 1;
  if (packet[1] == 0)
  {
    digitalWrite(*packet,LOW);

  }

  if (packet[1] == 1)
  {
    digitalWrite(*packet,HIGH);
  }

  if (packet[1]>1)
  {
    SendSlaveError(0,"Mode value out of range");
  }
  else
  {
SendAcknowledgment();
  }

}
void DigitalReadHandler(unsigned char *packet)
{
  if( SendErrorIfArgumentStringOutOfBounds(*packet,1,1))
  {
    return;
  }	
  packet += 1;
  unsigned char temp;

    temp = digitalRead(*packet);
    SendSlaveDataResponse(&temp,1);

}

void AnalogReadHandler(unsigned char *packet)
{

  if (SendErrorIfArgumentStringOutOfBounds(*packet,1,1))
  {
    return;
  }	

  packet += 1;
  unsigned char temp;

    temp = analogRead(*packet);
    SendSlaveDataResponse(&temp,2);

}

void AnalogWriteHandler(unsigned char *packet)
{

  if (SendErrorIfArgumentStringOutOfBounds(*packet,2,2))
  {
    return;
  }	

  packet += 1;
  analogWrite(packet[0],packet[1]);
SendAcknowledgment();

}

void RavenHandler(unsigned char *packet)
{
  SendSlaveDataResponse((unsigned char*)"Quoth the raven, 'Nevermore.'",29);
}



