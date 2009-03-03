# This test tries to use mux_waitforconn and mux_openconn. 
# It has 3 clients connecting to 1 server.
# Clients will use a mux_virtual_openconn, and the server a mux_virtual_waitforconn
# It then attempts to exchange the numbers 1 to 100

# Get the Multiplexer
include Multiplexer.py

MAX_NUM = 100

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

def client_exchange(clientn, real):
  if real:
    # Try to connect to the other multiplexer
    # This is necessary for the first client to actually establish a multiplexed connection
    virtualsock = mux_openconn("127.0.0.1", 12345,virtualport=5)
  else:
    # Do a virtual openconn
    virtualsock = mux_virtual_openconn("127.0.0.1", 12345,5)

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
  settimer(25, timeout,())

  # Setup a waitforconn on a real socket
  mux_waitforconn("127.0.0.1", 12345, new_virtual_conn)

  # Setup a virtual waitforconn on a fake socket
  mux_virtual_waitforconn("127.0.0.1", 5, new_virtual_conn)

  # Trigger three clients
  settimer(0,client_exchange,[1,True])

  # Second two clients will use virtual_openconn
  settimer(1,client_exchange,[2,False])

  settimer(2,client_exchange,[3,False])

  # Wait for a few seconds
  sleep(15)

  # Check that they all registered and finished
  if not 1 in mycontext or not mycontext[1]:
    print "Client 1 failed to finish!"

  if not 2 in mycontext or not mycontext[2]:
    print "Client 2 failed to finish!"

  if not 3 in mycontext or not mycontext[3]:
    print "Client 3 failed to finish!"
  
  exitall()