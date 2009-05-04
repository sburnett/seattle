# Tests that an exception is thrown if send() is called after close()

def close_it(remoteip, remoteport, sock, thishand, listenhand):
  while mycontext['keep_testing']: # do nothing forever
    sleep(3)
    
  sock.close()



if callfunc == "initialize":
  mycontext['keep_testing'] = True

  ip = '127.0.0.1'
  waitport = 12345

  handle = waitforconn(ip,waitport,close_it)

  sock = openconn(ip,waitport)

  sock.close()

  try:
    msg = sock.send('hello')
  except Exception,e:
    if 'Socket closed' not in str(e):  raise
  else:
    print 'ERROR: No exception was thrown'

  stopcomm(handle)
  mycontext['keep_testing'] = False
