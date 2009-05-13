# various tests for socketlikeobj argument semantics




#a dummy waitforconn to connect to
def nothing(rip,rport,sock,th,lh):
  while mycontext['keep_testing']:
    pass

  sock.close()


# a timeout function
def fail_test(sock,handle,thing):
  print 'ERROR: recv('+str(thing)+') blocked'
  sock.close()
  stopcomm(handle)
  mycontext['keep_testing']=False
  exitall()


if callfunc == 'initialize':
  mycontext['keep_testing'] = True
  ip = '127.0.0.1'
  port = 12345

  handle = waitforconn(ip,port,nothing)

  sock = openconn(ip,port)

  
  #test that an exception occurs if you send something not a string or char
  for thing in [5,['hi','there']]:
    try:
      sock.send(thing)
    except:
      pass
    else:
      print 'sending an invalid obj: '+str(thing)+' did not cause exception'


  #test that recv(not int) causes an exception
  for thing in ['hello',['hi','there'],3.14,-10,0]:
    timer = settimer(1,fail_test,[sock,handle,thing])
    try:
      sock.recv(thing)
    except:
      canceltimer(timer)

  sock.close()
  mycontext['keep_testing'] = False
  stopcomm(handle)
  
