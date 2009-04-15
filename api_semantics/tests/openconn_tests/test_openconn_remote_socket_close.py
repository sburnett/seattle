# if the socket returned from an openconn is kept open but the other side of
# the connection is closed and an identical open conn call is made
# an exception should occur
#
# note: this behavior is coupled to asymetric tcp connection termination.
#  
#
# no expected output

def do_nothing(remoteip, remoteport, sock, thishand, listenhand):
  sock.close()


if callfunc == "initialize":
  
  ip = '127.0.0.1'
  waitport = 12345
 

  handle = waitforconn(ip,waitport,do_nothing)

  # remote port is different
  sock = openconn(ip,waitport,ip,23456)
  
  
  sleep(3) #ensure other side is closed
  
  try:
    sock2= openconn(ip,waitport,ip,23456)
  except Exception:
    pass
  else:
    print "ERROR, no exception thrown"
    sock2.close()
  
  sock.close()
  stopcomm(handle)
  
  
  
