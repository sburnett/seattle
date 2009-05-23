# This test tries to use waitforconn and openconn from repy to get a real socket.
# It then manually initializes the Multiplexer, and attempts to exchange the numbers 1 to 100

# Get the Multiplexer
include Multiplexer.py

MAX_NUM = 100

# Handle a new virtual connection
def new_virtual_conn(remoteip, remoteport, virtualsock, junk, multiplexer):
  # send 0 to 9
  for i in range(10):
    virtualsock.send(str(i))
    
  # close the sock
  virtualsock.close()  
  mycontext['sent-lock'].release()


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
  
  mycontext['sent-lock'] = getlock()
  mycontext['sent-lock'].acquire() # unlock after peer socket is closed


  # Kill us in 10 seconds
  settimer(15, timeout,())

  # Setup a waitforconn on a real socket
  waitforconn("127.0.0.1", 12345, new_connection)

  # Try to connect to the real socket
  realsocket = openconn("127.0.0.1", 12345)

  # Try to setup a multiplexed connection on this
  mux = Multiplexer(realsocket, {"remoteip":"127.0.0.1","remoteport":12345,"mux":"openconn"})


  # Try to setup a virtual socket
  virtualsock = mux.openconn("127.0.0.1", 12345,timeout=5)

  # ensure the peer socket is closed
  mycontext['sent-lock'].acquire()
  mycontext['sent-lock'].release()

  sleep(1) # be sure the close has propigated

  # read the data
  for i in range(10):
    try:
      data = virtualsock.recv(1)
    except Exception, e:
      print 'Exception '+str(e)
      raise
    
    


  virtualsock.close()
    
  exitall()
