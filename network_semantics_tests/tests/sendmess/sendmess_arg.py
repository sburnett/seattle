# Test various argument semantics for sendmess



#a dummy method so there is something to connect to
def nothing(rip,rport,msg,handle):
  pass



# test that the locaip used by openconn is getmyip
def test_remoteip(rip,rport,msg,handle):
  if rip != getmyip():
    print 'remoteip did not equal getmyip: '+rip+' vs '+getmyip()



if callfunc == 'initialize':
  
  #start a listener
  handle = recvmess('127.0.0.1',12345,nothing)


  #ip given is not  a string
  try:
    sendmess(127001,12345,'hi')
  except:
    pass
  else:
    print 'int used for ip did not cause exception'


  #localip given is not a string
  try:
    sock = openconn('127.0.0.1',12345,'hello',127002,23456)
  except:
    pass
  else:
    print 'int used for local ip did not cause exception'
    



  # test port ranges
  for port in [-5000,65536]:
     try:
       sendmess('127.0.0.1',port,"hello")
     except:
       pass
     else:
      print 'invalid port did not cause exception: '+str(port)
  
   
     try:
       sendmess('127.0.0.1',12345,'hello','127.0.0.2',port)
     except:
       pass
     else:
       print 'invalid localport did not cause an exception: '+str(port)
  


  #test msg is a string
  try:
    sendmess('127.0.0.1',12345,42)
  except:
    pass
  else:
    print 'invalid msg (int)  did not cause exception'
    



  #test that if local ip / port is specified both are
  try:
    sendmess('127.0.0.1',12345,"hello",localip='127.0.0.1')
  except:
    pass
  else:
    print 'specifing localip and not locaPort did not cause exception'
    

  try:
    sendmess('127.0.0.1',12345,"hello",localport=12345)
  except:
    pass
  else:
    print 'specifing localport and not localip did not cause exception'
    


  # test that an unspecified localip will resolve to getmyip()
  h2 = recvmess(getmyip(),12345,test_remoteip)
  sendmess(getmyip(),12345,"hi")


  stopcomm(handle)
  stopcomm(h2)
   
  
