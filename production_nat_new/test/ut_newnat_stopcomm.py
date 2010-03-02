"""

a client connects to a server
the server calls stopcomm
another client trys to connect

the 2nd client should fail

"""
#pragma repy restrictions.normal

include ShimStack.repy
include NullShim.repy
include NatForwardingShim.repy


def response(remote_ip,remote_port,sock,th,listenhandle):
  sock.close()



if callfunc == 'initialize':
  
  serverkey = 'NAT$BLAHBLAHBLAH'

  ip = '127.0.0.1'
  port = 12345

  server_shim = ShimStack('(NatForwardingShim,'+ip+','+str(port)+')(NullShim)')

  handle = server_shim.waitforconn(serverkey,12347,response)


  # test that a connection can be made
  sleep(.2)
  client_shim = ShimStack('(NatForwardingShim,'+ip+','+str(port)+')(NullShim)')
  sock = client_shim.openconn(serverkey,12347)
  sock.close()
  

  # do the stopcomm
  server_shim.stopcomm(handle)

  # try to connect again
  sleep(.2)
  try:
   sock = client_shim.openconn(serverkey,12347)
  except NatConnError:
    pass
  else: 
    sock.close()
    print 'ERROR: was able to connect after stopcomm'
    
