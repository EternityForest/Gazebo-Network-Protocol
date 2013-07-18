Gazebo-Network-Protocol
=======================

A very simple network protocol for self documenting devices supporting natve error handling, 
units of measure, device discovery, and many other features.

Gazebo allows plug and play devices to expose "Parameters" to a master device.
Parameters are not limited to simple variables and may represent arrays, item or message oriented FIFO buffers, or 
even function calls.

Devices are uniquely identified with UUIDs allowing anyone to create conforming device by randomly generating the UUID
rather than purchase a number from some authority.

The code currently comiles to under 9k on the arduino leonardo. All the hardware dependant stuff is in one small file so
it is very easy to port.

Dependancies
------------
Python(tested on 3.xx, may work in 2.6+)

crcmod

pyserial

Creating Slave Devices
----------------------
Look at the example arduino sketch, particularly networkinterface.c and machine.cpp.
The implementation was designed so that those are the only files that you need to modify.
