# This test tries to use mux_waitforconn and mux_openconn.
# This has 2 servers, each connected to by 1 client.
# It then attempts to exchange the numbers 1 to MESG_LIMIT
# This is a long test, and it can take up to 70 seconds

# This seems to be CPU bound, e.g. there is an almost linear
# increase in the number of messages you can send as you increase
# CPU limit, lets assume 35 messages a second minimum

# Get the Multiplexer
include Multiplexer.py

# Adjust this on a per-system basis if necessary
# Run speed_benchmark on restrictions.default to get a reasonable idea
MIN_RATE = 20 

RUN_TIME = 60 # Desired run-time

MESG_LIMT = round(0.90* RUN_TIME*MIN_RATE)

printlock = getlock()

# Handle a new virtual connection
def new_virtual_conn(remoteip, remoteport, virtualsock, junk, multiplexer):
  # Exchange 1 to MESG_LIMT
  num = 1
  while True and num < MESG_LIMT:
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

  # Try to exchange 1 to MESG_LIMT
  num = 1
  while True and num <= MESG_LIMT:
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
  
  # Kill us in 70 seconds
  settimer(RUN_TIME+20, timeout,())

  # The following looks weird because Im trying to use 2 multiplexers
  # Rather than 4. If you do waitforconn on both ports first,
  # Then openconn, you end up with 4 ports used, and 4 muxes

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

  # Wait for a while
  sleep(RUN_TIME+10)

  # Get the lock incase we need to print
  printlock.acquire()

  # Check that they all registered and finished
  if not 1 in mycontext or not mycontext[1]:
    print "Client 1 failed to finish!"

  if not 2 in mycontext or not mycontext[2]:
    print "Client 2 failed to finish!"


  exitall()