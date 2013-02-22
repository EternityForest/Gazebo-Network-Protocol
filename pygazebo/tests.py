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

case('uint8[2][2]')

n = PyGazebo.GazeboDataFormatConverter('uint8[2][2]')

if n.PythonToGazebo([[1,2],[3,4]]) == b'\x01\x02\x03\x04':
    succeed()
else:
    fail()

if n.PythonToGazebo([[1,1],[3,3]]) == b'\x01\x01\x03\x03':
    succeed()
else:
    fail()
    
if n.GazeboToPython(b'\x01\x01\x03\x03') == [[1,1],[3,3]]:
    succeed()
else:
    fail()
    
####

case('uint8[4]')

n = PyGazebo.GazeboDataFormatConverter('uint8[4]')

if n.PythonToGazebo([1,2,3,4]) == b'\x01\x02\x03\x04':
    succeed()
else:
    fail()

if n.PythonToGazebo([1,1,3,3]) == b'\x01\x01\x03\x03':
    succeed()
else:
    fail()
    
if n.GazeboToPython(b'\x01\x01\x03\x03') == [1,1,3,3]:
    succeed()
else:
    fail()

##############################
case('uint8[3][6]')

n = PyGazebo.GazeboDataFormatConverter('uint8[3][6]')

if n.PythonToGazebo([[1,2,3],[4,5,6],[1,2,3],[4,5,6],[1,2,3],[4,5,6]]) == b'\x01\x02\x03\x04\x05\x06\x01\x02\x03\x04\x05\x06\x01\x02\x03\x04\x05\x06':
    succeed()
else:
    fail()


if n.GazeboToPython(b'\x01\x02\x03\x04\x05\x06\x01\x02\x03\x04\x05\x06\x01\x02\x03\x04\x05\x06') == [[1,2,3],[4,5,6],[1,2,3],[4,5,6],[1,2,3],[4,5,6]]:
    succeed()
else:
    fail()

    
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

if n.PythonToGazebo(['c','a']) == bytearray([2,0]):
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
test('ApplyNesting')
case
######################################################
test('GazeboArgumentsStringToListOfNamedTuples')

case("[a;b;c];[d;e;f]")

if PyGazebo.GazeboArgumentsStringToListOfNamedTuples('[[a;b;c];[d;e;f]]') == [('a','b','c'),('d','e','f')]:
    succeed()
else:
    fail()

case("[a;b;c];[d;e]")


try:
     PyGazebo.GazeboArgumentsStringToListOfNamedTuples('"[a;b;c];[d;e]"') #This cannot be made into an even number of 3-tuples so will fail.
     fail()
except ValueError:
     succeed()

#######################################################
test('GazeboPacket')
case('Make a packet, convert to bytes and back')

g = PyGazebo.GazeboPacket()

g.data = b'testing'
g.type = 123
g.address = 456

b = g.toBytes()

f = PyGazebo.GazeboPacket()

#Should return 0 or not complete
if f.ParseBytes(b[0:-3]):
    fail()
else:
    succeed()
    
#Should return 1 because we gave it the rest
if f.ParseBytes(b[-3:]):
    succeed()
else:
    fail()
#Maxe sure the data matches
if (f.data == b'testing') and (f.type ==g.type) and (f.address == g.address):
    succeed()
else:
    fail()

h = PyGazebo.GazeboPacket()

#Now parse again but give it a bad CRC
h.ParseBytes(b[:-1])
if h.ParseBytes(bytearray(b[-1]+2)) == -1:
    succeed()
else:
    fail()


 

    
print('failures: ' +str(failures) +'\n')
print(failedmodules)
