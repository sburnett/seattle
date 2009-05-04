# calling recvmess with the same ip and port as a previous recvmess will
# replace the call back function


def fail(remoteip,remoteport,message,handle):
  print 'called the old call back'

def foo(rip,rport,msg,handle):
  mycontext['called'] = True

if callfunc == 'initialize':

  mycontext['called'] = False

  ip = getmyip()
  
  old_handle = recvmess(ip,12345,fail)
  new_handle = recvmess(ip,12345,foo)

  
  sendmess(ip,12345,'ping')


  sleep(2)
  if not mycontext['called']:
    print 'failed to call new callback function'

 
  stopcomm(new_handle)
  stopcomm(old_handle)
