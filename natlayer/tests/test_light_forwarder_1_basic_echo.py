include NATLayer.py


# set up a server to echo client messages
def run_server():
  socket = openconn(mycontext['forwarder_ip'],mycontext['forwarder_server_port']                    ,localip=mycontext['server_ip']
                    ,localport=mycontext['server_port'])

  socket.send('SERVER_MAC__')
  
  


  data = socket.recv(100)
  if data != 'CONFIRMED':
    raise Exception, 'Could not connect server to forwarder'

  mux = Multiplexer(socket, {"localip":mycontext['server_ip'],
                             "localport":mycontext['server_port'],
                             "remoteip":mycontext['forwarder_ip'],
                             "remoteport":mycontext['forwarder_server_port']})

  mycontext['mux'] = mux
  mycontext['serversock'] = socket
  mux.waitforconn(mycontext['server_ip'],mycontext['server_port'],echo)
  


# echo client messages
def echo(remoteip,remoteport,sock,thiscommhandle,listencommhandle):
  for i in range(10):
    data = sock.recv(1024)
    sock.send(data)
  sock.close()


# a simple client says hi 10 times
def run_client():
  client_socket = openconn(mycontext['forwarder_ip'],mycontext['forwarder_client_port'])
 
  mycontext['cl_socket'] = client_socket

  client_socket.send("SERVER_MAC__")
  data = client_socket.recv(1024)
  if data == 'FAILED':
    raise Exception, 'Failed to connect client to server'

  for i in range(10):
    client_socket.send("hello")
    data =  client_socket.recv(1024)
    
  end_test()
  canceltimer(mycontext['timer'])


# timer ran out, fail the test
def fail():
  print "Test timed out"
  end_test()


# close everything
# if the test has already failed this may cause extra exceptions
def end_test():
  mycontext['cl_socket'].close()
  mycontext['mux'].stopcomm(mycontext['server_port'])
  mycontext['serversock'].close()
  
  
# run one server and one client that bounce
# a message back and forth 10 times
if callfunc == 'initialize':

  #forwarder values
  mycontext['forwarder_ip'] = '127.0.0.1'
  mycontext['forwarder_server_port'] = 12345
  mycontext['forwarder_client_port'] = 54321

  #server values
  mycontext['server_ip'] = '127.0.0.1'
  mycontext['server_port'] = 63133

  # set a timer to fail 
  mycontext['timer'] = settimer(20,fail,[])


  #start the server listening
  #settimer(0,run_server,[])
  server_handle = nat_waitforconn('SERVERSERVER',mycontext['server_port'],echo,
                           forwarderIP=mycontext['forwarder_ip'],
                           forwarderPort=mycontext['forwarder_server_port'])



  #start the client

  sleep(2)  #give the server a second to start
  #settimer(0,run_client,[])


  client_sock = nat_openconn('SERVERSERVER',21343, 
             forwarderIP=mycontext['forwarder_ip'],
             forwarderPort=mycontext['forwarder_client_port'])

  for i in range(10):
    client_socket.send("hello")
    data =  client_socket.recv(1024)
    if data != 'hello':
      print 'incorect data returned from echo: '+data
  client_sock.close()

  
  
  nat_stopcomm(server_handle)
  
