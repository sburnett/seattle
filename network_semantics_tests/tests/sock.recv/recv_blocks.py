# Test to ensure that a call to socket.recv() will block if the buffer is empty
# and the connection is open

def close_it(remoteip, remoteport, sock, thishand, listenhand):
  while mycontext['keep_testing']: # do nothing forever
    sleep(3)
    
  sock.close()


def end_test(handle,sock):
  mycontext['keep_testing'] = False
  sock.close()
  stopcomm(handle)


if callfunc == "initialize":
  mycontext['keep_testing'] = True

  ip = '127.0.0.1'
  waitport = 12345

  handle = waitforconn(ip,waitport,close_it)

  sock = openconn(ip,waitport)

  settimer(5,end_test,[handle,sock])

  try:
    msg = sock.recv(1)
  except Exception,e:
    pass  #otherwise an exception will be thrown when the test ends
  else:
    print 'msg = '+msg
    print 'Recv did not block'
