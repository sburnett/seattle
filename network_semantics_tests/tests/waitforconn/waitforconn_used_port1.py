#  Action:  waitforconn is called on a port being used by another waitforconn
#
#  Result:  No exception occurs, the callback function is replaced.


def echo(remoteip, remoteport, sock, thishand, listenhand):
  msg = sock.recv(1024)
  sock.send(msg)
  sock.close()

def do_nothing(remoteip, remoteport, sock, thishand, listenhand):
  sock.close()



if callfunc == "initialize":
  ip = '127.0.0.1'
  waitport = 12345
 
  
  waitforconn(ip,waitport,do_nothing)  
  handle = waitforconn(ip,waitport,echo)
    
  sock = openconn(ip,waitport)
  sock.send('hi')
  
  if sock.recv(2) != 'hi':
    raise Exception, "callback function was replaced"
  sock.close()
  stopcomm(handle)
  
