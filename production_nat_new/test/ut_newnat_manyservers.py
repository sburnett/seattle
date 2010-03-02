"""

many servers connect to one forwrader

"""
#pragma repy restrictions.normal

include ShimStack.repy
include NullShim.repy
include NatForwardingShim.repy

# uses ports 12347,...12347+TEST_4_NUMBER_OF_SERVERS -1

TEST_4_NUMBER_OF_SERVERS = 5
LOCK = getlock()

def response(remote_ip,remote_port,sock,th,listenhandle):
  sock.send('$')
  sock.close()


if callfunc == 'initialize':
  
  serverkey = 'SERVER'
  ip = '127.0.0.1'
  port = 12345



  # set up multiple server shims
  server_shim_list = []
  for i in range(TEST_4_NUMBER_OF_SERVERS):
    server_shim_list.append(ShimStack('(NatForwardingShim,'+ip+','+str(port)+')(NullShim)'))


  # do the waitforconns
  handles = []
  for i in range(TEST_4_NUMBER_OF_SERVERS):
    handles.append(server_shim_list[i].waitforconn(serverkey+str(i+1),12347+i,response))

  
  sleep(.2)
  
  # create a single client
  client_shim = ShimStack('(NatForwardingShim,'+ip+','+str(port)+')(NullShim)')
  
  # do an openconn to each server
  socks = []
  for i in range(TEST_4_NUMBER_OF_SERVERS):
    socks.append(client_shim.openconn(serverkey+str(i+1),12347+i))
  
  # check connection on eachsock
  for sock in socks:
    msg = sock.recv(1)
    if msg != '$': raise Exception("bad message recv: "+msg)


  # do all the stopcomms
  for i in range(TEST_4_NUMBER_OF_SERVERS):
    server_shim_list[i].stopcomm(handles[i])
