# if two openconns are called with different values for local ip but
# every other value of the 4-tuple the same, no exception is thrown
#
# no expected output

def do_nothing(remoteip, remoteport, sock, thishand, listenhand):
  sock.close()
    

if callfunc == "initialize":
  mycontext['keep_testing'] = True

  ip1 = '127.0.0.1'
  ip2 = '127.0.0.2'
  waitport = 12345
  port = 23456

  handle1 = waitforconn(ip1,waitport,do_nothing)

  # remote port is different
  sock1 = openconn(ip1,waitport,ip1,port)
  sock2 = openconn(ip1,waitport,ip2,port)
  sock1.close()
  sock2.close()

  stopcomm(handle1)
  
