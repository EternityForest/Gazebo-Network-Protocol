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

DATA_START_INDEX = 5
MINIMUM_NORMAL_GAZEBO_ADDRESS =4097

##Giant list of packet type data
PACKET_TYPE_SLAVE_PRESENCE_DETECT_REQUEST = 0
PACKET_TYPE_ADDRESS_SET = 2
PACKET_TYPE_SLAVE_DATA_REQUEST = 4
PACKET_TYPE_SLAVE_ERROR = 5
PACKET_TYPE_PARAMETER_INFO_REQUEST = 6
PACKET_TYPE_PARAMETER_READ = 8
PACKET_TYPE_WRITE = 10
PACKET_TYPE_INFORMATION_BROADCAST = 16
PACKET_TYPE_SAVE_NONVOLATILE = 22

##List of indexes into parameter descriptor strings after unCSVing
PARAMETER_DESCRIPTOR_NAME_INDEX = 0
PARAMETER_DESCRIPTOR_TYPE_INDEX = 1
PARAMETER_DESCRIPTOR_INTERPETATION_INDEX = 2
PARAMETER_DESCRIPTOR_ARGUMENTS_INDEX = 3
PARAMETER_DESCRIPTOR_FLAGS_INDEX = 4
PARAMETER_DESCRIPTOR_GROUP_ROLE_INDEX = 5
PARAMETER_DESCRIPTOR_GROUP_NAME_INDEX = 6
PARAMETER_DESCRIPTOR_GROUP_CLASS_INDEX = 7
PARAMETER_DESCRIPTOR_DESCRIPTION_INDEX = 8

SLAVE_DESCRIPTOR_FIRMWARE_VERSION_INDEX = 0
SLAVE_DESCRIPTOR_SLAVE_NAME_INDEX = 1
SLAVE_DESCRIPTOR_TOTAL_PARAMETERS_INDEX = 4


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
    
    #Get rid of the brackets, they are just syntax crap on the slave
    gstring = gstring.replace('[','').replace(']','')
    #Split on semicolons because once we get rid of the brackets its essentally a semicolon separated list
    s = gstring.split(';')
    
    
    #If there is no arguments required, there will be no semicolons and thus len(1) after parsing.
    if (len(s)==1):
       return []
    #[[a;b;c];[a;b;c]]
    #Check to make sure that it can be evenly divided into n name,type,interpretation tuples, or has no semicolons at all indicating maybe
    #there are no arguments
    if not ( (len(s) % 3) == 0):
        raise ValueError('Does not appear to be a valid Gazebo Arguments List')
    v = []

    #Iterate with step size 3 to divide s into tuples of three.
    for i in range(0,len(s),3):
        g = GazeboReadArgument(s[i],s[i+1],s[i+2])
        v.append(g)
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
        self.type = 5 #default to the error type
        self.data = b'\x00No Packet'
    
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
                        return 1  
                    if self._internalbuffer[0] == 0x31:
                        self.data = True
                        return 1                        
                    if self._internalbuffer[0] == 6:
                        self.data = 'ACK'
                        return 1
                return -1#Packets can't start with anything but 0x55
            
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
    """Class representing one gazebo slave. When you initialize it with a manager, UUID, and address, 
    it will automatically figure the rest out, by asking the the actual slave device for information."""
    def __init__(self, manager ,UUID,address):
    
        self.id = UUID
        self.address = address
        self.params = {}
        self.manager = manager
        g = GazeboPacket()
        
        SlaveDescriptor = ''
        for i in range(0,255):
            #Create a packet and send it
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
            
            #Get rid of the null terminator
            for j in n.returndata:
                if not j == 0:
                    dat.append(j)
                else:
                    break
            
            SlaveDescriptor = SlaveDescriptor + dat.decode('utf-8')
            
            if 0 in n.returndata:
                break #The page with the nul is the last page
        
        sd = SlaveDescriptor.split(',')
        self.name = sd[SLAVE_DESCRIPTOR_SLAVE_NAME_INDEX]
        self.fwversion = sd[SLAVE_DESCRIPTOR_FIRMWARE_VERSION_INDEX]
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
            n.description = pd[PARAMETER_DESCRIPTOR_DESCRIPTION_INDEX]
            n.arguments = GazeboArgumentsStringToListOfNamedTuples(pd[PARAMETER_DESCRIPTOR_ARGUMENTS_INDEX])
            
            n._datainterpreter = GazeboDataFormatConverter(n.type)
            n._argumentconverters = []
            
            #Pre-Intitialize a list of argument converters because it takes time to parse
            #One for each argument required when reading from this parameter
            for j in n.arguments:
                n._argumentconverters.append(GazeboDataFormatConverter(j.type))
            n.name = pd[PARAMETER_DESCRIPTOR_NAME_INDEX]
            self.params[pd[PARAMETER_DESCRIPTOR_NAME_INDEX]] = n

            
    def __repr__(self):
        return('<Gazebo Slave '+ self.name + ' with ID ' + base64.b64encode(self.id)[:16].decode() + ">")
      
    def SaveParameters(self):
         """Tell the slave to save all savable parameters to nonvolatile memory"""
         g = GazeboPacket()
         g.data = b'CONFIRM'
         g.address = self.address
         g.type = PACKET_TYPE_SAVE_NONVOLATILE
         b = g.toBytes()
         n = NetworkRequest(self.manager)
         n.data = b
         n.expect = 'gazebopacket'
         return n.Send()
         
    def GetInstances(self,groupclass):
        """Get a dict of dicts of parameters where the outer dict is indexed by group name and the inner by role"""
        output = {}
        
        #Iterate over params
        for i in self.params:
            #Ignore params without the proper group class
            if i.groupclass == groupclass:
                #If there is not already a dict of params for this group instance make one
                if not (i.groupname in output):
                    output[i.groupname] = {}
                #Add the param to the group instance dict with its group role as its key
                output[i.groupname][i.grouprole] = i
                
        return output
        
