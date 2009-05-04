# test that a call to send does not typically block, (it will block if 
# buffers are full)
#
# no expected output


def close_it(remoteip, remoteport, sock, thishand, listenhand):
  while not mycontext['close_the_socket']:
    sleep(1)
  sock.close()


def fail():
  print 'ERROR: call to send blocked'
  exitall()

if callfunc == "initialize":
  mycontext['close_the_socket'] = False

  ip = '127.0.0.1'
  waitport = 12345
 
  handle = waitforconn(ip,waitport,close_it)

  sock = openconn(ip,waitport)
  some_str = 'this call should finish without a read from the other side'

  timerhandle = settimer(1,fail,[])
  length_sent = sock.send(some_str)
  canceltimer(timerhandle)
  sock.close()
  stopcomm(handle)
  mycontext['close_the_socket'] = True
  
  if length_sent != len(some_str):
    print 'send did not return lenght of string sent'
   



  
 
