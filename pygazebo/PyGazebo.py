# Copyright 2013 Daniel Dunn

# This file is part of the Gazebo Protocol Project.

# The Gazebo Protocol Project is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Gazebo Protocol Project is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU Lesser General Public License
# along with The Gazebo Protocol Project.  If not, see <http://www.gnu.org/licenses/>.


import time
import struct
import base64
import crcmod
import threading
import queue
import serial
import collections

GAZEBO_SHORT_PACKETS = bytes([0x01,0x06] + list(range(0x30,0x46))) # ASCII 0 through F plus ACK and 1
PACKET_TYPE_READ = 0x08
DATA_START_INDEX = 5
MINIMUM_NORMAL_GAZEBO_ADDRESS =4097

PACKET_TYPE_ADDRESS_SET = 2
PACKET_TYPE_PARAMETER_INFO_REQUEST = 6
PACKET_TYPE_SLAVE_DATA_REQUEST = 4
PACKET_TYPE_SLAVE_PRESENCE_DETECT_REQUEST = 0
PACKET_TYPE_PARAMETER_READ = 8
PACKET_TYPE_SLAVE_ERROR = 5
PACKET_TYPE_WRITE = 10

PARAMETER_DESCRIPTOR_NAME_INDEX = 0
PARAMETER_DESCRIPTOR_TYPE_INDEX = 1
PARAMETER_DESCRIPTOR_INTERPETATION_INDEX = 2
PARAMETER_DESCRIPTOR_ARGUMENTS_INDEX = 3
PARAMETER_DESCRIPTOR_FLAGS_INDEX = 4
PARAMETER_DESCRIPTOR_GROUP_CLASS_INDEX = 7
PARAMETER_DESCRIPTOR_GROUP_ROLE_INDEX = 5
PARAMETER_DESCRIPTOR_GROUP_NAME_INDEX = 6
PARAMETER_DESCRIPTOR_DESCRIPTION_INDEX = 8

SLAVE_DESCRIPTOR_TOTAL_PARAMETERS_INDEX = 5


#Set up the CRC calc used to check the validity of Gazebo packets. [Baicheva00],0 initial, no bitreversal, 0 xor
def CRC16(data):
   """Take a CRC of the input bytes or bytearray and return it as a bytes object"""
   c=crcmod.Crc(0x1c86c, rev = False, xorOut = 0, initCrc = 0)
   c.update(data)
   return c.digest()
   
def GazeboArgumentsStringToListOfNamedTuples(gstring):
    """Convert a gazebo argument string to a list of (name,type,interpretation) tuples.
     Will not actually validate the string, hopefully the device supplies a correct one"""
    GazeboReadArgument = collections.namedtuple('GazeboReadArgument',['name','type','interpretation'])
    s = gstring.split(';')
    if (len(s)==1):
       return []
    #[[a;b;c];[a;b;c]]
    #Check to make sure that it can be evenly divided into n name,type,interpretation tuples, or has no semicolons at all indicating maybe
    #there are no arguments
    if not ( (len(s) % 3) == 0):
        raise ValueError('Does not appear to be a valid Gazebo Arguments List')
    v = []
    for i in range(0,len(s),3):
        g = GazeboReadArgument(s[i],s[i+1],s[i+2])
        v.append(g.replace('[','').replace(']',''))
    return v
        
    


