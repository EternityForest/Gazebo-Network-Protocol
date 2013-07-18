from distutils.core import setup
setup(name='gazebo_protocol',
      version='0.29',
      packages=['gazebo_protocol'],
	  requires=['crcmod','pyserial']
      )
