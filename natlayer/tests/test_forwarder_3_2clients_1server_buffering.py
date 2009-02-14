include NATLayer.py

#
# Test the seneraio where one client is sending large amounts
# of data that the server is reading slowly, while the server is
# also trying to communicate with another client

# the buffer size is set very small test cases where buffers are full


#the servers method to handle clients
def new_client(remotemac, natsocket, thisnatcon):

  # slowly read the loudmoth client 
  if remotemac=="LOUDMOUTH___":
    while True:
      data=natsocket.recv(1024)
      if len(data) !=10:
        print "recieved unexpected message size form loud client"
      sleep(.5)
 
  # handle the number echoing from the good client
  else:
    while True:
      num = int(natsocket.recv(1024))
      num +=1
      natsocket.send(str(num))


#send messages as fast as we can
def talksAlot(socket,natcon):
  while True:
  
    # this socket times out
    try:
      socket.send("heyheyheyheyheyheyhey")    
    except Exception, e:
      if 'socket.timeout' not in str(type(e)):
        raise

def sendNumbers(socket,natcon):
  num = 0
  for i in range(50):
    socket.send(str(num))
    new_num = int(socket.recv(1024))
    if new_num != num+1:
      print "Recieved incorrect response from server expected: "+str(num+1)+" actual: "+str(new_num)
    num = new_num 

   
  # if this loop was exited we got all response back, the test passed
  stop_test()


def stop_test(out=None):
  if out is not None:
    print out
  good_client_natcon.close()
  bad_client_natcon.close()
  server_natcon.close()
  exitall()

if callfunc == "initialize":
  serverMac = "SERVER______"
  goodClient = "GOODCLIENT__"
  badClient = "LOUDMOUTH___"


  server_natcon = NATConnection(serverMac, "127.0.0.1", 12345)
  server_natcon.initServerConnection(10)
  server_natcon.waitforconn(new_client)
  
  good_client_natcon = NATConnection(goodClient, "127.0.0.1", 12345)
  good_clientSock = good_client_natcon.initClientConnection(serverMac)
  
  bad_client_natcon = NATConnection(badClient, "127.0.0.1", 12345)
  bad_clientSock = bad_client_natcon.initClientConnection(serverMac)


  settimer(0,talksAlot,[bad_clientSock,bad_client_natcon])
  settimer(0,sendNumbers,[good_clientSock,good_client_natcon])


  #test times out in 30 seconds
  timer = settimer(30,stop_test,['test timed out'])


  
