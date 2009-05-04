# if two openconns are called and the 4-tuple is identical
# an exception is thrown.
#
# no expected output

def do_nothing(remoteip, remoteport, sock, thishand, listenhand):
  sock.close()
    

if callfunc == "initialize":
  mycontext['keep_testing'] = True

  ip = '127.0.0.1'
  waitport = 12345
 
  handle = waitforconn(ip,waitport,do_nothing)
  
  # tuples are identical
  sock1 = openconn(ip,waitport,ip,23456)
  try:
    sock2 = openconn(ip,waitport,ip,23456)
  except Exception,e:
    #tests currently only force that there is an exception, not the type
    #if 'Cannot assign requested address' not in str(e): raise
    pass
  else:
    print 'Error: no exception thrown with identical tuples'
    sock2.close()
  sock1.close()


  stopcomm(handle)
  
