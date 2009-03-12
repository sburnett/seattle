
# Get the NATLayer
include NATLayer.py

# Get the RPC constants
include RPC_Constants.py

FORWARDER_STATE = {"ip":"127.0.0.1","Next_Conn_ID":0}
SERVER_PORT = 12345  # What real port to listen on for servers
CLIENT_PORT = 23456  # What real port to listen on for clients
MAX_CLIENTS_PER_SERV = 8*2 # How many clients per server, the real number is this divided by 2
WAIT_INTERVAL = 3    # How long to wait after sending a status message before closing the socket
RECV_SIZE = 1024 # Size of chunks to exchange
CHECK_INTERVAL = 60  # How often to check if the Multiplexers are still alive

# Dictionary that maps Connection ID -> Dictionary of data about the server
CONNECTED_SERVERS = {}

# Allows a reverse lookup of MAC to Connection ID
MAC_ID_LOOKUP = {}

# Client length
CLIENT_INIT_LENGTH = NAT_MAC_LENGTH + NAT_PORT_LENGTH + len(NAT_SPLIT_CHAR)

# Safely closes a socket
def _safe_close(sock):
  try:
    sock.close()
  except:
    pass

# Returns the servers IP and Port to the server
def server_info(conn_id, value):
  # Get the server info
  serverinfo = CONNECTED_SERVERS[conn_id]

  # Package the requested info
  info = {"ip":serverinfo["ip"],"port":serverinfo["port"]}
  
  # Convert the dictionary to a string
  return (True, str(info))

# Registers a new server
def register_server(conn_id, value):
  # The value is the MAC address to register under
  # Check if this is already registered
  if value not in MAC_ID_LOOKUP:
    # Setup the reverse mapping, this allows clients to find the server
    MAC_ID_LOOKUP[value] = conn_id
    
    # Get the server info, assign the MAC
    serverinfo = CONNECTED_SERVERS[conn_id]
    serverinfo["mac"] = value
    
    return (True,None)
  
  # Something is wrong, the RPC call has failed
  else:
    return (False,None)
    
# De-registers a server
def deregister_server(conn_id,value):
  # Get the server info
  serverinfo = CONNECTED_SERVERS[conn_id]

  # Remove the MAC address reverse lookup
  if "mac" in serverinfo:
    mac = serverinfo["mac"]
    if mac in MAC_ID_LOOKUP:
      del MAC_ID_LOOKUP[mac]

  # Close the multiplexer
  if "mux" in serverinfo:
    mux = serverinfo["mux"]
    _safe_close(mux)
    
      
  # Delete the server entry
  del CONNECTED_SERVERS[conn_id]

  return (True, None)

# Registers a new wait port
def reg_waitport(conn_id,value):
  # Get the server info
  serverinfo = CONNECTED_SERVERS[conn_id]
  
  # Get the server ports
  ports = serverinfo["ports"]
  
  # Convert value to int, and append to ports
  new_port = int(value)
  ports.add(new_port)
  
  return (True,None)

# De-register a wait port
def dereg_waitport(conn_id,value):
  # Get the server info
  serverinfo = CONNECTED_SERVERS[conn_id]
  
  # Get the server ports
  ports = serverinfo["ports"]
  
  # Convert value to int, and append to ports
  old_port = int(value)
  ports.discard(old_port)
  
  return (True,None)

# Handle a remote procedure call
def new_rpc(conn_id, remoteip, remoteport, sock):
  # If anything fails, close the socket
  try:
    # Get the server info
    serverinfo = CONNECTED_SERVERS[conn_id]
  
    # Get the RPC object
    rpc_dict = RPC_decode(sock)
    
    # DEBUG
    print "RPC Request:",rpc_dict
    
    # Get the RPC call id
    callID = rpc_dict[RPC_REQUEST_ID]
    
    # Get the requested function
    if RPC_FUNCTION in rpc_dict:
      request = rpc_dict[RPC_FUNCTION]
    else:
      request = None
    
    # Get the value, this is the parameter to the function
    if RPC_PARAM in rpc_dict:
      value = rpc_dict[RPC_PARAM]
    else:
      value = None
    
    # Determine if there are remaining RPC requests
    if RPC_ADDI_REQ in rpc_dict:
      additional = rpc_dict[RPC_ADDI_REQ]
    else:
      additional = False
  
    # If the request exists, call the function
    if request in RPC_FUNCTIONS:
      func = RPC_FUNCTIONS[request]
    
      # Give the function the conn_id, and the value to the request
      # Store the status, and the return value
      status,retvalue = func(conn_id,value)
  
    # No request made, it has failed
    else:
      status = False
      retvalue = None
    
    # Send the status of the request
    statusdict = {RPC_REQUEST_ID:callID,RPC_REQUEST_STATUS:status,RPC_RESULT:retvalue}
  
    # Encode the RPC response dictionary
    response = RPC_encode(statusdict) 
  
    # Send the response
    sock.send(response)
  
    # Check if there is more RPC calls
    if additional:
      # Recurse
      new_rpc(conn_id, remoteip, remoteport, sock)
    else:
      # Wait for the client to receive the response
      sleep(WAIT_INTERVAL)
      
      # Close the socket
      _safe_close(sock)
      
  except Exception, e:
    print "Exception in RPC Layer:",str(e)
    # Something went wrong...
    _safe_close(sock)
  
