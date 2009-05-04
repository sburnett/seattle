#  Action:  when a waitforconn is called to replace a previous waitforconn a
#  new commhandle should be returned and the old comm handle is made invalid
#


def echo(remoteip, remoteport, sock, thishand, listenhand):
  msg = sock.recv(1024)
  sock.send(msg)
  sock.close()

def do_nothing(remoteip, remoteport, sock, thishand, listenhand):
  sock.close()



if callfunc == "initialize":
  ip = '127.0.0.1'
  waitport = 12345
 
  
  old_handle = waitforconn(ip,waitport,do_nothing)  
  new_handle = waitforconn(ip,waitport,echo)
    
  stopcomm(old_handle)

  sock = openconn(ip,waitport)
  sock.send('hi')
  
  if sock.recv(2) != 'hi':
    raise Exception, "callback function was replaced"
  sock.close()
  stopcomm(new_handle)
  
