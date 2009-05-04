# after stopcomm is called on a waitforconn handle
# an identical waitforconn can be performed without expcetion

def do_nothing(remoteip, remoteport, sock, thishand, listenhand):
  pass

def echo(rip,rport,sock,thish,lh):
  msg = sock.recv(100)
  sock.send(msg)
  sock.close()


if callfunc == "initialize":
  mycontext['keep_testing'] = True
  ip = '127.0.0.1'
  waitport = 12345
  
 
  # the waitfor conn we will connect to
  handle = waitforconn(ip,waitport,do_nothing)

  stopcomm(handle)
  handle = waitforconn(ip,waitport,echo)
  
  sock = openconn(ip,waitport)
  sock.send('beraber')
  if sock.recv(10) != 'beraber':
    print 'Listener does no appear active'
  sock.close()

  stopcomm(handle)
  
