include NATLayer_rpc.repy

# This test connects the maximum number of servers to a forwarder.
# It then tests...
#   1. additional servers are rejected
#   2. if a server disconects a new server can connect


# There is no expected output

serverMac =  "SERVER-----"
serverMac2 = "SERVER----2"
MAX_CONNECTED = 5

# The test will be forced to exit after this many seconds
# This is necessary since client 3 is expected to block indefinately
TIME_LIMIT = 30

def new_client(remoteip, remoteport, socketlikeobj, commhandle, thisnatcon):
 
  #clients dont send so this should just block
  mesg = socketlikeobj.recv(1024)
  raise Exception, 'Unexpected message recieved by server: '+mesg
          
 


# This is called if the test is taking too long
def long_execution():
  print "Execution exceeded "+str(TIME_LIMIT)+" seconds!"
  exitall()
  



# run the test!
if callfunc == "initialize":
  
  #mycontext['forwarderip'] = '128.208.1.138'  # attu
  mycontext['forwarderip']= getmyip()       #local

  # a list of clients
  server_list = []


  # do open conns to fake connections for up to max servers
  for i in range(MAX_CONNECTED):
    sleep(.5)
    sock = openconn(mycontext['forwarderip'],12345)
    sock.send('S')
    server_list.append(sock) 

  try:
    # Create server connection, force local forwarder
    whandle = nat_waitforconn(serverMac, 10000, new_client, 
                             mycontext['forwarderip'], 12345,12345)    

  except Exception:
    pass # this should occur, so do nothing
  else:
    print 'No exception thrown when extra servers were connected'
    nat_stopcomm(whandle)

  

  # close a connection, wait for the forwarder check interval to pass
  # and then try to make one more connection
  server_list[0].close()
  
  sleep(15)  # sleep while waiting for the server to open new connections
  
  
  # Create server connection, force local forwarder
  whandle = nat_waitforconn(serverMac2, 10000, new_client, 
                              mycontext['forwarderip'], 12345,12345) 
  
  
  for sock in server_list:
    sock.close()

  nat_stopcomm(whandle)
  exitall()
