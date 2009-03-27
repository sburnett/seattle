# This test tries to use mux_waitforconn and mux_openconn. It has 3 clients connecting to 1 server.
# After the first client connects, the server severs the underlying socket.

# Get the Multiplexer
include Multiplexer.py

MAX_NUM = 50

# Handle a new virtual connection
def new_virtual_conn(remoteip, remoteport, virtualsock, junk, multiplexer):
  mycontext["client"] += 1
  
  # Close the link for the first client
  if mycontext["client"] == 1:
    multiplexer.socket.close()
    
  # Exchange 1 to 100
  try:
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
  except EnvironmentError, err:
    if mycontext["client"] == 1 and str(err) == "The socket has been closed!":
      # This is expected
      pass
    else:
      print "Server Unexpected err:",err
      raise err
      exitall()

def client_exchange(clientn):
  try:
    # Try to connect to the other multiplexer
    virtualsock = mux_openconn("127.0.0.1", 12345,timeout=5)

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
  
    # This finished...
    mycontext[clientn] = True
    
  except EnvironmentError, err:
    if clientn == 1 and str(err) == "The socket has been closed!":
      # This is expected
      pass
    else:
      print "Client Unexpected Error",clientn,err
      raise err
        
  except Exception, err:
    print "Client Unexpected Error",clientn,err
    raise err
    exitall()  

def timeout():
  print "Reached timeout!"
  exitall()

def intercept_error(mux, errloc, excep):
  # Increment the error count
  mycontext["errcount"] += 1
  
  # Check the length of the MULTIPLEXER_OBJECTS
  prior = len(MULTIPLEXER_OBJECTS)
  
  # Call the default delegate
  original = mycontext["origErrorDelegate"]
  original(mux, errloc, excep)
  
  # Check the length of the MULTIPLEXER_OBJECTS
  post = len(MULTIPLEXER_OBJECTS)
  
  # Check if 2 mux's were removed
  if prior-1 == post:
    # Save the result
    mycontext[4] = (prior, post)
  
  else:
    # Save the failure as 5
    mycontext[5] = (prior, post)
  
if callfunc=='initialize':
  # Client num
  mycontext["client"] = 0
  mycontext["errcount"] = 0
  mycontext["origErrorDelegate"] = MULTIPLEXER_FUNCTIONS["errdelegate"] # Store the original delegate
  
  # Kill us in 25 seconds
  settimer(15, timeout,())
  
  # Override the builtin error delegate
  MULTIPLEXER_FUNCTIONS["errdelegate"] = intercept_error

  # Setup a waitforconn on a real socket
  mux_waitforconn("127.0.0.1", 12345, new_virtual_conn)

  # Trigger three clients
  settimer(0,client_exchange,[1])

  settimer(3,client_exchange,[2])

  settimer(6,client_exchange,[3])

  # Wait for a few seconds
  sleep(12)

  # Check that they all registered and finished
  if 1 in mycontext and mycontext[1]:
    print "Client 1 finished after a closed socket!"

  if not 2 in mycontext or not mycontext[2]:
    print "Client 2 failed to finish!"

  if not 3 in mycontext or not mycontext[3]:
    print "Client 3 failed to finish!"
  
  if not 4 in mycontext:
    print "Error Delegation not properly handled. Pre:",mycontext[5][0],"Post:",mycontext[5][1]
  
  if not mycontext["errcount"] >= 2:
    print "Expected at least 2 errors. Got:",mycontext["errcount"]
  
  if not mycontext["client"] == 3:
    print mycontext["client"],"Clients were able to connect. 3 expected."
  
  exitall()