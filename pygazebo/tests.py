import PyGazebo

failures = 0
sucesses = 0
failedmodules = {}


def fail():
    global failures
    failures += 1
    failedmodules[CurrentlyTesting].append(thistestcase)
def succeed():
    global sucesses
    sucesses +=1
def test(name):
    global CurrentlyTesting
    CurrentlyTesting = name
    failedmodules[CurrentlyTesting] = []
def case(case):
    global thistestcase
    thistestcase = case

test('Data format conversion with format strings')

case('UTF-8')

n = PyGazebo.GazeboDataFormatConverter('UTF-8[0:80]')

if n.PythonToGazebo('test') == b'test':
    succeed()
else:
    fail()

if n.PythonToGazebo('') == b'':
    succeed()
else:
    fail()
    
if n.GazeboToPython(b'') == '':
    succeed()
else:
    fail()
    
if n.GazeboToPython(b'1234') == '1234':
    succeed()
else:
    fail()
###
case('enum{a;b;c;de;fgh}')

n = PyGazebo.GazeboDataFormatConverter('enum{a;b;c;de;fgh}')

if n.PythonToGazebo('a') == b'\x00':
    succeed()
else:
    fail()

if n.PythonToGazebo('fgh') == b'\x04':
    succeed()
else:
    fail()
    
if n.GazeboToPython(b'\x00') == 'a':
    succeed()
else:
    fail()
    
if n.GazeboToPython(b'\x02') == 'c':
    succeed()
else:
    fail()
####

case('uint16')

n = PyGazebo.GazeboDataFormatConverter('uint16')

if n.PythonToGazebo(0) == b'\x00\x00':
    succeed()
else:
    fail()
    
if n.GazeboToPython(b'\x00\x00') == 0:
    succeed()
else:
    fail()
####

case('uint16[2][2]')

n = PyGazebo.GazeboDataFormatConverter('uint8[2][2]')

if n.PythonToGazebo([[1,2],[3,4]]) == b'\x01\x02\x03\x04':
    succeed()
else:
    fail()
    
if n.GazeboToPython(b'\x01\x02\x03\x04') == [[1,2],[3,4]]:
    succeed()
else:
    fail
    
###########
case('enum{a;b;c;de;fgh[2]}')

n = PyGazebo.GazeboDataFormatConverter('enum{a;b;c;de;fgh}[2]')

if n.PythonToGazebo(['a','b']) == bytearray([0,1]):
    succeed()
else:
    fail()

if n.PythonToGazebo(['b','a']) == bytearray([1,0]):
    succeed()
else:
    fail()
    
if n.GazeboToPython(b'\x01\x00') == ['b','a']:
    succeed()
else:
    fail()
    
if n.GazeboToPython(bytearray([0,1])) == ['a','b']:
    succeed()
else:
    fail()
    
print('failures: ' +str(failures) +'\n')
print(failedmodules)
