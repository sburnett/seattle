# Tests that send will block once interall buffers are full
# no expected output


def close_it(remoteip, remoteport, sock, thishand, listenhand):
  while not mycontext['close_the_socket']:
    sleep(1)
  sock.close()





if callfunc == "initialize":
  mycontext['close_the_socket'] = False

  ip = '127.0.0.1'
  waitport = 12345

  handle = waitforconn(ip,waitport,close_it)

  sock = openconn(ip,waitport)

  sent = sock.send('test')

  sock.close()
  mycontext['close_the_socket'] = True
  stopcomm(handle)
  
  if sent != 4:
    print 'Error: sent = '+str(sent)



  
 
