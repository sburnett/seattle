# when recv(n) has been called and is blocking, if characters arrive in the buffer
# the call returns with some number of characters <= n
  

def close_it(remoteip, remoteport, sock, thishand, listenhand):
  sleep(3) # want recv to be blocking
  sock.send('0123456789')
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
  
  msg = sock.recv(5)
  if len(msg) > 5:
    print 'Error: msg size > N was returned from recv(N)'

  end_test(handle,sock)
 
