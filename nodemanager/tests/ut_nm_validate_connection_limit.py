#pragma repy restrictions.loose


def waitonsocket(socketobj, num):
  try:
    socketobj.recv(1)
  except Exception, e:
    # this is good, the socket was closed...   This will usually be #5...
#    print num, e
    exitall()
  else:
    print "Error, should not return from recv!?!"
  

if callfunc == 'initialize':

  ip = getmyip()

  # nm accept only three cons from an IP, since it may be processing one, the
  # maximum I should be able to get and use is four.   The other should be
  # closed.
  junk1 = openconn(ip,1224)
  junk2 = openconn(ip,1224)
  junk3 = openconn(ip,1224)
  junk4 = openconn(ip,1224)
  junk5 = openconn(ip,1224)
  settimer(0, waitonsocket, (junk1,1))
  settimer(0, waitonsocket, (junk2,2))
  settimer(0, waitonsocket, (junk3,3))
  settimer(0, waitonsocket, (junk4,4))
  settimer(0, waitonsocket, (junk5,5))

  sleep(5)
  print "Error:Can happily block on 5 nm connections!?!"
  exitall()
#  sockobj.close()