class NetworkManager(object):
    """Manage the serial port, enumeration of slaves, and discovery of resources. also manage
    request queuein and resource sharing between threads. set HasEcho=True for half duplex lines where you hear everything you send."""
    
    def __init__(self,comport,HasEcho = False):
        self.comport = serial.Serial(comport)
        self.comport.timeout = 10
        self.MediumHasEcho = HasEcho
        #Setup the request queue
        self.requestqueue = queue.Queue()
        self.slaves = {}
        self.highestunusedaddress = 5000 #Because of reserved area in the address space
        self.retrylimit = 16
        #All the actual network stuff is going to happen in a new thread
        t = threading.Thread(target = self.__HandleRequestQueue)
        t.start()

    def __del__(self):
        self.comport.close()

    def close(self):
        """Close the underlying comport"""
        self.comport.close()
        
    #This goes and loops in its own thread and waits for new data to come into the request queue
    def __HandleRequestQueue(self):
        while self:
            thisrequest = self.requestqueue.get()
            self.comport.write(thisrequest.data)
            if self.MediumHasEcho:
               self.comport.timeout = 25
               self.comport.read(len(thisrequest.data))#Clear all the stuff in the buffer if we are on a half duplex line where we recieve what we send

            time.sleep(0.0015)
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
                t = 0
                self.comport.timeout = 0.3 #Max time between bytes
                while(time.time()-start)<10:#Max total packet time
                    #Check if a complete packet has been recieved
                    
                    x = self.comport.read(max(self.comport.inWaiting(),1))#If there are no bytes in waiting we need to wait for
                                                                          #one or else the whole thing will return and thing there is no packet
                    if x == b'': #If a read with timeout 0.3 does not return anything
                        break;   #Stop looking because responses must start within 10ms and not have
                                 #more than a byte time of silence so 0.3 is a big margin.
                                 
                    t = f.ParseBytes(x)
                    if not t == 0:
                        #Break if a complete packet is here or if a known bad packet is here
                        break;
                     
                #If no packet or a known bad packet
                if t == -1 or t == 0:
                    if thisrequest.retries > 0: #Retry up to the maximum number of attemts.
                        if thisrequest.retries > self.retrylimit:
                            thisrequest.retries = self.retrylimit
                            thisrequest.retries -= 1
                            self.requestqueue.put(thisrequest)
                    else: #If we have used up our maximum number of retries, return None
                        thisrequest.returndata = None
                        thisrequest.LockedWhileNotCompleted.set()
                #If a correct gazebo packet is here
                if t == 1:
                    thisrequest.returndata = f.data
                    thisrequest.fullpacket = f
                    thisrequest.LockedWhileNotCompleted.set()
                    
            thisrequest.LockedWhileNotCompleted.set()#Failsafe, handles the case of expect==none
                    
                    
    
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
                
    
    def GetDevicesNamed(self,name):
        """Get all devices with the specified device name"""
        matchingslaves = {}
        for slave in self.slaves:
            if slave[key].name == name:
                matchingslaves[slave.id] = slave
        return matchingslaves
                
    def GetDevicesImplementing(self,NameOfGroupClass):
        """Get all devices implementing the specified group"""
        matchingslaves = {}
        for slave in self.slaves:
            if slave.groupclass == NameOfGroupClass:
                matchingslaves[slave.id] = slave
        return matchingslaves
                
    def DetectSlavePresence(self,UUID,matchlength = 128,connected = 'unassigned'):
        """Returns true if there is a slave at the specified UUID. 
        Allows partial matching and matching devices that have not been given an ID"""
        
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
        #All we want to know is if at least one device responded. So we listen for 23ms.
        n.expect = ['time',0.023]
        n.Send()
        if len(n.returndata) >0:
            return True
        else:
            return False
            
        
        
        
    def SendInformationBroadcast(self,key,data,formatstring = None):
        """Send an information broadcast to all slaves connected or not.
          if the optional formatstring is a valid gazebo format string,
          will attempt to convert the input data according to it. Otherwise you must provide the raw bytes"""
        
        if not (formatstring == None):
           i = GazeboDataFormatConverter(formatstring)
           data = i.PythonToGazebo(data)
           
        g = GazeboPacket()
        g.address = 0

        #Pad with zeros till 8 chars, or truncate at 8.
        k = bytearray(8)
        j =0
        for i in key.encode('utf-8'):
           k[j]=i
           j+=1
           
        g.data = k + data
        g.type = PACKET_TYPE_INFORMATION_BROADCAST
        b = g.toBytes()
        n = NetworkRequest(self)
        n.data = b
        n.expect = None
        n.Send(7)
    
    # def SendTimeInfo(self):
                # t = time.localtime()
                # self.SendInformationBroadcast('YEAR',struct.pack('<H',t[0]))
                # self.SendInformationBroadcast('MONTH',struct.pack('<B',t[1]))
                # self.SendInformationBroadcast('MONTH',struct.pack('<B',t[3]))
                # self.SendInformationBroadcast('MONTH',struct.pack('<B',t[2]))
                
    def ForceAddOneSlave(self,slaveUUID):
        """Check for a slave based on the unique ID of that slave. If found return true and add that slave to
        The slave dict.
        """
    
        if slaveUUID in self.slaves:
            return True
            slaveUUID = (slaveUUID+'==').decode()
        if self.DetectSlavePresence(slaveUUID):
            s = GazeboSlave(self,slaveUUID,self.highestunusedaddress)
            self.highestunusedaddress +=1
            return True
        else:
            return False

