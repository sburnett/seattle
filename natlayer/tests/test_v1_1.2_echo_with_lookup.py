include NATLayer_rpc.repy

# This test connects a server to a forwarder and uses waitforconn
# Then it is tested to make sure it works properly with 1 client.

# Then numbers 1-50 are exchanged

# There is no expected output

serverMac = "FFFFFFFFFFFE"
clientMac1 = "FFFFFFFFFFFD"


# The test will be forced to exit after this many seconds
# This is necessary since client 3 is expected to block indefinately
TIME_LIMIT = 30

def new_client(remoteip, remoteport, socketlikeobj, commhandle, thisnatcon):
  # Increment the client connected count
 
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
  




# run the test!
if callfunc == "initialize":
  
  
  #mycontext['forwarderip'] = '128.208.1.138'  # attu
  mycontext['forwarderip']= getmyip()       #local

  # Create server connection, force local forwarder
  whandle = nat_waitforconn(serverMac, 10000, new_client) 
  
  sleep(2) # time for the advertisement to take place

  # Setup client sockets, force use of local forwarder for the tests
  clientsock1 = nat_openconn(serverMac, 10000)

  # Setup timer to kill us if we exceed our time limit
  handle = settimer(TIME_LIMIT, long_execution, ())
  
  # Try to connect client 1+2
  client_message(clientsock1, 50)

  # Quit even if any threads are left
  exitall()
