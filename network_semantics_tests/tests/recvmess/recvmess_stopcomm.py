# After stopcomm has benn called on a commhandle messages are not handled by
# the callback

def fail(remoteip,remoteport,message,handle):
  print 'called the old call back'



if callfunc == 'initialize':

  ip = getmyip()
  
  handle = recvmess(ip,12345,fail)
  stopcomm(handle)  
  sendmess(ip,12345,'ping')
  
 
