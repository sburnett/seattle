# This test tries to use waitforconn and openconn from repy to get a real socket.
# It then manually initializes the Multiplexer, and attempts to exchange "Hi!" once.

# Get the Multiplexer
include Multiplexer.py

# Handle a new virtual connection
def new_virtual_conn(remoteip, remoteport, virtualsock, junk, multiplexer):
  # Wait to recieve hi
  data = virtualsock.recv(3)

  if data != "Hi!":
    print "Server. Recieved unexpected response! Expected Hi!  Received:  ",data
  else:
    if mycontext["send"]:
      # Send hi back
      virtualsock.send("Hi!")
      mycontext["send"] = False
    else:
      print "Recieved data before any sent!"


# Handle a new client connecting to us
def new_connection(remoteip, remoteport, socket, thiscommhandle, listencommhandle):
  # Immediately create a multiplexer from this connection
  mux = Multiplexer(socket, {"localip":"127.0.0.1", "localport":12345,"remoteip":remoteip,"remoteport":remoteport,"mux":"waitforconn"})
  
  # Setup the waitforconn
  mux.waitforconn("127.0.0.1", 12345, new_virtual_conn)
  

def timeout():
  print "Reached timeout!"
  exitall()

if callfunc=='initialize':
  # Kill us in 20 seconds
  settimer(10, timeout,())
  mycontext["send"] = False

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
  mycontext["send"] = True
  data = virtualsock.recv(3)

  if data != "Hi!":
    print "Client. Recieved unexpected response! Expected Hi!  Received:  ",data

  exitall()