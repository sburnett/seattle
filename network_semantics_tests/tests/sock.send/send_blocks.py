# Tests that send will block once interall buffers are full
# no expected output


def close_it(remoteip, remoteport, sock, thishand, listenhand):
  while not mycontext['close_the_socket']:
    sleep(1)
  sock.close()



def stop_test(handle,sock):
  stopcomm(handle)
  sock.close()
  mycontext['close_the_socket'] = True
  exitall()  


  # check to see if the count value makes sense
  if mycontext['count'] > 500 or mycontext['count'] < 2:
    print 'ERROR: send did not block, or bufferes did not fill up'

if callfunc == "initialize":
  mycontext['close_the_socket'] = False
  mycontext['count'] = 0

  ip = '127.0.0.1'
  waitport = 12345
  filename = 'oneKfile.txt'

  handle = waitforconn(ip,waitport,close_it)

  sock = openconn(ip,waitport)

  file_obj = open(filename) 
  file_data = file_obj.read()
  file_obj.close 

  timerhandle = settimer(12,stop_test,[handle,sock])
  
  for i in range(1024):   #send until eventually it blocks
    sock.send(file_data)
   
   
  print 'exited for loop without send blocking'



  
 
