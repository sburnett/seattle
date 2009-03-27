# This test tries to check error delegation for the functional wrappers

# Get the Multiplexer
include Multiplexer.py

# Handle a new virtual connection
def new_virtual_conn(remoteip, remoteport, virtualsock, junk, multiplexer):
  try:
    # Wait to recieve hi
    data = virtualsock.recv(3)
  except:
    mycontext["fail2"] = True

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
  mycontext["fail1"] = False
  mycontext["fail2"] = False
  
  # Setup a waitforconn on a real socket
  waitforconn("127.0.0.1", 12345, new_connection)

  # Try to connect to the real socket
  realsocket = openconn("127.0.0.1", 12345)

  # Try to setup a multiplexed connection on this
  mux = Multiplexer(realsocket, {"remoteip":"127.0.0.1","remoteport":12345,"mux":"openconn"})

  # Try to setup a virtual socket
  virtualsock = mux.openconn("127.0.0.1", 12345,timeout=5)

  # Try closing the real socket
  realsocket.close()
  
  # Send hi, wait to recieve hi back
  try:
    virtualsock.send("Hi!")
  except:
    mycontext["fail1"] = True
  
  sleep(2)
  
  if not mycontext["fail1"]:
    print "Client was able to send data after a closed socket!"
    
  if not mycontext["fail2"]:
    print "Server was able to receive data after a closed socket!"

  exitall()