# Handle new servers
def new_server(remoteip, remoteport, sock, thiscommhandle, listencommhandle):
  # Get the connection ID
  id = FORWARDER_STATE["Next_Conn_ID"]
  
  # Increment the global ID counter
  FORWARDER_STATE["Next_Conn_ID"] += 1
  
  # Initialize the multiplexing socket with this socket
  mux = Multiplexer(sock, {"localip":FORWARDER_STATE["ip"], 
                             "localport":SERVER_PORT,
                             "remoteip":remoteip,
                             "remoteport":remoteport})
  
  # Helper wrapper function
  def rpc_wrapper(remoteip, remoteport, client_sock, thiscommhandle, listencommhandle):
    new_rpc(id, remoteip, remoteport, client_sock)
  
  # Set the RPC waitforconn
  mux.waitforconn(FORWARDER_STATE["ip"], RPC_VIRTUAL_PORT, rpc_wrapper)
  
  # Register this server/multiplexer
  # Store the ip,port, and set the port set
  info = {"mux":mux,"num_clients":0,"ports":set(),"ip":remoteip,"port":remoteport}
  CONNECTED_SERVERS[id] = info

# Sends a message, waits, then closes socket
def _send_wait_close(sock, mesg):
  sock.send(mesg)
  sleep(WAIT_INTERVAL)
  _safe_close(sock)
  
# Handle new clients
def new_client(remoteip, remoteport, sock, thiscommhandle, listencommhandle):
  # Get the key info
  try:
    # Get the client init message
    mesg = sock.recv(CLIENT_INIT_LENGTH)
    (servermac, port) = mesg.split(NAT_SPLIT_CHAR)
    port = int(port)
  except:
    # On failure, send the failed message
    _send_wait_close(sock,NAT_STATUS_FAILED)
    return
  
  # Has the server connected to this forwarder?
  if servermac not in MAC_ID_LOOKUP:
    _send_wait_close(sock,NAT_STATUS_NO_SERVER)
    return
    
  # Get the server info dictionary
  serverinfo = CONNECTED_SERVERS[MAC_ID_LOOKUP[servermac]]
  
  # Check if we have reach the limit of clients
  if not serverinfo["num_clients"] < MAX_CLIENTS_PER_SERV:
    _send_wait_close(sock,NAT_STATUS_BSY_SERVER)
    return
    
  # Check if the server is listening on the desired port
  if not port in serverinfo["ports"]:
    _send_wait_close(sock,NAT_STATUS_FAILED)
    return
    
  # Try to get a virtual socket
  try:
    virtualsock = serverinfo["mux"].openconn(serverinfo["ip"], port)
    
    # Send a confirmed message
    sock.send(NAT_STATUS_CONFIRMED)
  except:
    _send_wait_close(sock,NAT_STATUS_FAILED)
    return
    
  # Exchanges messages  
  def exchange_mesg(serverinfo, fromsock, tosock):
    try:
      while True:
        mesg = fromsock.recv(RECV_SIZE)
        tosock.send(mesg)
    except:
      # Something went wrong, close both sockets
      _safe_close(fromsock)
      _safe_close(tosock)
      # Decrement the connected client count
      serverinfo["num_clients"] -= 1
  
  # Add 2 client connections (really just 1)
  # This is because each exchange_mesg will decrement num_clients 
  # So there will be 2 decrements
  serverinfo["num_clients"] += 2
  
  # Spawn 2 threads to exchange the messages
  settimer(.1, exchange_mesg,[serverinfo,virtualsock,sock])
  settimer(.2, exchange_mesg,[serverinfo,sock,virtualsock])
  
# Main function
def main():
  # Forwarder IP
  ip = getmyip()
  FORWARDER_STATE["ip"] = ip
  
  # Setup a port for servers to connect
  server_wait_handle = waitforconn(ip, SERVER_PORT, new_server)
  
  # Setup a port for clients to connect
  client_wait_handle = waitforconn(ip, CLIENT_PORT, new_client)
  
  # Periodically check the multiplexers, see if they are alive
  while True:
    sleep(CHECK_INTERVAL)
    
    # Check each multiplexer
    for (id, info) in CONNECTED_SERVERS.items():
      mux = info["mux"]
      status = mux.connectionInit
      
      # Check if the mux is no longer initialized
      if not status:
        # De-register this server
        deregister_server(id, None)


# Dictionary maps valid RPC calls to internal functions
RPC_FUNCTIONS = {RPC_EXTERNAL_ADDR:server_info, 
                  RPC_REGISTER_SERVER:register_server,
                  RPC_DEREGISTER_SERVER:deregister_server,
                  RPC_REGISTER_PORT:reg_waitport,
                  RPC_DEREGISTER_PORT:dereg_waitport}

# Check if we are suppose to run
if callfunc == "initialize":
  main()
