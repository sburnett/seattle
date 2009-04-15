# after stopcomm is called on a waitforconn handle
# an identical waitforconn can be performed without expcetion

def do_nothing(remoteip, remoteport, sock, thishand, listenhand):
  pass




if callfunc == "initialize":
  mycontext['keep_testing'] = True
  ip = '127.0.0.1'
  waitport = 12345
  
 
  # the waitfor conn we will connect to
  handle = waitforconn(ip,waitport,do_nothing)

  stopcomm(handle)

  sleep(3) #give os time to reclaim the port

  handle = waitforconn(ip,waitport,do_nothing)
  

  stopcomm(handle)
  
