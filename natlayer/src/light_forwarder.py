include NATLayer.py



FORWARDER_VERSION = '1.0'
MAX_RECV = 1024

MAX_SERVER_CONNECTIONS = 10
MAX_CLIENT_CONNECTIONS = 40   #this number is actually N*2 for N clients

MAC_LENGTH = 12

connected_servers_dict ={}  #MAC:(multiplexer,ip,port,sock)
connected_clients_count = 0


# pass data from a server socket to a client socket
def forward(from_socket,to_socket,server_mac):
  while True:
    
    try:
      data = from_socket.recv(MAX_RECV)
      print "FORWARDING "+data
      
      to_socket.send(data)
    except Exception, e:
      print str(e)
      mycontext['client_count_lock'].acquire()
      mycontext['client_count'] = mycontext['client_count'] -1
      mycontext['client_count_lock'].release()
      return

    # TODO need to re-factor things so that i can remove servers at some point




# handle new server connections
# TODO dont allow clients to connect over the limit
def newserver(remoteip, remoteport, sock, thiscommhandle
            , listencommhandle):

  #initialize the multiplexing socket with this socket
  mux = Multiplexer(sock, {"localip":mycontext['forwarder_ip'], 
                             "localport":mycontext['forwarder_server_port'],
                             "remoteip":remoteip,
                             "remoteport":remoteport})

  server_mac = sock.recv(MAC_LENGTH)

  # TODO pass this on to the server
  if len(server_mac) != MAC_LENGTH:
    print "Invalid MAC recieved: "+server_mac
    return
  
  #add this server to the dict of servers
  connected_servers_dict[server_mac]= {'mux':mux,
                                     'ip':remoteip,
                                     'port':remoteport,
                                     'sock':sock}

  print connected_servers_dict.keys()

  #TODO Does the sever need some kind of acknowledgement
  sock.send('CONFIRMED')
  

# handle new client connections
# Don't allow servers to connect over the limit
def newclient(remoteip, remoteport, client_sock, thiscommhandle
            , listencommhandle):
 
  # should get servermac;clientmac 
  server_mac = client_sock.recv(1024)

  print "client connecting to "+server_mac

  # TODO, pass this onto the client
  if len(server_mac) != MAC_LENGTH:
    print "Invalid MAC recieve: "+server_mac
    client_sock.send('FAILED')
    return

  
  #TODO, pass this back to the client
  if server_mac not in connected_servers_dict:
    print "Server requested is not present"
    client_sock.send('FAILED')
    return
 
  server_ip = connected_servers_dict[server_mac]['ip']
  server_port = connected_servers_dict[server_mac]['port']
  print server_ip+" "+str(server_port)

  # the remote_ip and port are passed into openconn
  # this is ok because the socket is VIRTUAL i.e. it is 
  # conected to this server, not the specified port:ip
  server_sock = connected_servers_dict[server_mac]['mux'].openconn(
                                          server_ip,server_port)
  
  client_sock.send('CONFIRMED')

  # start threads to communicate between this client and server
  mycontext['client_count_lock'].acquire()
  mycontext['client_count'] = mycontext['client_count'] +2  # +1 per thread
  mycontext['client_count_lock'].release()
  settimer(0,forward,[client_sock,server_sock,server_mac])
  settimer(0,forward,[server_sock,client_sock,server_mac])






# launch the forwarder
if callfunc == 'initialize':
  print "beraber forwarder "+FORWARDER_VERSION
  
  mycontext['forwarder_ip'] = '127.0.0.1'
  mycontext['forwarder_server_port'] = 12345
  mycontext['forwarder_client_port'] = 54321
  mycontext['client_count'] = 0
  mycontext['client_count_lock'] = getlock()

  # establish connections with a  server
  waitforconn(mycontext['forwarder_ip'],mycontext['forwarder_server_port']
                                           ,newserver)
  
  # establish connections with clients
  waitforconn(mycontext['forwarder_ip'],mycontext['forwarder_client_port']
                                           ,newclient)
