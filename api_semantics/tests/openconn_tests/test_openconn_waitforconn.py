# if an openconn is called and then a waitforconn is called on the same 
# ip and port the socket returned from open conn should not fail, but
# the wait for conn should
#
#  
#
# no expected output

def do_nothing(remoteip, remoteport, sock, thishand, listenhand):
  while mycontext['keep_testing']:
    msg = sock.recv(10)
    sock.send('foo')

  sock.close()


def expload(remoteip, remoteport, sock, thishand, listenhand):
  print "ERROR, started in bad waitforconn"
  sock.close()


if callfunc == "initialize":
  mycontext['keep_testing'] = True
  ip = '127.0.0.1'
  waitport = 12345
  waitport2 = 23456
 
  # the waitfor conn we will connect to
  handle = waitforconn(ip,waitport,do_nothing)

  sock = openconn(ip,waitport,ip,waitport2)
  
  # test that we can do a quick echo
  sock.send('bar')
  msg = sock.recv(10)
  if msg != 'foo':
    print 'ERROR did not get foo,got '+msg
    

  # waitforconn that should fail  
  try:
    handle2 = waitforconn(ip,waitport2,expload)
  except Exception:
    pass
  else:
    print "ERROR, no exception thrown on bad waitforconn"
    #stopcomm(handle2)
  
  #test we can still echo
  sock.send('bar')
  msg = sock.recv(10)
  if msg != 'foo':
    print 'ERROR did not get foo,got '+msg
 


  mycontext['keep_testing'] = False
  stopcomm(handle)
  stopcomm(handle2)
  sock.close()
  
