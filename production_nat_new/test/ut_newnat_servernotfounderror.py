"""

a clt connects and asks for a host not registed at the forwarder.
An appropriate excetpion should be generated

"""

#pragma repy restrictions.normal

include ShimStack.repy
include NullShim.repy
include NatForwardingShim.repy



if callfunc == 'initialize':
  
  serverkey = 'NAT$BLAHBLAHBLAH'

  ip = '127.0.0.1'
  port = 12345

  # CLIENT LOGIC

  client_shim = ShimStack('(NatForwardingShim,'+ip+','+str(port)+')(NullShim)')
  try:
    sock = client_shim.openconn(serverkey,12347)
  except NatConnError,e:
    pass
  else:
    print 'ERROR: forwarder did not raise an error'
    sock.close()
