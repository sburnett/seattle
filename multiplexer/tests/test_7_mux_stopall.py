# This test tries to use mux_waitforconn and mux_openconn. It has 2 clients connecting to 1 server.
# It then attempts to exchange the numbers 1 to 50. Then we try to close everything, and exit without exitall().

# Get the Multiplexer
include Multiplexer.py

MAX_NUM = 50

# Handle a new virtual connection
def new_virtual_conn(remoteip, remoteport, virtualsock, junk, multiplexer):
  # Exchange 1 to 100
  num = 1
  while True and num < MAX_NUM:
    data = virtualsock.recv(1024)
    if data == str(num):
      num = num + 1
      virtualsock.send(str(num))
      num = num + 1
    else:
      print "Unexpected number! Expected: ", str(num), " Received: ",data

  # Sleep a second before closing the socket
  sleep(1)
  virtualsock.close()

def client_exchange(clientn):
  # Try to connect to the other multiplexer
  virtualsock = mux_openconn("127.0.0.1", 12345)

  # Try to exchange 1 to 10
  num = 1
  while True and num <= MAX_NUM:
    virtualsock.send(str(num))
    num = num + 1
    data = virtualsock.recv(1024)
    if data == str(num):
      num = num + 1
    else:
      print "Unexpected number! Expected: ", str(num), " Received: ",data
  
  virtualsock.close()
  
  # This finished...
  mycontext[clientn] = True

def timeout():
  print "Reached timeout!"
  exitall()

if callfunc=='initialize':
  
  # Kill us in 25 seconds
  settimer(20, timeout,())

  # Setup a waitforconn on a real socket
  mux_waitforconn("127.0.0.1", 12345, new_virtual_conn)

  # Trigger three clients
  settimer(0,client_exchange,[1])

  # Wait before starting the third client
  sleep(6)
  client_exchange(2)

  # Check that they all registered and finished
  if not 1 in mycontext or not mycontext[1]:
    print "Client 1 failed to finish!"

  if not 2 in mycontext or not mycontext[2]:
    print "Client 2 failed to finish!"
  
  mux_stopall()
  
  # Check if everything is cleaned up
  if MULTIPLEXER_OBJECTS == {} and MULTIPLEXER_WAIT_FUNCTIONS == {} and MULTIPLEXER_WAIT_HANDLES == {}:
    pass
  else:
    print "Not cleaned up!"
    
  exitall()
