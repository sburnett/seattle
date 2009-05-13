 # various tests for waitforconn argument semantics



# a dummy call back function with correct arguments
def nothing(rip,rport,sock,th,lh):
  sock.close()
  pass

# a call back function with the wrong number of args
def badargs(ip,port,sock):
  pass


if callfunc == 'initialize':
  
  #test that ip must be a string
  try:
    h = waitforconn(127001,12345,nothing)
  except:
    pass
  else:
    stopcomm(h)
    print 'using non string ip did not cause exception'


  #test various values for port
  for port in [-12345,0,65536,3.14,'string']:
  
    try:
      h = waitforconn('127.0.0.1',port,nothing)
    except:
      pass
    else:
      stopcomm(h)
      print 'using bad port: '+str(port)+' did not cause an exception'


  #test that an invalid call back func will cause an exception
  for func in [badargs,3]:

    try:
      h = waitforconn('127.0.0.1',12345,func)
    except:
      pass
    else:
      stopcomm(h)
      print 'using bad call back function: '+str(func)+' did not cause exception'
