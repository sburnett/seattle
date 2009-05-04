# A sendmess should be able to share a ip/port 4-tuple with a tcp connection

def nothing(ip,port,sock,handle1,handle2):
  pass

def foo(ip,port,msg,handle):
  mycontext['recv'] = True

if callfunc == 'initialize':
  mycontext['recv'] = False
  ip = getmyip()
  waitport = 12345
  port = 23456

  whandle = waitforconn(ip,waitport,nothing)
  rhandle = recvmess(ip,waitport,foo)  

  sock = openconn(ip,waitport,ip,port)
  sendmess(ip,waitport,'ping',localip=ip,localport=port)

  sock.close()
  stopcomm(whandle)
  stopcomm(rhandle)

  
  if not mycontext['recv']:
    print 'UDP message was not recieved'
