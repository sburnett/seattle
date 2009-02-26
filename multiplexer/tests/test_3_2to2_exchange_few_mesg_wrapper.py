# This test tries to use mux_waitforconn and mux_openconn.
# This has 2 servers, each connected to by 1 client.
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


def client_exchange(clientn,port,local):
  # Try to connect to the other multiplexer
  virtualsock = mux_openconn("127.0.0.1", port,"127.0.0.1",local)

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
  
  # This finished...
  mycontext[clientn] = True

def timeout():
  print "Reached timeout!"
  exitall()

# Kill us in 25 seconds
settimer(25, timeout,())

# Setup a waitforconn
mux_waitforconn("127.0.0.1", 12345, new_virtual_conn)

# Trigger two clients
settimer(0,client_exchange,[1,12345,20000])

sleep(2)

# Setup second waitforconn
mux_waitforconn("127.0.0.1", 20000, new_virtual_conn)

# Setup second client
settimer(1,client_exchange,[2,20000,None])

# Wait for a few seconds
sleep(15)

# Check that they all registered and finished
if not 1 in mycontext or not mycontext[1]:
  print "Client 1 failed to finish!"

if not 2 in mycontext or not mycontext[2]:
  print "Client 2 failed to finish!"


exitall()