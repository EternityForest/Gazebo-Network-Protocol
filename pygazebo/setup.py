from distutils.core import setup
setup(name='Gazebo Master Implementation',
      version='0.2',
      py_modules=['gazebo_protocol'],
	  requires=['crcmod','pyserial']
      )
