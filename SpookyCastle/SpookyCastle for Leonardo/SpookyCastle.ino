
#include "protocol.h"
#include "machine.h"
//All this is for the entropy gathering part
static unsigned char entropypool[200];
static unsigned char indexofhighestonnocupiedbyteinentropypool = 0;
static unsigned char newreading,oldreading;
static unsigned char a,b,c,x;
static unsigned char changes = 0;
unsigned char entropystrength = 200;

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
  HandleEntropyPooling();
}



void PinModeHandler(unsigned char *packet,unsigned char respond)
{ 	
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
    if (respond) SendSlaveError(0,"Mode value out of range");
  }
  else
  {
    if(respond) SendAcknowledgment();
  }
}

void DigitalWriteHandler(unsigned char *packet,unsigned char respond)
{
  
    return;
 	
  packet += 1;//get rid of len field
  
  if (packet[1] == 0)
  {
    digitalWrite(*packet,LOW);

  }

  if (packet[1] == 1)
  {
    digitalWrite(*packet,HIGH);
  }
if (respond)
{
  if (packet[1]>1)
  {
   SendSlaveError(0,"Mode value out of range");
  }
  else
  {
    SendAcknowledgment();
  }
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

void AnalogWriteHandler(unsigned char *packet,unsigned char respond)
{


  packet += 1;
  analogWrite(packet[0],packet[1]);
  
  if (respond)
  {
  SendAcknowledgment();
  }
}

void RavenHandler(unsigned char *packet)
{
  SendSlaveDataResponse((unsigned char*)"Quoth the raven, 'Nevermore.'",29);
}


//Handle a request for random data by sending up to 200 bytes thereof.
void ChaosCauldronHandler(unsigned char *packet)
{
  SendSlaveDataResponse(&entropypool[0], indexofhighestonnocupiedbyteinentropypool);
  indexofhighestonnocupiedbyteinentropypool = 0; //We already set out some entropy, and sending out already sent entropy would be bad
}

//This code reads the ADC value.
uint16_t read_temperature() {
  ADMUX = (1<<REFS1) | (1<<REFS0) | (1<<MUX3);
  // enable conversion
  ADCSRA |= 1<<ADSC;  
  // wait for conversion to finish  
  while (ADCSRA & (1<<ADSC)) {
  };

  uint16_t temperature = ADCL;
  temperature += ADCH<<8;

  return temperature;
}

//Take one temperature sensor reading, and run the whitening algorithm on it.
//If we have accumulated at least one byte's worth of entropy(As determined by how many times the value has changed)
//Add the byte into the entropy pool.
void HandleEntropyPooling()
{

  newreading = read_temperature();


  if (!(newreading == oldreading)) //keep track of how often the readng changes
  {
    changes++;
  }
//This is XABC to whiten the data, even though XABC itself is only about as good as LCG, it should whiten well because of how many cycles we put through it.
  x++;
  a = (a^c^x);
  b = (b+a+newreading);
  c = (c+(b>>1)^a);

  oldreading = newreading; //FIFO the readngs

  //If the input data has changed enough.
  if (changes >entropystrength)
  {

    changes = 0;
    //If there is space for more random bytes than store them
    if(indexofhighestonnocupiedbyteinentropypool<200)
    {
      entropypool[indexofhighestonnocupiedbyteinentropypool] = c;
      indexofhighestonnocupiedbyteinentropypool++;
    }
  }
}


