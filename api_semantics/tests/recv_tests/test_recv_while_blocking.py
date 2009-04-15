# with m > n, if recv(m) is called and is blocking and a string of n is sent
#  all n characters will be returned from the call.
  

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
  
  msg = sock.recv(32)
  if len(msg) != 10:
    print 'Error: msg with length < 10 recvied when len 10 was sent'

  end_test(handle,sock)
 
