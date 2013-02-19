/**A flag indicating that the parameter is a simple public variable and not a property with getters and setters*/
#define FLAG_SIMPLE 1
/**A flag indicating a parameter can be read from*/
#define FLAG_READ 2
/**A flag indicating a parameter can be written to*/
#define FLAG_WRITE 4

/**The index of the packet type field in a packet array*/
#define TYPE_OFFSET     0
/**The index of the LSB of the address in any packet array*/
#define ADDRESS_OFFSET  1
/**The index of the length byte in the packet array*/
#define LENGTH_OFFSET   3
/**The index of the first data byte in a packet array*/
#define DATA_OFFSET     4

/**The value sent in response to a matching Slave Presence Detect Request*/
#define SLAVE_PRESENCE_CHAR 0
/**The packet type code for a Parameter Read Request Message*/
#define TYPE_PARAMETER_READ 8
/**The packet type code for a Slave Presence Detect Request*/
#define TYPE_SLAVE_PRESENCE_REQUEST_DETECT 0
/**The packet type code for a Slave Exception packet sesnt by the slave*/
#define TYPE_SLAVE_EXCEPTION 5
/**The packet type code for a Slave Parameter Write request packet*/
#define TYPE_PARAMETER_WRITE 10
/**The packet type code for an Adress Set Request*/
#define TYPE_ADRESS_SET 2
/**The packet type code for a Slave Metadata Request Messege*/
#define TYPE_INFORMATION_REQUEST 4
/**The packet type code for a Slave Parameter Information Request*/
#define TYPE_PARAMETER_INFORMATION_REQUEST 6
/**The packet type code for a Group Quit Message*/
#define TYPE_GROUP_QUIT 20
/**The packet type code for a Slave Data Response*/
#define TYPE_SLAVE_DATA_RESPONSE 7
/**The packet type code for an Information Broadcast Message*/
#define TYPE_INFORMATION_BROADCAST 16
/**The error code sent in respose to a write request with too much data*/
#define ERROR_TOO_SMALL_DATA_WRITE 8
/**The error code sent in response to a write with too little data*/
#define ERROR_TOO_LARGE_DATA_WRITE 7
/**The error code sent in response to a request to join a new group when the group list is already full*/
#define ERROR_TOO_MANY_GROUPS 9
/**The error code sent in response to an operation on a nonexistant paramer*/
#define ERROR_NONEXISTANT_PARAMETER 1


/**
The overhead of each packet not including the Preamble.
i.e. the length field value for a packet with an empty
payload
*/
#define PACKET_OVERHEAD 6

/**The preamble used to signal the beginning of a packet*/
#define PACKET_PREAMBLE 0x55

/**The character the slave sends as an acknowledgement*/
#define ACKNOWLEDGE 6

/**Ten milliseconds(The minimum timeout ant any speed) measured in us*/
#define TEN_MILLISECONDS 10000

/**Send the acknowledgement packet*/
#define SendAcknowledgment() BufferedSerialWrite(ACKNOWLEDGE)

/**A struct representing a variable or property exposed to the master*/
struct Parameter
{
    /**A pointer to a function that returns an unsigned char length prefixed array
    Or a pointer to the actual data if it is a simple parameter*/
    void *getter;
    /**A pointer to a function that takes length prefixed arrays and returns 0 on sucess.
    Unused for simple params*/
    void *setter;
    /**The minimum length, or alternately the fixed length for simple parameters*/
    unsigned char minlength;
    /**The maximum length, unused for simple params*/
    unsigned char maxlength;
    /**A set of bitflags defined in the header file. A 1 in the LSB indicates a simple parameter.*/
    unsigned char flags;
    /**A pointer to a parameter descriptor string*/
    char *descriptor;
};

extern const struct Parameter Gazebo_Parameters[];
extern const unsigned char Gazebo_Parameters_Length;
extern const unsigned char Gazebo_DeviceUUID[16];
extern const char Gazebo_SlaveData[];
extern unsigned char Gazebo_SetBaudRate(unsigned char);

void HandleSlavePresenceDetectRequest(unsigned char*);
void HashUpdate(unsigned char);
void SendSlaveError(unsigned char,char*);
void HandleInformationBroadcast(unsigned char*);
void OnByteRecieved(unsigned char);
void baicheva00(unsigned char);

