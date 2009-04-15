# IF openconn is called with a local ip and port that is currently used by 
# a waitfor conn an exception should be caused

def do_nothing(remoteip, remoteport, sock, thishand, listenhand):
  pass
    

if callfunc == "initialize":
  mycontext['keep_testing'] = True

  ip = '127.0.0.1'
  waitport = 12345

  handle_local = waitforconn(ip,waitport,do_nothing)
  
  #ensure there is a valid waitforconn to conncet to
  handle_remote = waitforconn(ip,23456,do_nothing) 

  try:
    sock = openconn(ip,23456,ip,waitport)
  except Exception, e:
    #tests current do not care about Exception types
    #if 'Address already in use' not in str(e): raise
    pass
  else:
    print 'ERROR: exception was not thrown'
    sock.close()

  stopcomm(handle_local)
  stopcomm(handle_remote)

 
