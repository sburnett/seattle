#pragma repy restrictions.loose


def error_and_exit():
  print "Error:Can wait for more than 15 seconds!"
  exitall()

if callfunc == 'initialize':

  ip = getmyip()


  # nm will only wait 10 seconds for a connection to have activity...
  socketobj = openconn(ip,<nodemanager_port>)
  # the node manager should time the socket out before this fires...
  settimer(15, error_and_exit, ())

  try:
    socketobj.recv(1)
  except Exception, e:
    # this is good, the socket was closed...  
    if 'Socket closed' in str(e):
      exitall()
    else:
      raise
  else:
    print "Error, should not return from recv!?!"
  

