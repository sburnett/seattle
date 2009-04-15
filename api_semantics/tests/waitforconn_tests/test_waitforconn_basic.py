# test that waitforconn starts a listener that will pick up connections made
# to that port / ip


def do_nothing(remoteip, remoteport, sock, thishand, listenhand):
  canceltimer(mycontext['timer'])
  sock.close()

def fail_test():
  print "ERROR: waitforconn did not stop the timer"



if callfunc == "initialize":
  ip = '127.0.0.1'
  waitport = 12345
  
 
  handle = waitforconn(ip,waitport,do_nothing)
  
  # fail the test if this timer doesnt get canceled
  mycontext['timer'] = settimer(2,fail_test,[])  
  
  sock = openconn(ip,waitport)

  stopcomm(handle)
  sock.close()
  
