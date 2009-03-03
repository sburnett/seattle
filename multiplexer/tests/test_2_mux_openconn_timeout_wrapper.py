# This test tries to use mux_waitforconn and mux_openconn.
# Openconn is called with a low timout, so that is expected to timeout

# Get the Multiplexer
include Multiplexer.py

MAX_NUM = 100

# Handle a new virtual connection
def new_virtual_conn(remoteip, remoteport, virtualsock, junk, multiplexer):
  pass

def timeout():
  print "Reached timeout!"
  exitall()

if callfunc=='initialize':
  # Kill us in 10 seconds
  settimer(10, timeout,())

  # Setup a waitforconn on a real socket
  mux_waitforconn("127.0.0.1", 12345, new_virtual_conn)

  # Try to connect to the other multiplexer
  try:
    virtualsock = mux_openconn("127.0.0.1", 12345,timeout=0.01)
  except EnvironmentError,e:
    if str(e) != "Connection timed out!":
      print "Unexpected exception,expected timeout. Got:",e
  else:
    print "Expected timeout. Was able to open socket!"

  exitall()