class GazeboPacket():
    """class representing a raw arbitrary gazebo packet. 
    You can add datato data address and type or
    you can use parsebytes to add bytes and read out the data
    from the variables when you are finished.

    use toBytes and the NetworkRequest class to actually send the data.
    """
    
    def __init__(self):
        """Create a new GazeboPacket"""
        self._internalbuffer = bytearray([])

    
    def ParseBytes(self,bytes):
        """Attempt to decode a stream of bytes into a packet. 
        returns 1 on sucess, 0 on still need more data, 
        and -1 on known bad data."""
        
        #add our new bytes to the internal buffer
        self._internalbuffer.extend(bytes)
        
        #if we have at least one byte check if its a short packet code
        if len(self._internalbuffer) > 0:
            if self._internalbuffer[0] in GAZEBO_SHORT_PACKETS:
                if len(self._internalbuffer) == 1:
                    self.type = "SHORT"
                    self.address = "SHORT"
                    if self._internalbuffer[0] == 0x30:
                        self.data = False
                    if self._internalbuffer[0] == 0x31:
                        self.data = True
                    if self._internalbuffer[0] == 0x06:
                        self.data = 'ACK'
                    return 1
                    
        #if we have at least the minimum data any packet can have.
        if len(self._internalbuffer) > 6:
            #Look up the length the packet says it has and see if we have that many bytes
            if len(self._internalbuffer) > self._internalbuffer[4]:
                #Calculate a CRC of the whole packet less the  reamble and crc
                #and check if it matches the packet's crc which is the last two bytes.
                if CRC16(self._internalbuffer[1:-2]) == self._internalbuffer[-2:]:
                    self.address = struct.unpack("<H",self._internalbuffer[2:4])[0]
                    self.type = struct.unpack("<B",self._internalbuffer[1:2])[0]
                    self.data = self._internalbuffer[DATA_START_INDEX:-2]#We dont want the last 2 bytes those are crc
                    return 1
                else:
                    return -1
        
        return 0 #Nothing has happened yt we need more data
        
    def toBytes(self):
        """translate to the actual byte array suitable for transmission over the network."""

        r = bytearray([0x55])
        r.extend(struct.pack("<B",self.type))
        r.extend(struct.pack("<H",self.address))
        r.extend(struct.pack("<B",0)) #Placeholder for the length
        r.extend(self.data)
        r[4]= (len(r)+1) #Set the length. 
                         #We add one because in the specification the length field does not include 
                         #the preamble but includes all the other header stuff. so normall we would subtract one but we add two bytes it doesn't
                        #know about so we add one
        r.extend(CRC16(r[1:]))
        return r

class Gazebo_Slave(object):
    """Class representing one gazebo slave. When you initialize it with a manager, UUID, and address, it will automatically figure the rest out."""
    def __init__(self, manager ,UUID,address):
    
        self.id = UUID
        self.address = address
        self.params = {}
        self.manager = manager
        g = GazeboPacket()
        
        SlaveDescriptor = ''
        for i in range(0,255):
            g.address = self.address
            g.type = PACKET_TYPE_SLAVE_DATA_REQUEST
            g.data = bytearray([i])
            b = g.toBytes()
            n = NetworkRequest(self.manager)
            n.data = b
            n.expect = 'gazebopacket'
            n.Send()
            
            #Remove bytes after the null and don't include the null because python doesn't use null termination
            dat = bytearray([])
            
            for j in n.returndata:
                if not j == 0:
                    dat.append(j)
                else:
                    break
            
            SlaveDescriptor = SlaveDescriptor + dat.decode('utf-8')
            
            if 0x00 in n.returndata:
                break #The page with the nul is the last page
        
        sd = SlaveDescriptor.split(',')
        
        #For each parameter the slave says it has, ask about it nd create the appropriate object
        for i in range(int(sd[SLAVE_DESCRIPTOR_TOTAL_PARAMETERS_INDEX])):
            n = NetworkParameter()
            n.parentslave = self
            n.paramnumber = i
            g = GazeboPacket()
            g.type = PACKET_TYPE_PARAMETER_INFO_REQUEST
            g.address = self.address
            g.data = struct.pack("<B",i)
            b = g.toBytes()
            r = NetworkRequest(self.manager)
            r.data = b; r.expect = 'gazebopacket'
            r.Send()
            
            pd = r.returndata.decode("utf-8")
            pd = pd.split(',')
            
            n.flags = pd[PARAMETER_DESCRIPTOR_FLAGS_INDEX]
            n.type = pd[PARAMETER_DESCRIPTOR_TYPE_INDEX]
            n.interpretation = pd[PARAMETER_DESCRIPTOR_INTERPETATION_INDEX]
            n.grouprole = pd[PARAMETER_DESCRIPTOR_GROUP_ROLE_INDEX]
            n.groupname = pd[PARAMETER_DESCRIPTOR_GROUP_NAME_INDEX]
            n.groupclass = pd[PARAMETER_DESCRIPTOR_GROUP_CLASS_INDEX]
            n.arguments = GazeboArgumentsStringToListOfNamedTuples(pd[PARAMETER_DESCRIPTOR_ARGUMENTS_INDEX])
            
            n._datainterpreter = GazeboDataFormatConverter(n.type)
            n._argumentconverters = []
            
            #Pre-Intitialize a list of argument converters because it takes time to parse
            #One for each argument required when reading from this parameter
            for j in n.arguments:
                n._argumentconverters.append(GazeboDataFormatConverter(j.type))
                
            self.params[pd[PARAMETER_DESCRIPTOR_NAME_INDEX]] = n

