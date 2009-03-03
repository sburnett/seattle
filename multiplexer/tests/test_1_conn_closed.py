# This test tries to use waitforconn and openconn from repy to get a real socket.
# It then manually initializes the Multiplexer, and attempts to exchange the numbers 1 to 100
# The socket is closed in the process, so the server should get a connection closed message.

# Get the Multiplexer
include Multiplexer.py

MAX_NUM = 50

# Handle a new virtual connection
def new_virtual_conn(remoteip, remoteport, virtualsock, junk, multiplexer):
  # Exchange 1 to 100
  num = 1
  try:
    while True:
      data = virtualsock.recv(1024)
      if data == str(num):
        num = num + 1
        virtualsock.send(str(num))
        num = num + 1
      else:
        print "Unexpected number! Expected: ", str(num), " Received: ",data
  except EnvironmentError,e:
    # This is expected
    if not str(e) == "The socket has been closed!":
      print "Unexpected Exception. Should get socket closed. Got:",str(e)
          
  else:
    print "Server should have received EnvironmentError, closed connection."
  
  virtualsock.close()
  exitall()  

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
  # Kill us in 15 seconds
  settimer(15, timeout,())

  # Setup a waitforconn on a real socket
  waitforconn("127.0.0.1", 12345, new_connection)

  # Try to connect to the real socket
  realsocket = openconn("127.0.0.1", 12345)

  # Try to setup a multiplexed connection on this
  mux = Multiplexer(realsocket, {"remoteip":"127.0.0.1","remoteport":12345,"mux":"openconn"})

  # Try to setup a virtual socket
  virtualsock = mux.openconn("127.0.0.1", 12345,timeout=5)

  # Try to exchange 1 to 100
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