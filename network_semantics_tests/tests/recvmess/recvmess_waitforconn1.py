# check that a tcp message ariving at the recvmess port does not
# cause the function to be executed

def echo(remoteip,remoteport,message,handle):
  print 'called recv mess call back'

def echo2(rip,rport,sock,thishandle,lhandle):
  mycontext['called'] = True

if callfunc == 'initialize':

  mycontext['called'] = False

  ip = getmyip()
  
  udp_handle = recvmess(ip,12345,echo)
  tcp_handle = waitforconn(ip,12345,echo2)

  sock = openconn(ip,12345)
  sock.send('ping')
  sock.close()  

  sleep(2)
  if not mycontext['called']:
    print 'failed to call TCP callback function'

  stopcomm(udp_handle)
  stopcomm(tcp_handle)