class NetworkManager(object):
    """Manage the serial port, enumeration of slaves, and discovery of resources. also manage
    request queuein and resource sharing between threads"""
    
    def __init__(self,comport):
        self.comport = serial.Serial(comport)
        self.requestqueue = queue.Queue()
        self.slaves = {}
        self.highestunusedaddress = 5000 #Because of reserved area
        t = threading.Thread(target = self._HandleRequestQueue)
        t.start()

    def __del__(self):
        self.comport.close()

    def close(self):
        """Close the underlying comport"""
        self.comport.close()
        
    #This goes and loops in its own thread and waits for new data to come into the request queue
    def _HandleRequestQueue(self):
        while self:
            thisrequest = self.requestqueue.get()
            self.comport.write(thisrequest.data)
            
            #Try to understand what the request object expects to recieve
            if isinstance(thisrequest.expect,list):
                if thisrequest.expect[0] == 'time':
                    #handle the case where expect reads as many bytes are availible 
                    self.comport.timeout = thisrequest.expect[1]
                    thisrequest.returndata = self.comport.read(10000)
                    #let anything waiting for this unblock.
                    thisrequest.LockedWhileNotCompleted.set()

                
            if thisrequest.expect == 'gazebopacket':
                start = time.time()
                f = GazeboPacket()
                
                #Don't sit there waiting for data for more than 5 seconds.
                self.comport.timeout = 5
                while(time.time()-start)<5:
                    #Check if a complete packet has been recieved
                    t = f.ParseBytes(self.comport.read())
                    if not t == 0:
                        #Break if a complete packet is here or if a known bad packet is here
                        break;
                     
                #If no packet or a known bad packet
                if t == -1 or t == 0:
                    thisrequest.returndata = None
                    thisrequest.LockedWhileNotCompleted.set()
                #If a correct gazebo packet is here
                if t == 1:
                    thisrequest.returndata = f.data
                    thisrequest.fullpacket = f
                    thisrequest.LockedWhileNotCompleted.set()
                    
                    
    
    def EnumerateSlaves(self):
        """Populate the list of slaves."""
        
        
        #Keep discovering slaves until there is none and the loop breaks
        for i in range(self.highestunusedaddress,6000):
            UUID = bytearray(16)
            #We are going to try searching for slaves that match a UUID. 
            #We start by only requiring the first n bits to match, increasing n until there are no matching slaves
            #We then changed the bt that caused there to be no matched to a one and continue. This implements a binary searched
            #And gets either garbage or the address of a slave. If it is garbage we assume we have found all slaves.
            for position in range(1,129): 
                if not self.DetectSlavePresence(UUID, position,'unassigned'):
                   #Get the byte from the bit number. add 2^bit to it to change relevant bit to a 1. minus 1 because 0 means no requred match to the
                   #detect function
                    UUID[ int((position-1)/8) ] += pow(2,((position-1)%8))
                    #We only check the zero case because we don't want to make two requests.
                    #If there is no slave at all there we will stll get an id
                    #But lets check that later
            #Check for garbage IDs
            if self.DetectSlavePresence(UUID):
                
                
                #Give the slave a network address
                g = GazeboPacket()
                g.data = UUID + bytearray(struct.pack("<H",i))
                g.type = PACKET_TYPE_ADDRESS_SET
                g.address = 0
                b = g.toBytes()
                n = NetworkRequest(self)
                n.data = b
                n.expect = ['time',0.050]
                if n.Send() == b'\x06': #If the slave address set works, actually make the object
                    p = Gazebo_Slave(self,UUID,i)
                    #Remove paddng because UUDS are of known length always
                    self.slaves[base64.b64encode(UUID)[:16].decode()] = p #Add the slave to the paramdict
            else:
                self.highestunusedaddress = i+1
                break
                
    
    
    def DetectSlavePresence(self,UUID,matchlength = 128,connected = 'unassigned'):
    
        mask = bytearray(16)
        #Create an array of N 0ne bits followed by 128-N Zero bits
        for i in range(matchlength):
            mask[ int((i)/8)] += pow(2,i%8)
        #Append two zeros for the address requirement then append the bitmask we just made
        Data = UUID + bytearray(2) + mask

        if connected == 'unassigned':
            #If we are only looking for slaves with no network address, assign all of the bit to required in the
            #network address field
           Data+=bytearray([255,255])
        else:
            Data+=bytearray(2)
        
        g = GazeboPacket()
        g.data = Data
        g.type = PACKET_TYPE_SLAVE_PRESENCE_DETECT_REQUEST
        g.address = 0
        n = NetworkRequest(self)
        n.data = g.toBytes()
        #We are not expecting a packet in return. We are expectng garbage as many nodes send thier responses.
        #All we want to know is if at least one device responded. So we listen for 50ms.
        n.expect = ['time',0.050]
        n.Send()
        if len(n.returndata) >0:
            return True
        else:
            return False
            
        
        
        
    def SendInformationBroadcast(self,key,data):
                pass
    
    def SendTimeInfo(self):
       
                pass
                    

