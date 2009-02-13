include NATLayer.py

# This forwarder uses the NATLayer protocol to multiplex connections between
# servers and clients.  The majority of work is done by 4 types of threads.
#   read_from client: reads from a client socket and writes to a buffer
#   write to client: reads from a buffer and writes to a client
#   read_from server: reads from a server, writes to a buffer
#   write to server: reads from a buffer, writes to a server
#
# Writen be Eric Kimbrel Feb 2009



# print out everything the forwarder sends / recieves
TRACE = False


# How often should we sample sockets? (Time in seconds)
SAMPLE_TIME = .05



# Track connected clients
# {client_address:{server_address:{}}}
client = {} 

# Track connected servers
# {server_address:{}}
server = {} # connected server key: value -> serverMacaddress:{}


# Read from a client
def read_from_client(client_address,server_address):
  while (True):
    
    # if this client or server is not connected break
    try:
      this_client = client[client_address][server_address]
      this_server = server[server_address]
    except KeyError:
      print "stopping read thread for client: "+client_address+" to server: "+server_address
      break
 
    # read from the client the amount specified in server_buff_size
    buffer_avialable = this_client['server_buff_size']
    data=''

    try:
      data = this_client['socket'].recv(buffer_avialable)
    except Exception, e:
      if "socket" not in str(type(e)) and "Socket" not in str(e):
        raise
      print "SocketError occured reading from client: "+client_address
      drop_client(client_address,server_address)
      print "Dropped client: "+client_address
      break #stops this thread


    # if data is non null send it to the to_server_buffer
    if (len(data) != 0):
      frame = NATFrame()
      frame.initAsDataFrame(client_address,data)
       
      if TRACE:
        print "recived "+data+" from client"

      # send the frame as a string to the outgoing buffer
      this_server['to_server_buff'].append(frame.toString())  

    #decrement server_buf_size by len(data) (make atomic)
    this_client['buff_size_lock'].acquire()
    this_client['server_buff_size'] -= len(data)
    this_client['buff_size_lock'].release()

    sleep(SAMPLE_TIME)



def write_to_client(client_address,server_address):
  while (True):
  
    # if this client or server is not connected break
    try:
      this_client = client[client_address][server_address]
      this_server = server[server_address]
    except KeyError:
      print"stopping write thread to: "+client_address+" from server: "+server_address
      break
    

    buffer = this_client['to_client_buff']

    # get the data off the to client buffer
    if len(buffer) > 0:
      data = buffer.pop()

      if TRACE:
        print "writing to client: "+data

      # write to the client
      try:
        this_client['socket'].send(data)
      except Exception, e:
        if "socket" not in str(type(e)) and "Socket" not in str(e):
          raise
        print "Client socket error occured writing to client: ",
        client_address," server: ",server_address
        drop_client(client_address,server_address)
        break;      

    
    sleep(SAMPLE_TIME)



def read_from_server(server_address):
  while (True):
    
    # if this server is not connected break
    try:
      this_server = server[server_address]
    except KeyError:
      print "stopping read thread server: "+server_address
      break

    # get the message
    frame = NATFrame()
    
    # read from the socket
    try:
      frame.initFromSocket(this_server['socket'])
    except Exception, e:
      if ("socket" not in str(type(e))) and "Socket" not in str(e) and  ("Header" not in str(e)):
        raise
      if "socket" in str(e):
        print "Socket Error reading from server: "+server_address
      elif "Header" in str(e):
        print "Header Size Error reading from server: "+server_address
      drop_server(server_address)
      break

    if TRACE:
      print "server sent: "+frame.toString()


    client_address = frame.frameMACAddress 
    client_connected = True
    try:
      this_client = client[client_address][server_address]
    except KeyError:
      print "Client: "+client_address+" requested by server: "+server_address+" is not connected"
      client_connected = False
       

    # is the client connected to this server?
    if client_connected:    
      
      # is this a data frame
      if frame.frameMesgType == DATA_FORWARD and frame.frameContentLength != 0:
        
        buffer = this_client['to_client_buff']

        # if the servers outgoingAvail is now empty send it the buffer size     
        this_client['to_client_buff_current'] =- frame.frameContentLength
        if this_client['to_client_buff_current'] < 1:
          
          size_avail = this_client['to_client_buff_MAX'] - get_buff_size(buffer)
          buff_frame = NATFrame()
          buff_frame.initAsConnBufSizeMsg(client_address,size_avail)
          this_server['to_server_buff'].append(buff_frame.toString())

        # send the message to the to_client_buff, if the client exisits
        if client_address in client:    
          buffer.append(frame.frameContent)


      # is this a CONN_TERM frame
      elif frame.frameMesgType == CONN_TERM:
        print "Server terminated connection between:\n\tServer: "+server_address+"\n\tClient: "+client_address
        drop_client(client_address,server_address)

      # is this a CONN_BUFF_SIZE message
      elif frame.frameMesgType == CONN_BUF_SIZE:
        this_client['buff_size_lock'].acquire()
        this_client['server_buff_size'] = int(frame.frameContent)       
        this_client['buff_size_lock'].release()


    sleep(SAMPLE_TIME)



