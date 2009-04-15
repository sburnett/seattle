# ensure a waitforconn done on a port currently used by a waitforconn
# will cause an exception

def do_nothing(remoteip, remoteport, sock, thishand, listenhand):
  sock.close()

def do_nothing2(remoteip, remoteport, sock, thishand, listenhand):
  sock.close()



if callfunc == "initialize":
  ip = '127.0.0.1'
  waitport = 12345
 
  
  handle = waitforconn(ip,waitport,do_nothing)
  
  try:
    # use a different callback function so the call isnt completely duplicate
    handle2 = waitforconn(ip,waitport,do_nothing2)
  except:
    pass
  else:
    print "Error: no exception thrown when second waitforconn is called"
    stopcomm(handle2)

  stopcomm(handle)
  
