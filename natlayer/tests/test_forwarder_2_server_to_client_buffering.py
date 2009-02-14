include NATLayer.py

# Test buffering of data flowing form server to client
#
# Tests that a client can recieve data even if it has never sent data
# to the server
#
# This tests sets a low default buffer size (10)
# The server then sends a string of length 100
#
# If buffering is working correctly the client will see strings 10 strings
# of length 10.
#



def new_client(remotemac, natsocket, thisnatcon):
 
  # create a large string to send
  long_str =''
  for x in range(100):
    long_str+='1'
  
  
  #attempt to send more the data
  natsocket.send(long_str)
  
 


def stop_test(out=None):
  if out is not None:
    print out
  client_natcon.close()
  server_natcon.close()

if callfunc == "initialize":
  serverMac = "SERVER______"
  clientMac = "CLINET______"
  

  server_natcon = NATConnection(serverMac, "127.0.0.1", 12345)
  server_natcon.initServerConnection(10)
  server_natcon.waitforconn(new_client)
  
  client_natcon = NATConnection(clientMac, "127.0.0.1", 12345)
  clientSock = client_natcon.initClientConnection(serverMac)
  

  
 
  # if the forwarder is not sending new buffer sizes as it reads data
  # this test will block, so set a timmer and report the error
  timer = settimer(10,stop_test,['test timed out'])
  count = 0

  for i in range(10):
    mesg = clientSock.recv(1024)
    if len(mesg) !=10:
      print "Error, server recieved message: "+mesg
      print "message length should be less than 10"
    else:
      count +=1


  canceltimer(timer)
  
  if count != 10:
    stop_test("Client did not recieve 10 messages") 

  stop_test()
  
