# do two openconns with identical 4-tuples, except for having different remote
# ip


if callfunc == "initialize":
  mycontext['keep_testing'] = True

  if len(callargs) != 3:
    print "args = geni port, server ip1, server ip 2"
    exitall()

  

  ip = getmyip()
  remoteip1 = callargs[1]
  remoteip2 = callargs[2]
  port = int(callargs[0])


  # remote port is different
  sock1 = openconn(remoteip1,port,ip,port)
  sock2 = openconn(remoteip2,port,ip,port)
  
  sock1.send('foo')
  
  sock2.send('bar')

  if sock1.recv(5) != 'foo':
    print "ERROR, did not get correct echo from sock1"
  else:
    print "server 1 good"
  if sock2.recv(5) != 'bar':
    print "ERROR, did not get correct echo from sock1"
  else:
    print "server 2 good"


  sock1.close()
  sock2.close()
  
