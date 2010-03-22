"""
One server connects to a local forwarder
One legacy client connects to the server
A few messages are exchanged

"""

#pragma repy restrictions.normal

include NatForwardingShim.repy
include NATLayer_rpc.repy



def response(remote_ip,remote_port,sock,th,listenhandle):
  try:
    while True:
      msg = sock.recv(1024)
      sock.send('got it')
  except:
     sock.close()


if callfunc == 'initialize':
  
  serverkey = 'NAT$BLAHBLAHBLAH'

  ip = '127.0.0.1'
  port = 12345

  # use the nat shim
  server_shim = ShimStack('(NatForwardingShim,'+ip+','+str(port)+')(NullShim)')

  handle = server_shim.waitforconn(serverkey,12347,response)

  # CLIENT LOGIC
  
  # open connection using the legacy client
  #manually enter the forwarder info
  sock = nat_openconn(serverkey, 12347, forwarderIP='127.0.0.1',forwarderPort=12345)
  
  
  for i in range(10):
    sock.send(str(i))
    msg = sock.recv(10)
    #print msg
    if msg != 'got it':
      raise Exception("expected: got it recv: "+msg)

  sock.close()
  exitall()


