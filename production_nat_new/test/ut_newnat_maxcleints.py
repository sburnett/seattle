"""
The max number of clients + 1 tries to connect to a single server
The last one should not be allowed to connect

"""

#pragma repy restrictions.normal

include ShimStack.repy
include NullShim.repy
include NatForwardingShim.repy


TEST_9_NUMBER_OF_CLIENTS = 5
LOCK = getlock()

def response(remote_ip,remote_port,sock,th,listenhandle):
  sock.send('A')
  


def client_thread(client_shim):
  try:
    sock = client_shim.openconn(serverkey,12347)
    mycontext['socks'].append(sock)
  except NatConnError:
    LOCK.acquire()
    mycontext['failed_clients'] +=1
    mycontext['threads_done'] +=1
    LOCK.release()
    return

  msg = sock.recv(1)
  if msg != 'A':
    raise Exception("got wrong message in client thread: "+msg)
  LOCK.acquire()
  mycontext['threads_done'] = mycontext['threads_done'] +1 
  LOCK.release()
  return True

if callfunc == 'initialize':
  
  serverkey = 'NAT$BLAHBLAHBLAH'
  mycontext['threads_done'] = 0
  mycontext['failed_clients'] = 0
  mycontext['socks'] = []
  ip = '127.0.0.1'
  port = 12345

  server_shim = ShimStack('(NatForwardingShim,'+ip+','+str(port)+')(NullShim)')

  handle = server_shim.waitforconn(serverkey,12347,response)


  
  sleep(.2)
  
  # create several virtual clients
  client_shims = []
  for i in range(TEST_9_NUMBER_OF_CLIENTS):
    client_shims.append(ShimStack('(NatForwardingShim,'+ip+','+str(port)+')(NullShim)'))
  
  for client_shim in client_shims:
    settimer(0,client_thread,[client_shim])
  
  #stop here until all threads are done
  while mycontext['threads_done'] < TEST_9_NUMBER_OF_CLIENTS:
    sleep(1)

  # close all the clients
  for sock in mycontext['socks']:
    sock.close()

  if mycontext['failed_clients'] != 1:
    raise Exception("Failed number of clients is wrong: "+str(mycontext['failed_clients']))


  # make sure a client can connect again
  if not client_thread(client_shim):
    raise Exception("Client cant connection after dropping some connections")


  # do the stopcomm
  server_shim.stopcomm(handle)

  

  
