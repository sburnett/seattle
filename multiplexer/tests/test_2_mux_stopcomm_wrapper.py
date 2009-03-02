# This test tries to use mux_waitforconn and mux_openconn.
# Once connected, mux_stopcomm is called.
# It then attempts to exchange the numbers 1 to 100
# Finally, a new client attempts to connect, this is expected to fail with connection refused

# Get the Multiplexer
include Multiplexer.py

MAX_NUM = 50

# Handle a new virtual connection
def new_virtual_conn(remoteip, remoteport, virtualsock, junk, multiplexer):
  # Stop listening for new connections
  mux_stopcomm(mycontext["handle"])
  
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

def timeout():
  print "Reached timeout!"
  exitall()

if callfunc=='initialize':
  # Kill us in 15 seconds
  settimer(15, timeout,())

  # Setup a waitforconn on a real socket
  handle = mux_waitforconn("127.0.0.1", 12345, new_virtual_conn)

  # Save the handle
  mycontext["handle"] = handle

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
  
  # Try to connect, we should get connection refused
  try:
    virtualsock2 = mux_openconn("127.0.0.1", 12345)
  except EnvironmentError, err:
    if not "Connection Refused!" == str(err):
      print "Unexpected error. Expected Connection Refused. Got: ",str(err)
  else:
    print "Expected Connection Refused! Successfully created socket!"

  exitall()