# ensure that waitforconn can accept multiple connections and process them
# in parellell

def echo(remoteip, remoteport, sock, thishand, listenhand):
  msg = sock.recv(3)
  sock.send(msg)
  sock.close()




if callfunc == "initialize":
  
  ip = '127.0.0.1'
  waitport = 12345
  
 
  # the waitfor conn we will connect to
  handle = waitforconn(ip,waitport,echo)

  sock = openconn(ip,waitport)
  sock2 = openconn(ip,waitport)

  sock2.send('foo')
  if (sock2.recv(3) != 'foo'):
    print "ERROR: did not recieve foo"

  sock.send('bar')
  if (sock.recv(3) != 'bar'):
    print "ERROR: did not recieve bar"

  stopcomm(handle)
  sock.close()
  sock2.close()  