#A simple class encapsulating an arbitrary request of the network, in terms of data to be sent
#And data to be expected. manager must be a SerialManager or derivative.
#data must be a byte array. expect can be GazeboPacket, ["time", NumberOfSeconds], or ['len', BytesExpected]
#This can be sent multiple times and each time the 
class NetworkRequest(object):
    """A class encapsulatng one request that may expect a response. Does not need to be a Gazebo packet.
      when Send is called, the data in self.data will be sent using the selected network manager.
      if expect is 'gazebopacket', the data from the response wil be found in self.returndata
      The entire gazebo packet object will be found in fullpacket. """
    def __init__(self,manager, data = None, expect = ["time",1]):
        self.manager = manager
        self.data = data
        self.expect = expect
        self.LockedWhileNotCompleted = threading.Event()
        
        
    def Send(self,priority ="7",block = True):
        self.manager.requestqueue.put(self)
        self.LockedWhileNotCompleted.clear()
        if block:
            #wait for the request to complete
            self.LockedWhileNotCompleted.wait()
            return self.returndata
        
        return None
        

class NetworkParameter(object):
    """A class representing one parameter of a slave device. Contains a reference to its parent slave."""
    

    def __init__(self):
      self.LastUpdated = 0
      self.expires =0.1 #Default to read-idempotent parameters being cached for a tenth of a second
      
    def Read(self, *args):
        """Returns the value of the parameter. Will use the cached value if possible."""
        
        #Check if we can avoid making the request by just returning the cached value.
        if not self._fresh():
            g = GazeboPacket()
            g.data = struct.pack("<B",self.paramnumber)
            j = 0
            for i in args:
                #Convert all of the arguments using the list of argument converters that the parameter
                #instance has
                g.data.append(self._argumentconverters[j].PythonDataToGazebo(i))
                j = j + 1
                
            g.address = self.parentslave.address
            g.type = PACKET_TYPE_PARAMETER_READ
            d = g.toBytes()
            #Make a new network request and send it
            r = NetworkRequest(self.parentslave.manager, d, "gazebopacket")
            temp = r.Send()
            
            
            if r.fullpacket.type == 5:
                raise ValueError('Slave says something went wrong, errordata:' + str(r.returndata))
                
            #If we got a valid value back
            if (not (temp == None)):
                temp = self._datainterpreter.GazeboToPython(temp)
                self.CachedValue = temp
                self.LastUpdated = time.time()
                return temp
            else:
                return None
        #If the cached value was fresh
        else:
            return CachedValue
            
    def Write(self,*data):
        """Write data to a parameter. Data must be of a format that is compatibe with the devices expected type."""
        
        #Translate the input data to gazebo's format, prepend the parameter number
        temp = self._datainterpreter.PythonToGazebo(data)
        data = bytearray(struct.pack('<B',self.paramnumber))
        data.extend(temp)
        
        
        g = GazeboPacket()
        g.data = data
        g.address = self.parentslave.address
        g.type = PACKET_TYPE_WRITE
        b = g.toBytes()
        n = NetworkRequest(self.parentslave.manager)
        n.data = b
        n.expect = 'gazebopacket'
        #[]todo handle slave exceptions
        #Look for an acknowlegdement
        if n.Send() =='ACK':
            return True
        else:
            return False
    
    def _fresh(self):
        """Internal function used to determine if the cached value is still good."""
        #Not-Idempotent values are not cacheable
        if not 'i' in self.flags:
            return False
        
        #If the variable has already expired
        if (time.time() - self.LastUpdated) > self.expires:
            return False
            
        #Early return pattern
        return true
        
    def info(self):
    #Make a human readable report of this parameter
        string = "<"
        if 'r' in self.flags and "w" in self.flags:
            string+= 'Readable and writable parameter '
        elif 'r' in self.flags:
            string += 'Readable parameter '
        elif 'w' in self.flags:
            string += 'Writable parameter '
            
        string += 'of type ' + self.type
        string += ' to be interpreted as ' + self.interpretation
        string += '\n' +  'This parameter plays role ' + self.grouprole + ' in group ' + self.groupname + ' of type ' + self.groupclass + "\n"
        if len(self.arguments) == 0:
            string += 'No arguments are required when reading from this parameter\n'
        if 's' in self.flags:
            string += 'Reads have side effects.\n'
        if 'S' in self.flags:
            string += 'Writes have side effects.\n'
        if 'i' in self.flags:
            string += 'Reads are idempotent(two succesive reads will produce the same data absent external changes).\n'
        if 'I' in self.flags:
            string += 'Writes are idempotent(writing the same data twite is equivalent to once)\n'
        if 'b' in self.flags:
            string += 'This is an item-wise FIFO. Reads will return the oldest N items and likewise for writes\n'
        if 'B' in self.flags:
            string += 'This is a message-wise FIFO. Reads will return the one(1) oldest item.\n'
        if 'n' in self.flags:
            string += 'This parameter can be saved to nonvolatile memory.\n'
        if '!' in self.flags:
            string += 'CAUTION!! ATCHUNG!! USE CARE WHEN MESSING WITH THIS PARAMETER. THE DEVICE HAS MARKED IT AS CRITICAL.\n'
            
        print(string)
        
        

