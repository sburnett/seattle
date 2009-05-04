# connect to some computers in WAN with a low timeout, expect a connection
# to fail

if callfunc == "initialize":
  mycontext['keep_testing'] = True

  if len(callargs) != 6:
    print "this test is ented to be run against 3 remote servers"
    print "args = ip port, ip port, ip port"
    exitall()

  rip1 = callargs[0]
  rport1 = callargs[1]
  rip2 = callargs[2]
  rport2 = callargs[3]
  rip3 = callargs[4]
  rport4 = callargs[5]
  
  #set a small time out
  time = 0.1

  socks = []

  try:
    socks.append(openconn(rip1,rport1,timeout=time))
    socks.append(openconn(rip2,rport2))
    socks.append(openconn(rip3,rport3))
  except Exception, e:
    print str(e)
  else:
    print "All connects were made with a low timeout"

  for sock in socks:
    sock.close()
