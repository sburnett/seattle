# if there are no free events waitforconn will process additional connections
# after a free event becomes available.
#
# this test is ran with the provided echo_server

def fail_test():
  print 'test timed out'
  exitall()



def free_an_event(socks):
  mycontext['freed_an_event'] = True
  socks[0].close()
  

if callfunc == "initialize":
  
  if len(callargs) != 0 and len(callargs) != 2:
    print 'usage: enter the echo server ip and port on the command line'
    print 'enter nothing for 127.0.0.1 12345'

  max_events = 10
  mycontext['freed_an_event'] = False

  # if running locally
  if len(callargs) == 0:
    ip = '127.0.0.1'
    port = 12345
  else:
    ip = callargs[0]
    port = int(callargs[1])

  
  socks = []


  #consume all events with connections 
  for i in range(max_events - 2):  #subtract for main and socke selector
    socks.append(openconn(ip,port))  

  settimer(3,free_an_event,[socks])  
  handle = settimer(15,fail_test,[])

  #this connection should connect, but be ignored until a timer expires
  sock = openconn(ip,port)
  sock.send('hello')
  msg = sock.recv(10)
  
  canceltimer(handle)
   
  if msg != 'hello':
    print 'did not get echo'
  

  #close open sockets
  sock.close()
  for i in range(max_events -2):
    socks[i].close()
  
  
