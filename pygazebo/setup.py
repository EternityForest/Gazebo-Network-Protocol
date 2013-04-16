from distutils.core import setup
setup(name='gazebo_protocol',
      version='0.28',
      py_modules=['gazebo_protocol'],
	  requires=['crcmod','pyserial']
      )
