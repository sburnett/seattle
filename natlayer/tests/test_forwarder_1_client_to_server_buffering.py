include NATLayer.py

# Test buffering of data flowing form client to server
#
# This tests sets a low default buffer size (10)
# The client then sends a string of length 100
#
# If buffering is working correctly the server will only see strings
# of length 10.
#
# This also tests the server, requireing it to send new CON_BUFF_SIZE messages
# whenever it can recieve more data


def new_client(remotemac, natsocket, thisnatcon):
  
  # if the server is not sending new buffer sizes as it reads data
  # this test will block, so set a timmer and report the error
  timer = settimer(20,stop_test,['test timed out'])

  count = 0

  for i in range(10):
    mesg = natsocket.recv(1024)
    if len(mesg) !=10:
      print "Error, server recieved message: "+mesg
      print "message length should be 10"
    else:
      count +=1
  
  
  canceltimer(timer)
  
  if count != 10:
    stop_test("Not all messages were recieved by server")

  stop_test()


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
  
  # create a large string to send
  long_str =''
  for x in range(100):
    long_str+='1'
  
  #attempt to send more the data
  clientSock.send(long_str)
  
  
 

 
 
  