#A simple class encapsulating an arbitrary request of the network, in terms of data to be sent
#And data to be expected. manager must be a SerialManager or derivative.
#data must be a byte array. expect can be GazeboPacket, ["time", NumberOfSeconds], or ['len', BytesExpected]
#This can be sent multiple times and each time the 
class NetworkRequest(object):
    """A class encapsulatng one request that may expect a response. Does not need to be a Gazebo packet.
      when Send is called, the data in self.data will be sent using the selected network manager.
      if expect is 'gazebopacket', the data from the response wil be found in self.returndata
      The entire gazebo packet object will be found in fullpacket. """
    def __init__(self, manager, data = None, expect = ["time",1]):
        self.manager = manager
        self.data = data
        self.expect = expect
        self.LockedWhileNotCompleted = threading.Event()
        self.retries = 0
        
        
    def Send(self,priority ="7",block = True):
        self.manager.requestqueue.put(self)
        self.LockedWhileNotCompleted.clear()
        if block and (not(self.expect == None)):
            #wait for the request to complete
            self.LockedWhileNotCompleted.wait()
            return self.returndata
        
        return None
        

class NetworkParameter(object):
    """A class representing one parameter of a slave device. Contains a reference to its parent slave."""
    

    def __init__(self):
      self.LastUpdated = 0
      self.expires =0.1 #Default to read-idempotent parameters being cached for a tenth of a second
      
    def __call__(self, *args): #NetworkParameter is callable, and calling it is an alias for read.
        return self.read(*args)
      
    def read(self, *args):
        """Returns the value of the parameter. Will use the cached value if possible."""
        #Check if we can avoid making the request by just returning the cached value.
        if not self.fresh():
            g = GazeboPacket()
            g.data = bytearray(struct.pack("<B",self.paramnumber))
            j = 0
            for i in args:
                #Convert all of the arguments using the list of argument converters that the parameter
                #instance has
                g.data.extend(self._argumentconverters[j].PythonToGazebo(i))
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
                if r.fullpacket.type == 5:
                    raise ValueError('Slave says something went wrong, errordata:' + str(r.returndata))
                temp = self._datainterpreter.GazeboToPython(temp)
                self.CachedValue = temp
                self.LastUpdated = time.time()
                return temp
            else:
                return None
        #If the cached value was fresh
        else:
            return self.CachedValue
            
    def write(self,data):
        """Write data to a parameter. Data must be of a format that is compatibe with the devices expected type."""
        
        #Translate the input data to gazebo's format, prepend the parameter number
        temp = self._datainterpreter.PythonToGazebo(data)
        data = struct.pack('<B',self.paramnumber)
        data= data + temp
        
        
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
    
    def fresh(self):
        """Internal function used to determine if the cached value is still good."""
        #Not-Idempotent values are not cacheable
        if not 'i' in self.flags:
            return False
        #Read with arguments values are not cacheable
        if len(self.arguments):
           return False
        #If the variable has already expired
        if (time.time() - self.LastUpdated) > self.expires:
            return False
            
        #Early return pattern
        return True
    def pinfo(self):
        print(self.info())
        
    def info(self):
    #Make a human readable report of this parameter
        string = "\n"
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
        else:
            string+=('The following arguments are required when reading from this parameter(in first to last order):\n')
            for i in self.arguments:
                string+= repr(i)
                string+= ('\n')
        if '!' in self.flags:
            string += '***CAUTION!! ACHTUNG!! USE CARE WHEN MESSING WITH THIS PARAMETER. THE DEVICE HAS MARKED IT AS CRITICAL.***\n'
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
            string += 'This is a message-wise FIFO. Reads will return the one(1) oldest item and likewise for writes.\n'
        if 'n' in self.flags:
            string += 'This parameter can be saved to nonvolatile memory.\n'
        
        string += '\n\nThe slave provides the following description of ths parameter:'
        string += self.description
            
        return string

    def __repr__(self):
        return('<Parameter Object ' + self.name + ' of type ' + self.type + ' with interpretation ' +self.interpretation + '>')

