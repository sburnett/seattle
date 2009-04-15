# if waitforconn is called and then a stopcomm performed, an openconn
# should then be able to reuse the ip and port
#
# no expected output

def do_nothing(remoteip, remoteport, sock, thishand, listenhand):
  sock.close()
    

if callfunc == "initialize":

  ip = '127.0.0.1'
  waitport = 12345
  waitport2 = 23456
   
  handle = waitforconn(ip,waitport,do_nothing)
  stopcomm(handle)

  ##something for the openconn to connect to
  handle2 = waitforconn(ip,waitport2,do_nothing)

  sock = openconn(ip,waitport2,ip,waitport)
  sock.close()
  stopcomm(handle2)
