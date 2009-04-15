

def do_nothing(remoteip, remoteport, sock, thishand, listenhand):
  while mycontext['keep_testing']:
    

  sock.close()




if callfunc == "initialize":
  mycontext['keep_testing'] = True
  ip = '127.0.0.1'
  waitport = 12345
  
 
  # the waitfor conn we will connect to
  handle = waitforconn(ip,waitport,do_nothing)

  sock = openconn(ip,waitport)
  

  mycontext['keep_testing'] = False
  stopcomm(handle)
  sock.close()
  