def GazeboDataFormatConverter(formatstring):
    """Create some specialized sublclass of BaseGazeboDataConverter toconvert to and from binary data according to
    the format string."""

   #void types have a very simple converter
    if formatstring.startswith('void'):
       return GazeboVoidConverter()
      
    #Detect enum types
    if formatstring.startswith('enum'):
        #If this is an array of enum, it will have at leat one [
        if '[' in formatstring:
            #GazeboArrayofEnumConverter also does nested arrays
            return GazeboArrayofEnumConverter(formatstring)
        else:
            return GazeboEnumConverter(formatstring)
    
    #TODO add array of string support
    if formatstring.startswith('UTF-8'):
        return GazeboStringConverter(formatstring)
        
    #If we got ths far it is not a string or an enum, so if it has a brace, it is probable an array of numbers
    if '[' in formatstring:
        #GazeboArrayofNumbersConverter also does nested arrays
        return GazeboArrayofNumbersConverter(formatstring)
    else:
    #No brace, not enum or string, probably a single number.
        return GazeboNumberConverter(formatstring)
      

 
class BaseGazeboDataConverter():
    """Base class providing functionality for interpreting gazebo types. May not be instatiated.
    The API is that you pass the gazebo format string from the parameter descriptor to the constructor of a subclass
    and the resulting object will convert to and from gazebo data. Conversions should not have side effects.

    Subclasses need only handle their subset of format strings.
    """

    #Some data to convert from gazebo's idea of a base type to a struct pack unpack input.
    GazeboTypes = {"int16":"<h","uint16":'<H','int8':'<b','uint8':'<B','uint32':'<I','int32':'<i','UTF-8':'<B','float32':'<f','float64':'<d','enum':'<B'}

    def __init__(self,formatstring):
        raise NotImplementedError

    def GazeboToPython(self,data):
        """This must return relevant python data"""
        raise NotImplementedError
    def PythonToGazebo(self,data):
       """This must return a bytestring"""
       raise NotImplementedError

    def FormatStringToTupleOfBaseAndNesting(self,formatstring):
       """Take as input a Gazebo format string, 
       and return as output a tuple of the base type along with a list representing the nesting structure
       an example of the nesting format would be: [ [2] [ [1][2] ] ] for a variable array of two element arrays.

       Essentially, the innermost array size is the first element, the second to innermost array size is the second element, and optionally the last element may itself be a list, with the first being min and the second being max. ONLY the outermost array can be of variable size. If we allowed multiple levels of variable array it would be very ambiguos how we should parse a raw bytestring. If we allowed any level other than the last to be variable it would complicate parsing for not much benefit.
       """

       #Each array level is specified C style in braces so split on opening braces
       Type_as_list = formatstring.split('[')



       i2 = [Type_as_list[0]]
       #Get rid of all the closing brackets
       for i in Type_as_list[1:]:
           i2.append( i.replace(']',''))

      #We want to make the last one a list [min,max] if it is a range.
       #dont split if there is no colon
       if ':' in Type_as_list[-1]:
           Type_as_list[-1] = Type_as_list[-1].split(':')
           Type_as_list[-1][0] = int(Type_as_list[-1][0])
           Type_as_list[-1][1] = int( Type_as_list[-1][1])
           
       Type_as_list = i2
 
       #The first element is the base type and the rest is a nesting structure
       return (Type_as_list[0],Type_as_list[1:])

    def ApplyNesting(self,nesting,data):
       """take a flat list and nest it according to a nesting structure supplied as a list
       The nesting format is that which is returned by the FormatStringToTupleOfBaseAndNesting function.
       """
       temp = data
       for i in nesting:
           
               #if this level of nesting is variable size check for size in range.
               if isinstance(i, list):
                   if (len(temp)> int(i[0])) and (len(temp)<int(i[1])):
                       #Variable elements can only be the last element in the nesting
                       return temp
                   else:
                        raise ValueError('Could not decode bytestream according to format string')
               #If this nesting level is fixed size
               else:
                   #check for things that are not multiples of the size we want
                   if len(temp) % int(i) ==0:
                       ##Package what we have so far into i equal size units
                       temp2=[]
                       for j in range(0,len(temp),int(i)):
                           temp2.append(temp[j:j+int(i)])
                       temp = temp2
                   #When we cannot resolve how to unpack
                   else:#This is for when you are having a bad problem and will not go to space
                       raise ValueError('Could not decode bytestream according to format string')
               #return the native python representation of the gazebo byte array
               
       return temp[0]
        
    def RecursiveNestedListSerialize(self,inputdata):
       """collapse a nested array to a single array. e.g. convert [[1,2],[3,4]] to [1,2,3,4]
          Basically recursively walks a tree of lists and returns one big list of things that are not lists.
       """

       outer = []
       #Go through the input and add anything that is not itself a list to the list
       #Anything that is iterable gets all of its contents added after first going through this function.
       for i in inputdata:
          if isinstance(i,list):
                outer.extend(self.RecursiveNestedListSerialize (i))
          else:
               outer.append(i)
       return outer

        
        
