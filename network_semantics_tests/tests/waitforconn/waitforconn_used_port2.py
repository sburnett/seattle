# ensure a waitforconn done on a port currently used by an openconn
# will NOT cause an exception

def do_nothing(remoteip, remoteport, sock, thishand, listenhand):
  sock.close()

if callfunc == "initialize":
  ip = '127.0.0.1'
  waitport = 12345
  waitport2 = 23456
  
  

  handle = waitforconn(ip,waitport,do_nothing)
  sock = openconn(ip,waitport,ip,waitport2)

  # use a different callback function so the call isnt completely duplicate
  handle2 = waitforconn(ip,waitport2,do_nothing)
  
  stopcomm(handle2)
  stopcomm(handle)
  sock.close()
