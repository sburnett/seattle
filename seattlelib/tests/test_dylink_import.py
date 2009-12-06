"""
Author: Armon Dadgar
Description:
  This test checks that the dylink import methods are working properly by importing
  the sockettimeout library. We then check that the functions work.

  This test uses import_module.
"""

# Import the sockettimeout library as timeout
timeout = dyn_import_module("sockettimeout")

def new_conn(ip,port,sock,ch1,ch2):
  # Wait 3 seconds, then send data
  sleep(2)
  sock.send("Ping! Ping!")
  sock.close()

if callfunc == "initialize":
  # Check that we have the basic openconn,waitforconn and stopcomm
  # This will throw an Attribute error if these are not set
  check = timeout.timeout_openconn
  check = timeout.timeout_waitforconn
  check = timeout.timeout_stopcomm

  # Check that the module's name is set
  if timeout._name is not "sockettimeout":
    print "Module name is incorrect! It is: ",timeout._name

  # Get our ip
  ip = getmyip()
  port = 12345

  # Setup a waitforconn
  waith = timeout.timeout_waitforconn(ip,port,new_conn)

  # Try to do a timeout openconn
  sock = timeout.timeout_openconn(ip,port,timeout=2)

  # Set the timeout to 1 seconds, and try to read
  sock.settimeout(1)
  try:
    data = sock.recv(16)

    # We should timeout
    print "Bad! Got data: ",data
  except:
    pass

  # Close the socket, and shutdown
  sock.close()
  timeout.timeout_stopcomm(waith)

  