class GazeboNumberConverter(BaseGazeboDataConverter):
    
    def __init__(self,formatstring):
        #init a value passed to struct.pack and struct.unpack with the data
        self._structformat = self.GazeboTypes[self.FormatStringToTupleOfBaseAndNesting(formatstring)[0]]
    
    def GazeboToPython(self, data):
        return struct.unpack(self._structformat,data)[0]
    
    def PythonToGazebo(self,data):
        return struct.pack(self._structformat,data)

class GazeboArrayofNumbersConverter(BaseGazeboDataConverter):
    
    def __init__(self,formatstring):
        #init a value passed to struct.pack and struct.unpack with the data
        self._structformat = self.GazeboTypes[self.FormatStringToTupleOfBaseAndNesting(formatstring)[0]]
        self._nestingformat = self.FormatStringToTupleOfBaseAndNesting(formatstring)[1]
        self._BaseTypeLen = struct.calcsize(self.GazeboTypes[self.FormatStringToTupleOfBaseAndNesting(formatstring)[0]])
        
    def GazeboToPython(self, data):
        if not( (len(data) % self._BaseTypeLen)==0):
            raise ValueError("The data was not an even multiple of the base type")
        
        t = []
        
        #Make a flat array of all of the values
        for i in range(0,len(data),self._BaseTypeLen):
            t.append(struct.unpack(self._structformat,data[i:i+self._BaseTypeLen])[0])
            
        #Impose the nesting structure
        return self.ApplyNesting(self._nestingformat,t)
    
    def PythonToGazebo(self,data):
        t = bytearray(0)
        
        #Flatten the list, than structify it and return it
        for i in self.RecursiveNestedListSerialize(data):
            t.extend(struct.pack(self._structformat,i))
            
        return t