# Write to a server
def write_to_server(server_address):
  while (True):
    
    # if this server is not connected break
    try:
      this_server = server[server_address]
    except KeyError:
      print "stopping write thread to server: "+server_address
      break

    # get the next message off the buffer
    if len(this_server['to_server_buff']) >0:
      outgoing_frame_str = this_server['to_server_buff'].pop()
    
      

      try:
        this_server['socket'].send(outgoing_frame_str)
      except Exception,e:
        if "socket" not in str(type(e)) and "Socket" not in str(e):
          raise
        print "Socket Error while writeing to server: "+server_address
        drop_server(server_address)
        print "dropped server: "+server_address
        break    
     
      if TRACE:
        print "sent "+outgoing_frame_str+" to server"    


    sleep(SAMPLE_TIME)


# copy a list of strings and return the size of the copy
def get_buff_size(str_list):
  list_copy = [x for x in str_list]
  total_length=0
  for str in list_copy:
    total_length= total_length + len(str)
  return total_length


#terminate a server connection
def drop_server(server_address):
  # drop all clients connected to the server
  
  # get a list of clients connected to this server
  # without iterating through the client dictionary
  clients_connected_to_server=[]
  client_address_list = client.keys()
  for client_address in client_address_list:
    if server_address in client[client_address].keys():
      clients_connected_to_server.append(client_address)
  
  for client_address in clients_connected_to_server:
    drop_client(client_address,server_address)
  

  # drop the server
  try:
    server[server_address]['socket'].close()
    del server[server_address]
  except KeyError:
    return


#terminate a client connection
def drop_client(client_address,server_address):

  try:
    client[client_address][server_address]['socket'].close()

    # remove connections from the client data structure
    del client[client_address][server_address]

    # tell the server this connection is gone
    frame = NATFrame()
    frame.initAsConnTermMsg(client_address)
    if server_address in server:
      server[server_address]['to_server_buff'].append(frame.toString())

    # if the client is connected to no one, remove it entirely
    if len(client[client_address]) < 1:
      del client[client_address]
   
  except KeyError:
    return



# Handles a new connection to the forwarder
def newconn(socket, frame):
  
  # INIT SERVER
  # TODO handle the -1 connbuff size option
  if frame.frameMesgType == INIT_SERVER:
    
    print "Connected to new server: "+frame.frameMACAddress  

    # declare a new buffer to store data from clients to the server
    buff =  []
    
    # setup the main server data structure
    server[frame.frameMACAddress] = {"socket":socket,
    "default_server_buff_size":int(frame.frameContent),"to_server_buff":buff}

    # send a response to the server
    resp = NATFrame()
    resp.initAsForwarderResponse(STATUS_CONFIRMED)
    try:
      socket.send(resp.toString())
    except Exception, e:
      if "socket" not in str(type(e)) and "Socket" not in str(e):
        raise
      drop_server(frame.frameMACAddress)
      print "SocketError occured sending Status_Confirm Response to server: "+frame.frameMACAddress
    

    # launch threads to handle this server
    settimer(0,read_from_server,[frame.frameMACAddress])
    settimer(0,write_to_server,[frame.frameMACAddress])

  # INIT CLIENT
  elif frame.frameMesgType == INIT_CLIENT:
    serverMac = frame.frameContent
    found_server = (serverMac in server)

    # is the server available
    if found_server:
      this_server = server[serverMac]
      client_address = frame.frameMACAddress
      
      print "Connected Client: "+client_address+" to server: "+serverMac

      # buffer for messages from server to client
      buff = []      

      # is the client already connected
      if client_address in client:
        client[client_address][serverMac] = {"socket":socket,
        "to_client_buff":buff,
        'to_client_buff_MAX':this_server['default_server_buff_size'],
        'to_client_buff_current':this_server['default_server_buff_size'],
        'server_buff_size':this_server['default_server_buff_size'],
        'buff_size_lock':getlock()}
      
      # is this an initial connection
      else: 
        client[frame.frameMACAddress]= {serverMac:{"socket":socket,
        "to_client_buff":buff,
        'to_client_buff_MAX':this_server['default_server_buff_size'],
        'to_client_buff_current':this_server['default_server_buff_size'],
        'server_buff_size':this_server['default_server_buff_size'],
        'buff_size_lock':getlock()}}
      
      # send a response
      resp = NATFrame()
      resp.initAsForwarderResponse(STATUS_CONFIRMED)
      try:
        socket.send(resp.toString())
      except Exception, e:
        if "socket" not in str(type(e)) and "Socket" not in str(e):
          raise
        print "SocketError occured sending Status Confirmed to client: "+client_address
        drop_client(frame.frameMACAddress,serverMac)
        print "Dropped Client: "+client_address
      
      # Tell the server it has this client
      this_server['socket'].send(frame.toString())

      # start threads to read and write from this client socket
      settimer(0,read_from_client,[client_address,serverMac])
      settimer(0,write_to_client,[client_address,serverMac])

    # The server is not available
    else:
      resp = NATFrame()
      resp.initAsForwarderResponse(STATUS_NO_SERVER)
      try:
        socket.send(resp.toString())
      except Exception,e:
        if "socket" not in str(type(e)) and "Socket" not in str(e):
          raise
        print "SocketError occured sending STATUS_NO_SERVER to client: "+frame.frameMACAddress
        drop_client(frame.frameMACAddress,serverMac)
        print frame.frameMACAddress+" has been dropped"




# Start the forwarder 
if callfunc == "initialize":
  
  # Initialize the NAT channel
  # natcon = NATConnection(FORWARDER_MAC, callargs[0], int(callargs[1]))
  natcon = NATConnection(FORWARDER_MAC,"127.0.0.1" , 12345)

  # Setup our process to handle new connections
  natcon.frameHandler = newconn
