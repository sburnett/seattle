# if the socket returned from an openconn is closed but the other side of
# the connection is kept open and an identical open conn call is made
# a new connection should be established without an exception
#  
#
# no expected output

def do_nothing(remoteip, remoteport, sock, thishand, listenhand):
  
  send_this = mycontext['send_this']
  while(True):
    
    # not concerend with erros that occur here do to
    # connections breaking
    try:
      msg=sock.recv(10)
      sock.send(send_this)
    except:
      break
  sock.close()

if callfunc == "initialize":
  mycontext['send_this'] = 'foo'

  ip = '127.0.0.1'
  waitport = 12345
 

  handle = waitforconn(ip,waitport,do_nothing)

  # remote port is different
  sock = openconn(ip,waitport,ip,23456)
  
  # set the value that the next connection to a waitfor conn
  # will reutrn to 'bar'
  mycontext['send_this'] = 'bar'

 
  #check that we are connected and recv foo
  sock.send('a')
  if (sock.recv(10) != 'foo'): 
    print ' ERROR: did not recv foo'

  sock.close()
  sleep(3) #time for the os to reclaim the socket 
  
  
  sock2= openconn(ip,waitport,ip,23456)
  sock.send('a')
  if (sock.recv(10) != 'bar'): 
    print ' ERROR: did not recv bar'
  
  
 stopcomm(handle)
 sock2.close()
 
  
  
