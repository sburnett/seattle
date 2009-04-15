# a simple echo server for testing

def echo(remoteip, remoteport,sock,thishandle,listenhandle):
  print ' connected to '+remoteip+':'+str(remoteport)
  while True:
    msg = sock.recv(10)
    sock.send(msg)



if callfunc == "initialize":
  mycontext['keep_testing'] = True

  if len(callargs) != 1:
    print "args = geni port,"
    exitall()
  

  ip = getmyip()
  port = int(callargs[0])


  handle = waitforconn(ip,port,echo)
