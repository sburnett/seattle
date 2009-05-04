# if there are no free events when wait for conn is called
# an exception occurs 


def echo(remoteip, remoteport, sock, thishand, listenhand):
  msg = sock.recv(3)
  sock.close()

def fail_test():
  print 'test timed out'
  exitall()


if callfunc == "initialize":
  max_events = 10

  ip = '127.0.0.1'
  waitport = 12345

  handles = []

  # consume all free events
  for i in range(max_events):
    handles.append(settimer(5,fail_test,[]))
  

  # the waitfor conn we will connect to
  try:
    handle = waitforconn(ip,waitport,echo)
  except:
    pass
  else:
    print 'no exception occured when waitforconn called'


  #cancel timers and end the test
  for i in range(max_events):
    canceltimer(handles[i])
