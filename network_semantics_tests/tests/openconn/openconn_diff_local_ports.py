# if two openconns are called with different values for local port but
# every other value of the 4-tuple the same, no exception is thrown
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
  sock1 = openconn(ip,waitport,ip,23456)
  sock2 = openconn(ip,waitport,ip,34567)
  sock1.close()
  sock2.close()

  stopcomm(handle)
  
  
