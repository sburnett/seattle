# after stopcomm is called on a waitforconn handle
# the listener is stopped and stopcomm returns true


def echo(rip,rport,sock,thish,lh):
  sock.close()


if callfunc == "initialize":
  
  ip = '127.0.0.1'
  waitport = 12345
  
 
  # the waitfor conn we will connect to
  handle = waitforconn(ip,waitport,echo)

  stopped = stopcomm(handle)
  if (stopped is not True):
    print 'Stopcomm did not return true'  
 
  try:
    sock = openconn(ip,waitport)
  except:
    pass
  else:
    print 'Stopcomm did not stop the listener'
    sock.close()

  stopcomm(handle)
  
