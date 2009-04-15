# Test to ensure that after one end of a socket connection is closed
# the other end can continue to read until the buffer is empty.
# once the buffer is empty the empty string will be returned.

def close_it(remoteip, remoteport, sock, thishand, listenhand):
  sock.send('0123456789')
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
  msg = sock.recv(5)
  msg = sock.recv(5)
  if msg != '56789':
    raise 'buffered message not recived after sock was closed'
  for i in range(3):  # try this a few times
    msg = sock.recv(5)
    if msg != '':
      raise 'null string not recived after sock was closed and buffer emptied'
  
  
  sock.close()
  stopcomm(handle)
