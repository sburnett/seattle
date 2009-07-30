include NATLayer_rpc.repy

# This test connects 2 servers to a forwarder and uses waitforconn
# Then it is tested to make sure a client can talk to two servers via
# the same forwarder.

# Then numbers 1-50 are exchanged

# There is no expected output

serverMac1 =  "SERVER111111"
serverMac2 =  "SERVER222222"


# The test will be forced to exit after this many seconds
# This is necessary since client 3 is expected to block indefinately
TIME_LIMIT = 15

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
def client_message(socket, stop,client_done):
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

  # mark the client as done
  mycontext[client_done] = True

# This is called if the test is taking too long
def long_execution():
  print "Execution exceeded "+str(TIME_LIMIT)+" seconds!"
  exitall()
  




# run the test!
if callfunc == "initialize":
  

  
  #mycontext['forwarderip'] = '128.208.1.138'  # attu
  mycontext['forwarderip']= getmyip()       #local


  mycontext['client1_done'] = False

  # Create server connection
  nat_waitforconn(serverMac1, 10000, new_client, 
                              mycontext['forwarderip'], 12345,23456)

  nat_waitforconn(serverMac2, 20000, new_client, 
                              mycontext['forwarderip'], 12345,23456) 
  
  # Setup client sockets
  clientsock1 = nat_openconn(serverMac1, 10000,
             forwarderIP=mycontext['forwarderip'],forwarderPort=12345)
  clientsock2 = nat_openconn(serverMac2, 20000, 
             forwarderIP=mycontext['forwarderip'],forwarderPort=12345)

  # Setup timer to kill us if we exceed our time limit
  handle = settimer(TIME_LIMIT, long_execution, ())
  
  # launch client 1 in .1 seconds
  settimer(0.1,client_message,(clientsock1, 50,'client1_done'))
 
  # launch client 2 now
  settimer(0,client_message,(clientsock2,50,'client2_done'))

  # wait for both clients to finish
  while not (mycontext['client1_done'] and mycontext['client2_done']):
    sleep(.5)
  
  # exit the test
  exitall()
