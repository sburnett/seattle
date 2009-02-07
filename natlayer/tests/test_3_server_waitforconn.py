include NATLayer.py

# This test connects a server to a forwarder and uses waitforconn
# Then it is tested to make sure it works properly with 3 clients.
# Then numbers 1-50 are exchanged

# There is no expected output

serverMac = "999999999999"
clientMac1 = "888888888888"
clientMac2 = "777777777777"
clientMac3 = "666666666666"

# The test will be forced to fail after this many seconds
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
          break
        
  else:
    raise Exception, "Unexpected client connected! "+remotemac  
  
def client_message(socket):
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
        
    # Send a number to the server    
    socket.send(str(num))
    
    # Expect a larger number
    num = num + 1
    
    # Break now
    first = False
    
    # Break at 50
    if int(serverMesg) == 50:
      break
  
  # Close the socket
  socket.close()

# This is called if the test is taking too long
def long_execution():
  print "Execution exceeded "+str(TIME_LIMIT)+" seconds!"
  exitall()

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
  
  clientnat3 = NATConnection(clientMac3, "127.0.0.1", 12345)
  clientsock3 = clientnat3.initClientConnection(serverMac)
  
  # Setup timer to kill us if we exceed our time limit
  handle = settimer(TIME_LIMIT, long_execution, ())
  
  # Try to connect each client
  client_message(clientsock1)
  clientnat1.close()
  
  client_message(clientsock2)
  clientnat2.close()
  
  client_message(clientsock3)
  clientnat3.close()
   
  # Close the server connection
  natcon.close()
  
  # Make sure everybody has connected by now
  if not mycontext[clientMac1]:
    raise Exception, clientMac1+" failed to connect to the server!"
    
  if not mycontext[clientMac2]:
    raise Exception, clientMac2+" failed to connect to the server!"
    
  if not mycontext[clientMac3]:
    raise Exception, clientMac3+" failed to connect to the server!"

  # We are successful, so stop the timer
  canceltimer(handle)
  
  # Quit even if any threads are left
  exitall()