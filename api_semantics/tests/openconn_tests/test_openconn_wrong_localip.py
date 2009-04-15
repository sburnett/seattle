# if openconn is called with the wrong ip...
#
# no expected output

def do_nothing(remoteip, remoteport, sock, thishand, listenhand):
  sock.close()
    

if callfunc == "initialize":
  mycontext['keep_testing'] = True

  ip = '127.0.0.1'
  waitport = 12345
 

  handle = waitforconn(ip,waitport,do_nothing)

  # remote port is different
  sock1 = openconn(ip,waitport,'128.345.342.111',23456)
  sock1.close()
 

  stopcomm(handle)
 
  
