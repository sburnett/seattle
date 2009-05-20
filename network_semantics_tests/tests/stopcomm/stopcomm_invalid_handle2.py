# if stopcomm is called on a handle that has been replaced
# by a newer waitforconn False is returned


def echo(rip,rport,m,h):
  sock.close()

def do_nothing(rip,rport,msg,handle):
  pass


if callfunc == "initialize":
  
  ip = '127.0.0.1'
  waitport = 12345
  
 
  # the waitfor conn we will connect to
  handle = recvmess(ip,waitport,echo)
  new_handle = recvmess(ip,waitport,do_nothing)

  stopped = stopcomm(handle)
  if (stopped is not False):
    print 'Stopcomm did not return False'  
 
  stopcomm(new_handle)
  
