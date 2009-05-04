# Test to ensure that a blocking call to socket.recv() will throw an exception 
# if socket.close() is called

def close_it(remoteip, remoteport, sock, thishand, listenhand):
  while mycontext['keep_testing']: # do nothing forever
    sleep(3)
    
  sock.close()


def close_sock(sock):
  sock.close()


if callfunc == "initialize":
  mycontext['keep_testing'] = True

  ip = '127.0.0.1'
  waitport = 12345

  handle = waitforconn(ip,waitport,close_it)

  sock = openconn(ip,waitport)

  settimer(2,close_sock,[sock])

  try:
    msg = sock.recv(1)
  except Exception,e:
    if str(e) != 'Socket closed':  raise
  else:
    print 'ERROR: No exception was thrown'

  stopcomm(handle)
  mycontext['keep_testing'] = False