class GazeboStringConverter(BaseGazeboDataConverter):
    """Handles conversion to strings, automatically decodes and encodes to python strings.
    Currently no support for arrays of strings. Uses UTF-8.
    """
    
    def __init__(self,formatstring):
       ...
        
    def GazeboToPython(self, data):
        return data.decode('utf8')
    
    def PythonToGazebo(self,data):
        return data.encode('utf8')

class GazeboEnumConverter(BaseGazeboDataConverter):
    """Handle gazebo values consisting of single enums"""
    
    def __init__(self,formatstring):
        #init a value passed to struct.pack and struct.unpack with the data
        
        temp = self.FormatStringToTupleOfBaseAndNesting(formatstring)[0]
        temp = temp.split('{')[1] #Get just the enum list
        temp = temp.split('}')[0] #Remove trailing close bracket to get raw csv
        
        temp = temp.split('|')   #Get the list of possibilities
    
        #Create a dict mapping enumeration keys to values.
        self._enumtovalues = {}
        j=0
        for i in temp:
            self._enumtovalues[i] = j
            j+=1
        
        #Now make a dict mapping values back to enumeration keys
        self._valuetoenum = {}
        j=0
        for i in temp:
            self._valuetoenum[j] = i
            j+=1
        #All gazebo enums are based on unsigned chars, so set the structformat as appropriate
        self._structformat = '<B'
    
    def GazeboToPython(self, data):
        return self._valuetoenum[struct.unpack(self._structformat,data)[0]]
    
    def PythonToGazebo(self,data):
       if isinstance(data,int):
          return bytearray([data])
         
       return struct.pack(self._structformat,self._enumtovalues[data])
    
