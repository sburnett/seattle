# ensure a waitforconn done on a port currently used by an openconn
# will cause an exception

def do_nothing(remoteip, remoteport, sock, thishand, listenhand):
  sock.close()

if callfunc == "initialize":
  ip = '127.0.0.1'
  waitport = 12345
  waitport2 = 23456
  
  

  handle = waitforconn(ip,waitport,do_nothing)
  sock = openconn(ip,waitport,ip,waitport2)

  try:
    # use a different callback function so the call isnt completely duplicate
    handle2 = waitforconn(ip,waitport2,do_nothing)
  except:
    pass
  else:
    print "Error: no exception thrown when second waitforconn is called"
    stopcomm(handle2)

  stopcomm(handle)
  sock.close()
