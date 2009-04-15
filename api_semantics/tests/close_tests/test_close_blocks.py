# close() should block until the connection is truly closed and could
# be re-used

def do_nothing(remoteip, remoteport, sock, thishand, listenhand):
  print 'hi'
  while mycontext['keep_testing']:
    sleep(1)

  sock.close()




if callfunc == "initialize":
  mycontext['keep_testing'] = True
  ip = '127.0.0.1'
  waitport = 12345
  localport = 23456
 
  # the waitfor conn we will connect to
  handle = waitforconn(ip,waitport,do_nothing)

  sock = openconn(ip,waitport,ip,localport)
  sock.close()
  sock = openconn(ip,waitport,ip,localport)
  

  mycontext['keep_testing'] = False
  stopcomm(handle)
  sock.close()
  
