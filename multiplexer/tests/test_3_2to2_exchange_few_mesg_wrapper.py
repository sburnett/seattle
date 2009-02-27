# This test tries to use mux_waitforconn and mux_openconn.
# This has 2 servers, each connected to by 1 client.
# It then attempts to exchange the numbers 1 to 100

# Get the Multiplexer
include Multiplexer.py

MAX_NUM = 100
printlock = getlock()

# Handle a new virtual connection
def new_virtual_conn(remoteip, remoteport, virtualsock, junk, multiplexer):
  # Exchange 1 to 100
  num = 1
  while True and num < MAX_NUM:
    data = virtualsock.recv(1024)
    if data == str(num):
      num = num + 1
      virtualsock.send(str(num))
      num = num + 1
    else:
      printlock.acquire()
      print "Serv. Unexpected number! Expected: ", str(num), " Received: ",data
      printlock.release()

  # Sleep a second before closing the socket
  sleep(1)
  virtualsock.close()

def client_exchange(clientn,port,local):
  # Try to connect to the other multiplexer
  try:
    virtualsock = mux_openconn("127.0.0.1", port,"127.0.0.1",local)
  except Exception, e:
    print e
    print "Failed to open virtual socket! Client:",clientn,"Port:",port,"From:",local
    exitall()

  # Try to exchange 1 to 10
  num = 1
  while True and num <= MAX_NUM:
    virtualsock.send(str(num))
    num = num + 1
    data = virtualsock.recv(1024)
    if data == str(num):
      num = num + 1
    else:
      printlock.acquire()
      print "Client.",clientn,"Unexpected number! Expected: ", str(num), " Received: ",data
      printlock.release()
  
  virtualsock.close()
  
  # This finished...
  mycontext[clientn] = True

def timeout():
  print "Reached timeout!"
  exitall()

if callfunc=='initialize':
  # Kill us in 30 seconds
  settimer(30, timeout,())

  # Setup a waitforconn
  mux_waitforconn("127.0.0.1", 12345, new_virtual_conn)

  # Trigger two clients
  settimer(0,client_exchange,[1,12345,20000])

  # Wait before calling waitforconn
  sleep(5)

  # Setup second waitforconn
  mux_waitforconn("127.0.0.1", 20000, new_virtual_conn)

  # Setup second client
  settimer(1,client_exchange,[2,20000,None])

  # Wait for a few seconds
  sleep(20)

  # Get the lock incase we need to print
  printlock.acquire()

  # Check that they all registered and finished
  if not 1 in mycontext or not mycontext[1]:
    print "Client 1 failed to finish!"

  if not 2 in mycontext or not mycontext[2]:
    print "Client 2 failed to finish!"


  exitall()