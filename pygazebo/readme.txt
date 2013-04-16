Content-Type: text/x-zim-wiki
Wiki-Format: zim 0.4
Creation-Date: 2013-02-18T23:15:28-08:00

====== pygazebo docs ======
Created Monday 18 February 2013

Copyright 2013 Daniel Dunn
This work is licensed under a Creative Commons Attribution 3.0 Unported License.

===== Introduction =====

gazebo_protocol depends on crcmod and pyserial, so install those first.

===== The NetworkManager object: =====

The NetworkManager object handes request queuing, serial I/O, and slave discovery.

==== NetworkManger(comport) [Constructor] ====
To create it, you pass the constructor a string containing the name of a serial port.


=== Example: ===

'''
>>>manager = NetworkManager('com6')
>>>
'''


==== NetworkManager.EnumerateSlaves() ====
Causes the manager to search the network for slaves. May take up to 30 seconds per slave.
Every slave found will be placed in the slaves dict, indexed by a base64 version of thier UUID.

=== Example: ===
''>>>manager.EnumerateSlaves()''
''>>>''

==== NetworkManager.slaves ====
A dict of all of the slaves as Gazebo_Slave objects, indexed by UUID.

=== Example: ===
'''
>>> manager.slaves
{'VEhJU0lTQVRFU1RV': <__main__.Gazebo_Slave object at 0x0000000003085FD0>}
'''


==== NetworkManager.GetDevicesImplementing(GroupClassName) ====
Returns a dict of slaves that implement at least one instance of GroupClassName, indexed by UUID

==== NetworkManger.GetDevicesNamed(name) ====
Returns a dict of slaves with the specified device name, indexed by UUID

==== NetworkManager.SendInformationBroadcast(key,data,formatstring=None) ====

This lets you send arbitrary information broadcasts. Key is the broadcast key, data is the data, and formatstring is a normal gazebo format string(e.g uint8[9], float,float[2][2],enum{a;b;c;d},etc) that described how to translate the data. If  ths argument is missing, you must pass the exact raw binary.

===== The Gazebo_Slave object =====

This object represents one slave.

==== Gazebo_Slave.params ====
A dict of all parameters of the slave as NetworkParameter objects

==== Gazebo_Slave.SaveParameters() ====
Tell the slave to save all parameters that can be saved to nonvolatile memory. This command may take several seconds.
Watch out, as slaves will likely only support 10,000 to 1,000,000 write cycles.

==== Gazebo_Slave.GetInstances(groupclass) ====
Returns a dict(indexed by group instance name) of dicts(indexed by group role) of parameters

===== The NetworkParameter object =====

Represents one parameter


==== NetworkParameter.__call__(*args) ====
The network parameter object itself is callable. If the parameter is either readable or writable whichever one is supported will occur.
if the parameter is readable and writable a runtime error will be raised.

==== NetworkParameter.info() ====
Return a string of imformation about the parameter


==== NetworkParameter.pinfo() ====
prints the info string as retuned by info()

=== Example ===
'''
temp.info() #Get some info about the param. This was stored on the slave in a much more compact format
<Readable and writable parameter of type uint8 to be interpreted as temp
This parameter plays role none in group none of type none
No arguments are required when reading from this parameter
Reads are idempotent(two succesive reads will produce the same data absent external changes).
Writes are idempotent(writing the same data twite is equivalent to once)
'''


==== NetworkParameter.read(*args) ====
Read the value of the network parameter. Some parameters may not be simple variables and Reading may be equivalent to pulling from a queue, and some parameters may represent functions and arguments may be required. If the value was read very recently(default is 10hz), this may return a cached value, but only for reads that arer idempotent. The value will be translated to a native python equivalent(enum to string, utf8 to string, array to list, nested array to nested list,etc)

Note that in some cases the "read" operation of a parameter may in fact be a function that writes something.
In this case calling parameter.read to write something is confusing, so the parameter itself is callable for these cases. NetworkParameter(*args) is a direct alias of NetworkParameter.read(*args). Use whichever one you feel to be clearer.

=== Example ===
'''
>>> temp.Read()
254
'''


==== NetworkParameter.write(*data) ====
Writes data to the parameter. Returns True on success. The value will be translated from a native python equivalent. You can pass arrays in as lists, enums as strings, and nested arrays as nested lists.

If the gazebo parameter being written is a tuple, each field must be be passed as a separate argument.

=== Example ===
>>> temp.Write(90) #Lets write some random data to it!
True
>>> temp.Read() #Now let's read it back!
90

>>> XYposition.Write(90,87) #Lets write to a tuple parameter
True
>>> temp.Read() #Now let's read it back!
(90,87)

==== NetworkParameter.expires ====
The time(in seconds) to keep an old value for. The pygazebo library will try to cache values if it can to avoid unnecessary traffic.
Float values are allowed. parameters that have side effects to reading and parameters with non idempotent read operations will not be cached. Defaults to 100ms.

==== NetworkParameter.fresh() ====
Returns true if the parameter has not expired

==== NetworkParameter.CachedValue ====
The value returned the last time the actually slave device was polled
