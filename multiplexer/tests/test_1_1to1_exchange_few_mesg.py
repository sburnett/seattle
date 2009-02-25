# This test tries to use waitforconn and openconn from repy to get a real socket.
# It then manually initializes the Multiplexer, and attempts to exchange the numbers 1 to 100

# Get the Multiplexer
include Multiplexer.py

MAX_NUM = 100

# Handle a new virtual connection
def new_virtual_conn(remoteip, remoteport, virtualsock, multiplexer):
  # Wait to recieve hi
  data = virtualsock.recv(3)

  num = 1
  while True and num < MAX_NUM:
    data = virtualsock.recv(1024)
    if data == str(num):
      num = num + 1
      virtualsock.send(str(num))
      num = num + 1
    else:
      print "Unexpected number! Expected: ", str(num), " Received: ",data


# Handle a new client connecting to us
def new_connection(remoteip, remoteport, socket, thiscommhandle, listencommhandle):
  # Immediately create a multiplexer from this connection
  mux = Multiplexer(socket, {"localip":"127.0.0.1", "localport":12345,"remoteip":remoteip,"remoteport":remoteport,"mux":"waitforconn"})
  
  # Setup the waitforconn
  mux.waitforconn("127.0.0.1", 12345, new_virtual_conn)
  

def timeout():
  print "Reached timeout!"
  exitall()

# Kill us in 20 seconds
settimer(10, timeout,())

# Setup a waitforconn on a real socket
waitforconn("127.0.0.1", 12345, new_connection)

# Try to connect to the real socket
realsocket = openconn("127.0.0.1", 12345)

# Try to setup a multiplexed connection on this
mux = Multiplexer(realsocket, {"remoteip":"127.0.0.1","remoteport":12345,"mux":"openconn"})

# Try to setup a virtual socket
virtualsock = mux.openconn("127.0.0.1", 12345,timeout=5)

# Send hi, wait to recieve hi back
virtualsock.send("Hi!")

num = 1
while True and num <= MAX_NUM:
  virtualsock.send(str(num))
  num = num + 1
  data = virtualsock.recv(1024)
  if data == str(num):
    num = num + 1
  else:
    print "Unexpected number! Expected: ", str(num), " Received: ",data


exitall()