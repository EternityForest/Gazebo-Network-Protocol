Introduction
------------

pygazebo depends on crcmod and pyserial, so install those first.

The NetworkManager object:
--------------------------

The NetworkManager object handes request queuing, serial I/O, and slave discovery.

### NetworkManger(comport) [Constructor]
To create it, you pass the constructor a string containing the name of a serial port.


#### Example:

	>>>manager = NetworkManager('com6')
	>>>


### NetworkManager.EnumerateSlaves()
Causes the manager to search the network for slaves. May take up to 30 seconds per slave.
Every slave found will be placed in the slaves dict, indexed by a base64 version of thier UUID.

#### Example:
``>>>manager.EnumerateSlaves()``
``>>>``

### NetworkManager.slaves
A dict of all of the slaves as Gazebo_Slave objects, indexed by UUID.

#### Example:
	>>> manager.slaves
	{'VEhJU0lTQVRFU1RV': <__main__.Gazebo_Slave object at 0x0000000003085FD0>}


The Gazebo_Slave object
-----------------------

This object represents one slave.

### Gazebo_Slave.params
A dict of all parameters of the slave as NetworkParameter objects

The NetworkParameter object
---------------------------

Represents one parameter

### NetworkParameter.info()
prints an info string.

#### Example
	temp.info() #Get some info about the param. This was stored on the slave in a much more compact format
	<Readable and writable parameter of type uint8 to be interpreted as temp
	This parameter plays role none in group none of type none
	No arguments are required when reading from this parameter
	Reads are idempotent(two succesive reads will produce the same data absent external changes).
	Writes are idempotent(writing the same data twite is equivalent to once)


### NetworkParameter.Read(*args)
Read the value of the network parameter. Some parameters may not be simple variables and Reading may be equivalent to pulling from a queue, and some parameters may represent functions and arguments may be required. If the value was read very recently(default is 10hz), this may return a cached value, but only for reads that arer idempotent.

#### Example
	>>> temp.Read()
	254


### NetworkParameter.Write(data)
Writes data to the parameter. data can be an integer or a list as appropriate for the parameter. Returns True on success.

#### Example
>>> temp.Write(90) #Lets write some random data to it!
True
>>> temp.Read() #Now let's read it back!
90