class GazeboArrayofEnumConverter(GazeboEnumConverter):
    
    def __init__(self,formatstring):
        #init a value passed to struct.pack and struct.unpack with the data
        GazeboEnumConverter.__init__(self,formatstring) #We need a lot of stuff the base class does
        self._nestingformat = self.FormatStringToTupleOfBaseAndNesting(formatstring)[1]
        self._BaseTypeLen = 1
        
    def GazeboToPython(self, data):
       
        if not( (len(data) % self._BaseTypeLen)==0):
            raise ValueError("The data was not an even multiple of the base type")
        
        t = []
        
        #Make a flat array of all of the values
        for i in data:
            t.append(self._valuetoenum[i])
            
        #Impose the nesting structure
        return self.ApplyNesting(self._nestingformat,t)
    
    def PythonToGazebo(self,data):
        t = bytearray(0)
        
        #Flatten the list, than structify it and return it
        for i in self.RecursiveNestedListSerialize(data):
           if isinstance(i,int):
              t.append(i)
           else:
               t.extend(struct.pack(self._structformat,self._enumtovalues[i]))
            
        return t
   
class GazeboVoidConverter(BaseGazeboDataConverter):
   def __init__(self):#Override
      pass
   def PythonToGazebo(self,data):
      return b''
   def GazeboToPython(self,data):
      return True

        
# def CreateGazebeException(ErrorCode,ExtraData = ''):
    # if ErrorCode == 0:
        # return GazeboError(ExtraData)
    # if ErrorCode == 0:
        # return GazeboError(ExtraData)
    # if ErrorCode == 0:
        # return GazeboError(ExtraData)
        
# class GazeboError(Exception):
        
        # def __init__(self,description):
           # self.value = value
        # def __str__(self):
           # return repr(self.value)
           
# class GazeboNonexistantParameterError(GazeboError):
        # def __init__(self,description,parameter = None):
           # self.value = 'Too short data string to write to parameter'
        # def __str__(self):
           # return repr(self.value)

# class GazeboTooShortDataWriteError(GazeboError):
        # def __init__(self,description,parameter = None):
           # self.value = 'Too short data string to write to parameter'
        # def __str__(self):
           # return repr(self.value)
           
# class GazeboTooLongDataWriteError(GazeboError):
        # def __init__(self,description,parameter = None):
           # self.value = 'Too long data string to write to parameter'
        # def __str__(self):
           # return repr(self.value)
           
# class GazeboTooManyGroupsError(GazeboError):
        # def __init__(self,description,parameter = None):
           # self.value = 'The device cannot join any more groups without quitting at least one'
        # def __str__(self):
           # return repr(self.value)
           
# class GazeboTooLittleArgumentDataError(GazeboError):
        # def __init__(self,description,parameter = None):
           # self.value = 'Too short data string as argument(s) to parameter read operation'
        # def __str__(self):
           # return repr(self.value)
           
# class GazeboTooMuchArgumentDataError(GazeboError):
        # def __init__(self,description,parameter = None):
           # self.value = 'Too long data string as argument(s) to parameter read operation'
        # def __str__(self):
           # return repr(self.value)

# class GazeboInvalidDataError(GazeboError):
        # def __init__(self,description,parameter = None):
           # self.value = 'Data sent was rejected by slave as invalid'
        # def __str__(self):
           # return repr(self.value)
           
# class GazeboInvalidDataError(GazeboError):
        # def __init__(self,description,parameter = None):
           # self.value = 'Data sent was rejected by slave as invalid'
        # def __str__(self):
           # return repr(self.value)
