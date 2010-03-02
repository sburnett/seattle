"""
One server connects to a local forwarder
One client connects to the server
A few messages are exchanged

"""

#pragma repy restrictions.normal

include NatForwardingShim.repy


def response(remote_ip,remote_port,sock,th,listenhandle):
  try:
    while True:
      msg = sock.recv(1024)
      sock.send('got it')
  except:
     sock.close()

def test_print():
  print "hi"

if callfunc == 'initialize':
  
  serverkey = 'NAT$BLAHBLAHBLAH'

  ip = '127.0.0.1'
  port = 12345

  server_shim = ShimStack('(NatForwardingShim,'+ip+','+str(port)+')(NullShim)')

  handle = server_shim.waitforconn(serverkey,12347,response)

  # CLIENT LOGIC
  client_shim = ShimStack('(NatForwardingShim,'+ip+','+str(port)+')(NullShim)')
  sock = client_shim.openconn(serverkey,12347)
  
  for i in range(10):
    sock.send(str(i))
    msg = sock.recv(10)
    if msg != 'got it':
      raise Exception("expected: got it recv: "+msg)

  sock.close()
  exitall()


