include NATLayer.py

# This test just attempts to create a NATConnection object, which should connect to the forwarder
# as the server. Then it creates a second NATConnection object which should be a client (to the same server)

# The client will send the server "1", server replies "2", this is repeated until 100

# There is no expected output

if callfunc == "initialize":
  serverMac = "234567234567"
  clientMac = "765432765432"
  
  natcon = NATConnection(serverMac, "127.0.0.1", 12345)
  natcon.initServerConnection()

  natcon2 = NATConnection(clientMac, "127.0.0.1", 12345)
  clientSock = natcon2.initClientConnection(serverMac)
  
  num = 1
  first = True
  
  while True:
    # Check the server response (after the first time)
    if not first:
      serverMesg = clientSock.recv(1024)
      if int(serverMesg) != num:
        raise Exception, "Unexpected Message! Expected: " + str(num) + " Received: " + serverMesg
      else:
        num = num + 1
    
    # Send a number to the server    
    clientSock.send(str(num))

    # Server gets the same number, from expected client
    (fromMac, mesg) = natcon.recvTuple()
    if fromMac != clientMac:
      raise Exception, "Unexpected Client Mac! Expected: "+ clientMac + " Received: " + fromMac
    
    if int(mesg) != num:
      raise Exception, "Unexpected Message! Expected: " + str(num) + " Received: " + mesg
  
    # Only go to 100
    if int(mesg) == 100:
      break
    else:
      # Reply to the message
      num + 1
      natcon.send(clientMac, str(num))
    
    # This signals that the client should check our response
    first=False
      
  natcon2.close()
  natcon.close()