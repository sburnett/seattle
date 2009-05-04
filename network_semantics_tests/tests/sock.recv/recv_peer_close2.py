# If the peer closes the socket, and recv() is called where there is no
# data to be read, an exception is thrown

def close_it(remoteip, remoteport, sock, thishand, listenhand):
  sock.close()
  mycontext['lock'].release()


if callfunc == "initialize":
  ip = '127.0.0.1'
  waitport = 12345
  mycontext['lock'] = getlock()


  mycontext['lock'].acquire()

  handle = waitforconn(ip,waitport,close_it)

  sock = openconn(ip,waitport)
  mycontext['lock'].acquire() #ensure the connection is closed
  mycontext['lock'].release()
  try:
    msg = sock.recv(1)
  except:
    pass
  else:
    print "No exception occured after the buffer was empty"
  
  
  sock.close()
  stopcomm(handle)