#Interpret a byte array according to a native Gazebo format string.
#Output is in native python types and arrays are converted to lists.
#For example, uint8[3][0:15] will return a list of up to 15 3-integer lists.
def InterpretByteArrayAccordingToGazeboFormatString(ByteArray,Gazebo_DataType):
        """Take a byte array and a standard gazebo type string as found in a resorce descriptor and convert it to a native python representation"""

        #This basically works by tokenizing the gazebo datatype string, applying
        #a series of transformations, and then finallly parsing it.
        
        #we want an array where the fisrt elment is the base type
        #The second element is how many base types make up an innermost array
        #The second is how many innermot arrays make up a second level array, and so on.
        
        Type_as_list = Gazebo_DataType.split('[')
        
        
        #Convert the base type to a python struct format string
        BaseTypeLen = GazeboTypes[Type_as_list[0]]    ['length']
        Type_as_list[0] = GazeboTypes[Type_as_list[0]]['pythonformat']
        
        
        i2 = [Type_as_list[0]]
        #Get rid of all the closing brackets
        for i in Type_as_list[1:]:
            i2.append( i.replace(']',''))
        #Hack because I don't think we can change the iterable while iterating
        Type_as_list = i2
        
            

        #We want to make the last one a list [min,max] if it is a range.
        #dont split if there is no colon
        if ':' in Type_as_list[len(Type_as_list)-1]:
            Type_as_list[len(Type_as_list)-1] = Type_as_list[len(Type_as_list)-1].split(':')
        
        
        #Check if the length of the byte array is an even multiple of the base type
        #Otherwise we have bytes that don't go anywhere and that is an error.
        if not len(ByteArray) % BaseTypeLen == 0:
            return None
        
        #Unpack the input byte array into a list of whatever the base type is
        temp = []
        
        for i in range(0,len(ByteArray),struct.calcsize(Type_as_list[0])):
            temp.append(struct.unpack(Type_as_list[0],ByteArray[i:i+struct.calcsize(Type_as_list[0])])[0])
        
        #Iterate over all of the nesting levels starting at the smallest and going towards the outermost
        
        for i in Type_as_list[1:]:
        
            #if this level of nesting is variable size check for size in range.
            if isinstance(i, list):
                if (len(temp)> int(i[0])) and (len(temp)<int(i[1])):
                    #Variable elements can only be the last element in the nesting
                    return temp
            #If this nesting level is fixed size
            else:
                #check for things that are not multiples of the size we want
                if len(temp) % int(i)==0:
                    ##Package what we have so far into i equal size units
                    temp2=[]
                    for j in range(0,len(temp),int(i)):
                        temp2.append(temp[j:j+int(i)])
                    return temp2
                #When we cannot resolve how to unpack
                else:
                    #This is for when you are having a bad problem and will not go to space
                    return None
        #return the native python representation of the gazebo byte array
        return temp


        
