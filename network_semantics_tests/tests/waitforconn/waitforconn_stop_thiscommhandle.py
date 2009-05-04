# waitforconn is called sucessfully, then a stopcomm is called on the
#  "thiscommhandle" in the call back arguments, this has the effect of
# closing the socket, the listener remains active

def do_nothing(remoteip, remoteport, sock, thishand, listenhand):
  mycontext['connections'] += 1
  stopcomm(thishand)
  mycontext['lock'].release()

  # don't let this function exit in case there are unknown side effects
  while mycontext['keep_testing']:
    sleep(1)
    
def fail_test(handle,sock):
  stopcomm(handle)
  sock.close()
  print 'test failed due to recv timeout'


if callfunc == "initialize":
  mycontext['keep_testing'] = True
  mycontext['connections'] = 0
  mycontext['lock'] = getlock()
  ip = '127.0.0.1'
  waitport = 12345
  

  lock = mycontext['lock']
 
  # the waitfor conn we will connect to
  handle = waitforconn(ip,waitport,do_nothing)
  
  lock.acquire()
  sock = openconn(ip,waitport)
  
  lock.acquire()
  lock.release()

  # in case the call to recv blocks
  timerhandle = settimer(2, fail_test,[handle,sock])

  # ensure the socket is closed
  try:
    sock.recv('1')
  except:
    pass
  else: 
    print 'no exception when recv from closed connection'

  canceltimer(timerhandle) 

  
  #ensure that the listener is still active
  lock.acquire()
  sock2 = openconn(ip,waitport)

  lock.acquire()
  lock.release()

  mycontext['keep_testing'] = False
  stopcomm(handle)
  sock.close()

  if mycontext['connections'] != 2:
    print "ERROR, inncorect number of connections made: "+str(mycontext['connections'])
  
