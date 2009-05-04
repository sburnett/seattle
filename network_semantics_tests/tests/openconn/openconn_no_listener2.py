# if openconn is attempts to connect to an allready open socket
# connection an exception is thrown
#
# no expected output

def do_nothing(rip,rport,sock,thishandle,listhandle):
  sock.close()


if callfunc == "initialize":

  ip = '127.0.0.1'
  waitport = 12345
  port = 23456
 
  #set up a do nothing waitforcon
  handle = waitforconn(ip,waitport,do_nothing)

  #set up a valid connection
  good_sock = openconn(ip,waitport,ip,port)


  #try to open a connection to the good_sock
  try:
    sock = openconn(ip,port)
  except Exception:
    pass
  else:
    sock.close()
    print "ERROR, openconn with no listener did not throw exception"

  good_sock.close()
  stopcomm(handle)
