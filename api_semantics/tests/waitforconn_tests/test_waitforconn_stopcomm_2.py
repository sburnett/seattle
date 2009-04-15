# duplicate of test_waitforconn_stopcomm1.py except that stopcomm is
# called on the listenhandle provided to the callback function

# waitforconn is called sucessfully, then a stopcomm is called
# the listener is stoped and further connections are not accepted
# (connections not made nor is callback function called), connections 
# allready being processed are not canceled

def do_nothing(remoteip, remoteport, sock, thishand, listenhand):
  stopcomm(listenhand)
  mycontext['lock'].release()
  msg = sock.recv(10)
  sock.send(msg)


if callfunc == "initialize":
  mycontext['lock'] = getlock()
  ip = '127.0.0.1'
  waitport = 12345
  
  mycontext['lock'].acquire() 

  # the waitfor conn we will connect to
  handle = waitforconn(ip,waitport,do_nothing)
  
  # open a connection
  sock = openconn(ip,waitport)
  
  mycontext['lock'].acquire()
  mycontext['lock'].release()  
 

  #ensure the listner is no longer active
  try:
    sock2 = openconn(ip,waitport)
  except:
    pass
  else:
    sock2.close()
    print 'Error, second connection was accepted'

  # ensure that the original call back funciton
  # was not stopped
  sock.send('hi')
  if sock.recv(10) != 'hi':
    print 'Error, did not recieve echo'
  
 
  stopcomm(handle)
  sock.close()

 
