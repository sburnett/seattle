# A new recvmess called on the same ip and port will reuturn a new commhandle
# calling stopcomm on the old comm handle will have no affect.

def fail(remoteip,remoteport,message,handle):
  print 'called the old call back'

def foo(rip,rport,msg,handle):
  mycontext['called'] = True
  

if callfunc == 'initialize':

  mycontext['called'] = False

  ip = getmyip()
  
  old_handle = recvmess(ip,12345,fail)
  new_handle = recvmess(ip,12345,foo)

  stopcomm(old_handle)  # this should have NO EFFECT
  sendmess(ip,12345,'ping')


  sleep(2)
  if not mycontext['called']:
    print 'ERROR: failed to call new callback function'

 
  stopcomm(new_handle)
 
