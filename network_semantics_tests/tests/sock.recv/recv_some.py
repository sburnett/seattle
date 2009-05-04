# Test to ensure that a call to socket.recv(n) will return <= n characters when
# there are greater than n characters ready to be returned


def close_it(remoteip, remoteport, sock, thishand, listenhand):
  sock.send('0123456789')
  mycontext['lock'].release()
  while mycontext['keep_testing']: # do nothing forever
    sleep(3)
    
  sock.close()


def end_test(handle,sock):
  mycontext['keep_testing'] = False
  sock.close()
  stopcomm(handle)


if callfunc == "initialize":
  mycontext['keep_testing'] = True
  mycontext['lock'] = getlock()
  ip = '127.0.0.1'
  waitport = 12345

  # ensure chars a ready to read when recv is called
  mycontext['lock'].acquire() 

  handle = waitforconn(ip,waitport,close_it)

  sock = openconn(ip,waitport)
  
  mycontext['lock'].acquire()
  mycontext['lock'].release()
  msg = sock.recv(3)
  if len(msg) > 3:
    print 'Error: msg with length > 3 reutnred from recv(3)'

  end_test(handle,sock)
 
