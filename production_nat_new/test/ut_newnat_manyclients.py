"""
Several clients connect to a server 

"""
#pragma repy restrictions.normal

include ShimStack.repy
include NullShim.repy
include NatForwardingShim.repy


TEST_3_NUMBER_OF_CLIENTS = 4
LOCK = getlock()

def response(remote_ip,remote_port,sock,th,listenhandle):
  sock.send('A')
  sock.close()


def client_thread(client_shim):
  sock = client_shim.openconn(serverkey,12347)
  msg = sock.recv(1)
  sock.close()
  if msg != 'A':
    raise Exception("got wrong message in client thread: "+msg)
  LOCK.acquire()
  mycontext['threads_done'] = mycontext['threads_done'] +1 
  LOCK.release()

if callfunc == 'initialize':
  
  serverkey = 'NAT$BLAHBLAHBLAH'
  mycontext['threads_done'] = 0
  ip = '127.0.0.1'
  port = 12345

  server_shim = ShimStack('(NatForwardingShim,'+ip+','+str(port)+')(NullShim)')

  handle = server_shim.waitforconn(serverkey,12347,response)


  
  sleep(.2)
  
  # create several virtual clients
  client_shims = []
  for i in range(TEST_3_NUMBER_OF_CLIENTS):
    client_shims.append(ShimStack('(NatForwardingShim,'+ip+','+str(port)+')(NullShim)'))
  
  for client_shim in client_shims:
    settimer(0,client_thread,[client_shim])
  
  #stop here until all threads are done
  while mycontext['threads_done'] < TEST_3_NUMBER_OF_CLIENTS:
    sleep(1)

  # do the stopcomm
  server_shim.stopcomm(handle)