class GazeboDataFormatConverter():
    """Class that converts to and from raw gazebo bytestring data
    According to gazebo's native format description strings, which are basic type[9][9:15] looking strings
    Each GazeboDataFormatConverter can convert to and from a single format given to the constructor.
    Note that [n:o] does not indicate a slice in a gazebo string but rather a variable array.
    """

    def __init__(self,formatstring):
        #This basically works by tokenizing the gazebo datatype string, applying
        #a series of transformations, and then finallly parsing it.
        
        #we want an array where the fisrt elment is the base type
        #The second element is how many base types make up an innermost array
        #The second is how many innermot arrays make up a second level array, and so on.
        GazeboTypes = {"int16":"<h","uint16":'<H','int8':'<b','uint8':'<B','uint32':'<I','int32':'<i','UTF-8':'<B','float32':'<f','float64':'<d'}
        Type_as_list = formatstring.split('[')
        self.GazeboBaseType = Type_as_list[0]
        
        #Convert the base type to a python struct format string
        Type_as_list[0] = GazeboTypes[Type_as_list[0]]
        self.BaseTypeLen = struct.calcsize(Type_as_list[0])
        
        i2 = [Type_as_list[0]]
        #Get rid of all the closing brackets
        for i in Type_as_list[1:]:
            i2.append( i.replace(']',''))
        #Hack because I don't think we can change the iterable while iterating
        Type_as_list = i2
        
            

        #We want to make the last one a list [min,max] if it is a range.
        #dont split if there is no colon
        if ':' in Type_as_list[len(Type_as_list)-1]:
            Type_as_list[len(Type_as_list)-1] = Type_as_list[len(Type_as_list)-1].split(':')
        
        self.format = Type_as_list
        
    def GazeboToPython(self,data):
        """Take a byte array and convert it to python data"""
    #Check if the length of the byte array is an even multiple of the base type
        #Otherwise we have bytes that don't go anywhere and that is an error.
        if not ((len(data) % self.BaseTypeLen) == 0):
            return None
        
        #Unpack the input byte array into a list of whatever the base type is
        temp = []
        
        for i in range(0,len(data),struct.calcsize(self.format[0])):
            temp.append(struct.unpack(self.format[0],data[i:i+struct.calcsize(self.format[0])])[0])
        
        #Iterate over all of the nesting levels starting at the smallest and going towards the outermost
        
        for i in self.format[1:]:
        
            #if this level of nesting is variable size check for size in range.
            if isinstance(i, list):
                if (len(temp)> int(i[0])) and (len(temp)<int(i[1])):
                    #Variable elements can only be the last element in the nesting
                    return temp
            #If this nesting level is fixed size
            else:
                #check for things that are not multiples of the size we want
                if len(temp) % int(i)==0:
                    ##Package what we have so far into i equal size units
                    temp2=[]
                    for j in range(0,len(temp),int(i)):
                        temp2.append(temp[j:j+int(i)])
                    temp = temp2
                #When we cannot resolve how to unpack
                else:#This is for when you are having a bad problem and will not go to space
                    raise ValueError('Could not decode bytestream according to format string')
        #return the native python representation of the gazebo byte array
        if len(self.format)>1: #Ugly hack to see if the format is an array type or not
            return temp
        else:
            return temp[0]      #In this case there should only be one element so why wrap it in an array
         
    def PythonToGazebo(self,data):
        """Convert a python number, or iterable to gazebo's native data format"""
        
        def RecursiveNestedListSerialize(inputdata):
            """collapse a nested array to a single array. e.g. convert [[1,2],[3,4]] to [1,2,3,4]"""
            outer = []
            #Go through the input and add anything that is not iterable to the list
            #Anything that is iterable gets all of its contents added after first going through this function.
            for i in inputdata:
               if isinstance(i,collections.Iterable):
                     outer.extend(RecursiveNestedListSerialize (i))
               else:
                    outer.append(i)
            return outer
        
        if isinstance(data,int):
            return struct.pack(self.format[0],data)
        else:
            f = bytearray(0)
            d = RecursiveNestedListSerialize(data)
            for i in d:
                f.extend(struct.pack(self.format[0],i))

        return f
                
        

    
    
    
    
    
    
    
    
    
    
    
    
    
