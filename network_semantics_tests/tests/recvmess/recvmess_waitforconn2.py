# check that a UDP message ariving at the recvmess port does not
# cause the function to be executed

def echo(remoteip,remoteport,message,handle):
  mycontext['called'] = True

def echo2(rip,rport,sock,thishandle,lhandle):
  print 'called waitfor conn callback'

if callfunc == 'initialize':

  mycontext['called'] = False

  ip = getmyip()
  
  udp_handle = recvmess(ip,12345,echo)
  tcp_handle = waitforconn(ip,12345,echo2)

  
  sendmess(ip,12345,"hi")

  sleep(2)
  if not mycontext['called']:
    print 'failed to call call back function'

  stopcomm(udp_handle)
  stopcomm(tcp_handle)
