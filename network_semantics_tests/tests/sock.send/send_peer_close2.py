# Tests tests the behavior of a call to send() that is blocking
# after close() is called by a peer, an exception should be thrown
#
# no expected output


def close_it(remoteip, remoteport, sock, thishand, listenhand):
  while not mycontext['close_the_socket']:
    sleep(1)
  sock.close()

def close_the_socket():
  mycontext['close_the_socket'] = True

def stop_test(handle,sock):
  stopcomm(handle)
  sock.close()
  
def fail():
  print 'ERROR: THE SOCKET BLOCKED WITHOUT AN EXCEPTION'


if callfunc == "initialize":
  mycontext['close_the_socket'] = False

  ip = '127.0.0.1'
  waitport = 12345
  filename = 'oneKfile.txt'

  handle = waitforconn(ip,waitport,close_it)

  sock = openconn(ip,waitport)

  file_obj = open(filename) 
  file_data = file_obj.read()
  file_obj.close 

  settimer(12,close_the_socket,[])
  failtimer = settimer(15,fail,[])

  for i in range(1024):   #send until eventually it blocks
    try:
      sock.send(file_data)
    except Exception,e:
      canceltimer(failtimer)
      stop_test(handle,sock)  #got the exception, stop the test
      break
   



  
 
