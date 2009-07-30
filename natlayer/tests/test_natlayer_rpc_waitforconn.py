include NATLayer_rpc.repy

# This test connects a server to a forwarder and uses waitforconn
# Then it is tested to make sure it works properly with 3 clients.
# However, after the second client a stopcomm is issued, so the 3rd client should not be able to connect
# Then numbers 1-50 are exchanged
# This test is based on test_4_server_stopcomm, however it uses the NATLayer function wrappers
# and avoids directly using the objects, except where necessary for the unit test

# There is no expected output

serverMac = "FFFFFFFFFFFE"
clientMac1 = "FFFFFFFFFFFD"
clientMac2 = "FFFFFFFFFFFC"
clientMac3 = "FFFFFFFFFFFB"

# The test will be forced to exit after this many seconds
# This is necessary since client 3 is expected to block indefinately
TIME_LIMIT = 30

def new_client(remoteip, remoteport, socketlikeobj, commhandle, thisnatcon):
  # Increment the client connected count
  if remoteip == getmyip():
    num = 1

    while True:
      # Check the client message
      mesg = socketlikeobj.recv(1024)

      if int(mesg) != num:
        raise Exception, "Unexpected Message! Expected: " + str(num) + " Received: " + mesg
      else:
        num = num + 1
        
        # Send a number to the server    
        socketlikeobj.send(str(num))
        
        # Expect a larger response
        num = num + 1
        
        # If we are expecting 51, break
        if num == 51:
          sleep(1)
          socketlikeobj.close()
          break
        
  else:
    raise Exception, "Unexpected client connected! "+remoteip  

# Bounced messages back and forth to server, stops when reaches "stop"  
def client_message(socket, stop=50):
  num = 1
  first = True
  serverMesg = "0"
  
  # Loop until the magic number
  while True:
    # Check the server response (after the first time)
    if not first:
      serverMesg = socket.recv(1024)
      if int(serverMesg) != num:
        raise Exception, "Unexpected Message! Expected: " + str(num) + " Received: " + serverMesg
      else:
        num = num + 1
      
      # Break at stop
      if int(serverMesg) == stop:
        break
        
    # Send a number to the server    
    socket.send(str(num))
    
    # Expect a larger number
    num = num + 1
    
    # Break now
    first = False
  
  # Close the socket
  socket.close()

# This is called if the test is taking too long
def long_execution():
  print "Execution exceeded "+str(TIME_LIMIT)+" seconds!"
  exitall()
  

if callfunc == "initialize":
  # Create server connection, force local forwarder
  whandle = nat_waitforconn(serverMac, 10000, new_client, getmyip(), 12345, 12345) 
  
  sleep(2)
  
  # Now we issue a stopcomm, so client 3 should never connect with a virtual socket
  nat_stopcomm(whandle)

  # Quit even if any threads are left
  exitall()
