# if the socket returned from an open conn is closed on both sides of the
# connection an identical open conn call can be made
#
# no expected output

def do_nothing(remoteip, remoteport, sock, thishand, listenhand):
  sock.close()
    

if callfunc == "initialize":

  ip = '127.0.0.1'
  waitport = 12345
 

  handle = waitforconn(ip,waitport,do_nothing)

  # remote port is different
  sock = openconn(ip,waitport,ip,23456)
  sock.close()
  
  sleep(3) #time for the os to reclaim the socket 

  sock2= openconn(ip,waitport,ip,23456)
  sock2.close()

  stopcomm(handle)
  
  
