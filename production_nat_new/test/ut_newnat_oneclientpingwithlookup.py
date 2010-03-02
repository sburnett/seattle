"""
One server connects to a local forwarder
One client connects to the server
A few messages are exchanged

the forwarder must be fould using lookups

"""
#pragma repy restrictions.normal


include ShimStack.repy
include NullShim.repy
include NatForwardingShim.repy


def response(remote_ip,remote_port,sock,th,listenhandle):
  try:
    while True:
      msg = sock.recv(1024)
      sock.send('got it')
  except:
     sock.close()



if callfunc == 'initialize':
  
  # use runtime to make sure this is unqiue
  serverkey = 'NATUNITTEST_TEST11_'+str(getruntime())

  ip = '127.0.0.1'
  port = 12345

  server_shim = ShimStack('(NatForwardingShim)(NullShim)')

  handle = server_shim.waitforconn(serverkey,12347,response)

  sleep(5) # give time for the advertisement

  # CLIENT LOGIC
  client_shim = ShimStack('(NatForwardingShim)(NullShim)')
  sock = client_shim.openconn(serverkey,12347)
  
  for i in range(10):
    sock.send(str(i))
    msg = sock.recv(10)
    if msg != 'got it':
      raise Exception("expected: got it recv: "+msg)

  sock.close()
  server_shim.stopcomm(handle)


