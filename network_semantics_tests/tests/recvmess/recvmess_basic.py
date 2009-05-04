# basic check that recv mess registers a listener and calls the call back func


def echo(remoteip,remoteport,message,handle):
  mycontext['called'] = True


if callfunc == 'initialize':

  mycontext['called'] = False

  
  handle = recvmess(getmyip(),12345,echo)
  sendmess(getmyip(),12345,'ping')

  sleep(2)
  if not mycontext['called']:
    print 'failed to call call back function'

  stopcomm(handle)
  
