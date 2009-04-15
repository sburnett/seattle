# after stopcomm is called on a waitforconn handle
# an new waitforconn can be performed on the same ip and port with
# a different call back funciton.
#
# this tests that the correct call back funcion is called when a connection
# is made

def foo(remoteip, remoteport, sock, thishand, listenhand):
  stopcomm(listenhand)
  sock.send('foo')
  sock.recv(1)
  sock.close()

def bar(remoteip, remoteport, sock, thishand, listenhand):
  stopcomm(listenhand)
  sock.send('bar')
  sock.recv(1)
  sock.close()


if callfunc == "initialize":
  ip = '127.0.0.1'
  waitport = 12345
  
 
  # the waitfor conn we will connect to
  handle = waitforconn(ip,waitport,foo)
  sock = openconn(ip,waitport)

  if sock.recv(3) != 'foo':
    print 'ERROR: did not recieve foo'
  sock.send('a')
  sock.close()

  sleep(3) #give os time to reclaim the port
  handle = waitforconn(ip,waitport,bar)
  sock = openconn(ip,waitport)
  
  if sock.recv(3) != 'bar':
    print 'ERROR: did not recieve bar'
  sock.send('a')
  sock.close()  
