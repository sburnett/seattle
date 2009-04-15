# Tests tests the behavior of send after close() is called by a peer.
#
# close() closes the connection entirely, so an exception should occur when
# send is called
#
# this is a simple test case, where close is called and no other actions are
# taken for some amount of time, such that there is no in flight traffic while
# closing the connection
#
# no expected output

def close_it(remoteip, remoteport, sock, thishand, listenhand):
  sock.close()


if callfunc == "initialize":
  mycontext['keep_testing'] = True

  ip = '127.0.0.1'
  waitport = 12345

  handle = waitforconn(ip,waitport,close_it)

  sock = openconn(ip,waitport)

  sleep(10) #ensure the remote socket has closed  

  
  try:
    sock.send('i should throw an exception')
  except:
    pass # exception should occur
  else:
    print 'no exception occured after first send'

  try:
    sock.send('again')
  except:
    pass # exception should occur
  else:
    print 'no exception occured after second send'


  sock.close()
  stopcomm(handle)
 
