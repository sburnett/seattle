"""
lookups are used

a server registers two callbacks

4 clients connect to each callback

"""

#pragma repy restrictions.normal

include ShimStack.repy
include NullShim.repy
include NatForwardingShim.repy



TEST_5_NUMBER_OF_CLIENTS= 4
LOCK = getlock()

def response1(remote_ip,remote_port,sock,th,listenhandle):
  sock.send('1')
  sock.close()

def response2(remote_ip,remote_port,sock,th,listenhandle):
  sock.send('2')
  sock.close()


if callfunc == 'initialize':
  
  serverkey = 'TEST_12_SERVER'+str(getruntime()) #for unqiueness
  

  # set up multiple server shims
  server_shim = ShimStack('(NatForwardingShim)(NullShim)')


  # do the waitforconns
  handle1 = server_shim.waitforconn(serverkey,12347,response1)
  handle2 = server_shim.waitforconn(serverkey,12348,response2)

  
  sleep(20) # need time for advertisements to occur
  
  # create many clients
  client_shims = []
  for i in range(TEST_5_NUMBER_OF_CLIENTS):
    client_shims.append(ShimStack('(NatForwardingShim)(NullShim)'))
  


  # for each client openconn to each callback
  socks1 = []
  socks2 = []
  for i in range(TEST_5_NUMBER_OF_CLIENTS):
    socks1.append(client_shims[i].openconn(serverkey,12347))
    socks2.append(client_shims[i].openconn(serverkey,12348))
  

  # check connection on each sock
  for sock in socks1:
    msg = sock.recv(1)
    sock.close()
    if msg != '1': raise Exception("bad message recv: "+msg)
  for sock in socks2:
    msg = sock.recv(1)
    sock.close()
    if msg != '2': raise Exception("bad message recv: "+msg)




  # do all the stopcomms
  server_shim.stopcomm(handle1)
  server_shim.stopcomm(handle2)
