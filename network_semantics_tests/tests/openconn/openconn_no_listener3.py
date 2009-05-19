# if openconn attempts to connect to a recvmess 
# connection an exception is thrown
#
# no expected output

def do_nothing(rip,rport,msg,thishandle):
  pass


if callfunc == "initialize":

  ip = '127.0.0.1'
  waitport = 12345
 
 
  #set up a recmess
  handle = recvmess(ip,waitport,do_nothing)


  #try to open a connection to the good_sock
  try:
    sock = openconn(ip,waitport)
  except Exception:
    pass
  else:
    sock.close()
    print "ERROR, openconn with no listener did not throw exception"

  
  stopcomm(handle)
