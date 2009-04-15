# if there are no free events waitforconn will not except further connections

def echo(remoteip, remoteport, sock, thishand, listenhand):
  msg = sock.recv(3)
  sock.send(msg)
  sock.close()




if callfunc == "initialize":
  max_events = 10

  ip = '127.0.0.1'
  waitport = 12345
  socks = []
 
  # the waitfor conn we will connect to
  handle = waitforconn(ip,waitport,echo)

  for i in range(max_events):
    socks.append(openconn(ip,waitport))
  

  try:
    one_more_socket = openconn(ip,waitport)
  except:
    pass
  else:
    print 'ERROR: waitforconn accepted connection with no free events'
    one_more_socket.close()

  stopcomm(handle)
  

  for i in range(max_events):
    socks[i].close() 
