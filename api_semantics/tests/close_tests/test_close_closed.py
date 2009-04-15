# calling close() on a closed connection should not fail

def do_nothing(remoteip, remoteport, sock, thishand, listenhand):
  sock.close()




if callfunc == "initialize":
  ip = '127.0.0.1'
  waitport = 12345
  
 
  # the waitfor conn we will connect to
  handle = waitforconn(ip,waitport,do_nothing)

  sock = openconn(ip,waitport)
  
  stopcomm(handle)
  sock.close()
  sock.close()
  
