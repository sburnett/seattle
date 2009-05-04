# a simple echo server for testing

def echo(remoteip, remoteport,sock,thishandle,listenhandle):
  while True:
    try:
      msg = sock.recv(10)
      sock.send(msg)
      if msg == '':    
        sock.close()
        return
    finally:
      sock.close()
      return 


if callfunc == "initialize":
  mycontext['keep_testing'] = True


  if len(callargs) != 2 and len(callargs) !=1:
    print "args = ip, geni port (getmyip() will be used if ip is not supplied,"
    exitall()
  
  if len(callargs) ==2:
    ip = callargs[0]
    port = int(callargs[1])
  else:
    ip = getmyip()
    port = int(callargs[0])

  handle = waitforconn(ip,port,echo)
 
   
