# Test various argument semantics for openconn



#a dummy method so there is something to connect to
def nothing(rip,rport,sock,th,lh):
  pass



# test that the locaip used by openconn is getmyip
def test_remoteip(rip,rport,sock,th,lh):
  if rip != getmyip():
    print 'remoteip did not equal getmyip: '+rip+' vs '+getmyip()



if callfunc == 'initialize':
  
  #start a listener
  handle = waitforconn('127.0.0.1',12345,nothing)


  #ip given is not  a string
  try:
    sock = openconn(127001,12345)
  except:
    pass
  else:
    print 'int used for ip did not cause exception'
    sock.close()

  #localip given is not a string
  #ip given is not  a string
  try:
    sock = openconn('127.0.0.1',12345,127002,23456)
  except:
    pass
  else:
    print 'int used for local ip did not cause exception'
    sock.close()



  # test port ranges
  for port in [-5000,65536]:
     try:
       sock = openconn('127.0.0.1',port)
     except:
       pass
     else:
      print 'invalid port did not cause exception: '+str(port)
      sock.close()
   
     try:
       sock = openconn('127.0.0.1',12345,'127.0.0.2',port)
     except:
       pass
     else:
       print 'invalid localport did not cause an exception: '+str(port)
       sock.close()


  #test values for timeout
  for t in [-5,0,'string']:
     try:
       sock = openconn('127.0.0.1',12345,timeout=t)
     except:
       pass
     else:
       print 'invalid timeout did not cause exception: '+str(t)
       sock.close()



  #test that if local ip / port is specified both are
  try:
    sock = openconn('127.0.0.1',12345,localip='127.0.0.1')
  except:
    pass
  else:
    print 'specifing localip and not locaPort did not cause exception'
    sock.close()

  try:
    sock = openconn('127.0.0.1',12345,localport=12345)
  except:
    pass
  else:
    print 'specifing localport and not localip did not cause exception'
    sock.close()


  # test that an unspecified localip will resolve to getmyip()
  h2 = waitforconn(getmyip(),12345,test_remoteip)
  sock =openconn(getmyip(),12345)
  sock.close()

  stopcomm(handle)
  stopcomm(h2)
   
  
