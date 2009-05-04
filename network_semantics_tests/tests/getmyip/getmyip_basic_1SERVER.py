# getmyip returns a valid ip that can be used to make a connection to the
# network, this test is intended to be used with the echo server on geni nodes

if callfunc == 'initialize':

  if len(callargs) != 2 and len(callargs) !=0:
    print ' usage:  remoteip, genei port'
    exitall()

  if len(callargs) == 0:  #local automatic testing
    rip = '127.0.0.1'
    port = 12345
  else:
    rip = callargs[0]
    port = int(callargs[1])  

  sock = openconn(rip,port,getmyip(),port)

  sock.send('hi')
  if sock.recv(2) != 'hi':
    print ' did not echo'

  sock.close()
