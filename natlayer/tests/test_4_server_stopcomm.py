include NATLayer.py

# This test connects a server to a forwarder and uses waitforconn
# Then it is tested to make sure it works properly with 3 clients.
# However, after the second client a stopcomm is issued, so the 3rd client should not be able to connect
# Then numbers 1-50 are exchanged

# There is no expected output

serverMac = "FFFFFFFFFFFE"
clientMac1 = "FFFFFFFFFFFD"
clientMac2 = "FFFFFFFFFFFC"
clientMac3 = "FFFFFFFFFFFB"

# The test will be forced to exit after this many seconds
# This is necessary since client 3 is expected to block indefinately
TIME_LIMIT = 30

def new_client(remotemac, socketlikeobj, thisnatcon):
  # Increment the client connected count
  if remotemac == clientMac1 or remotemac == clientMac2 or remotemac == clientMac3:
    mycontext[remotemac] = True
    
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
          socketlikeobj.close()
          break
        
  else:
    raise Exception, "Unexpected client connected! "+remotemac  

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

# This is called to check that the socket still works as expected after stopcomm
def check_socket(natcon):
  # Recieve the first frame from client 3
  (fromMac, data) = natcon.recvTuple()
  
  if fromMac != clientMac3:
    raise Exception, "Unexpected Client Message! Expected: "+clientMac3+" Received: "+fromMac+" Mesg: "+data
  
  if int(data) != 1:
    raise Exception, "Unexpected Client Message! Expected: 1 Received: "+data
    
  # Reply to the client, so that it can exit  
  natcon.send(fromMac, "2")
  

if callfunc == "initialize":
  natcon = NATConnection(serverMac, "127.0.0.1", 12345)
  natcon.initServerConnection()
  natcon.waitforconn(new_client)
  
  # Setup variable for each client that should connect
  mycontext[clientMac1] = False
  mycontext[clientMac2] = False
  mycontext[clientMac3] = False

  clientnat1 = NATConnection(clientMac1, "127.0.0.1", 12345)
  clientsock1 = clientnat1.initClientConnection(serverMac)
  
  clientnat2 = NATConnection(clientMac2, "127.0.0.1", 12345)
  clientsock2 = clientnat2.initClientConnection(serverMac)
  
  # Setup timer to kill us if we exceed our time limit
  handle = settimer(TIME_LIMIT, long_execution, ())
  
  # Try to connect client 1+2
  client_message(clientsock1, 50)
  clientnat1.close()
  
  client_message(clientsock2, 50)
  clientnat2.close()
  
  # Now we issue a stopcomm, so client 3 should never connect with a virtual socket
  natcon.stopcomm()
  
  # Initialize client 3 after stopcomm
  clientnat3 = NATConnection(clientMac3, "127.0.0.1", 12345)
  clientsock3 = clientnat3.initClientConnection(serverMac)
  
  # Launch a thread to check that the socket is still operational after stopcomm
  # this just checks that one of client 3's frames got through
  settimer(1, check_socket, [natcon])
  
  # Client 3 should only get 1 reply from the server
  client_message(clientsock3,2)
  clientnat3.close()
   
  # Close the server connection
  natcon.close()
  
  # Make sure everybody has connected by now
  if not mycontext[clientMac1]:
    raise Exception, clientMac1+" failed to connect to the server!"
    
  if not mycontext[clientMac2]:
    raise Exception, clientMac2+" failed to connect to the server!"
  
  # Client 3 should NOT have connected  
  if mycontext[clientMac3]:
    raise Exception, clientMac3+" connect to the server after stopcomm was issued!"

  # Quit even if any threads are left
  exitall()