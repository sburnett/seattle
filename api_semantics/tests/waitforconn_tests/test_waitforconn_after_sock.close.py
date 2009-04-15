# ensure a waitforconn done on a port previously used by an openconn
# will not cause an excpetion after sock.close() is called

def do_nothing(remoteip, remoteport, sock, thishand, listenhand):
  sock.close()

if callfunc == "initialize":
  ip = '127.0.0.1'
  waitport = 12345
  waitport2 = 23456
  
  

  handle = waitforconn(ip,waitport,do_nothing)
  sock = openconn(ip,waitport,ip,waitport2)
  sock.close()

  handle2 = waitforconn(ip,waitport2,do_nothing)

  stopcomm(handle2)

  stopcomm(handle)
  
