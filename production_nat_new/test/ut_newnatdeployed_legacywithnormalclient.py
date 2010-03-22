"""
One server connects to a deployed forwarder
One legacy client connects to the server
One new client connects to the server

A few messages are exchanged

"""

#pragma repy restrictions.normal

include NatForwardingShim.repy
include NATLayer_rpc.repy



def response(remote_ip,remote_port,sock,th,listenhandle):
  try:
    while True:
      msg = sock.recv(1024)
      sock.send('got'+msg)
  except:
     sock.close()


if callfunc == 'initialize':
  
  serverkey = 'NAT$BLAHBLAHBLAH'

  ip = '127.0.0.1'
  port = 12345

  # use the nat shim
  server_shim = ShimStack('(NatForwardingShim)(NullShim)')

  handle = server_shim.waitforconn(serverkey,12347,response)


  sleep(10) # need to sleep while the value is advertised

  # CLIENT LOGIC
  
  # open connection using the legacy client
  # manually enter the forwarder info
  
  
  
  
  legacy_sock = nat_openconn(serverkey, 12347)

  
     
  #client_shim = ShimStack('(NatForwardingShim)(NullShim)')
  #sock = client_shim.openconn(serverkey,12347)
  sock = nat_openconn(serverkey, 12347)
 
  
  for i in range(10):
    legacy_sock.send(str(i))
    sock.send(str(i)) 
    legacy_msg = legacy_sock.recv(10)
    msg1 = sock.recv(10)
    if msg1 != 'got'+str(i):
      print 'GOT WRONG MSG FROM SHIM SOCK'
    elif legacy_msg != 'got'+str(i):
      print 'GOT WRONG MSG FROM LEGACY SOCK'
    
  
  legacy_sock.close()
  sock.close()
  exitall()


