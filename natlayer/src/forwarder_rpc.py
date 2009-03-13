
# Get the NATLayer
include NATLayer_rpc.py

# Get the RPC constants
include RPC_Constants.py

FORWARDER_STATE = {"ip":"127.0.0.1","Next_Conn_ID":0}
SERVER_PORT = 12345  # What real port to listen on for servers
CLIENT_PORT = 23456  # What real port to listen on for clients
MAX_CLIENTS_PER_SERV = 8*2 # How many clients per server, the real number is this divided by 2
WAIT_INTERVAL = 3    # How long to wait after sending a status message before closing the socket
RECV_SIZE = 1024 # Size of chunks to exchange
CHECK_INTERVAL = 60  # How often to cleanup our state, e.g. remove dead multiplexers

# Dictionary that maps Connection ID -> Dictionary of data about the connection
CONNECTIONS = {}

# Allows a reverse lookup of MAC to Connection ID
MAC_ID_LOOKUP = {}

# Safely closes a socket
def _safe_close(sock):
  try:
    sock.close()
  except:
    pass


# Returns the connections IP and Port to the client
def connection_info(conn_id, value):
  # Get the server info
  serverinfo = CONNECTIONS[conn_id]
  
  # Package the requested info
  info = {"ip":serverinfo["ip"],"port":serverinfo["port"]}
  
  # Convert the dictionary to a string
  return (True, str(info))


# Registers a new server
def register_server(conn_id, value):
  # The value is the MAC address to register under
  # Check if this is already registered
  if value not in MAC_ID_LOOKUP:
    # Get the server info, assign the MAC
    serverinfo = CONNECTIONS[conn_id]
    serverinfo["mac"] = value
    
    # Make sure this is a server typed connection
    if serverinfo["type"] != "server":
      return (False,None)
      
    # Setup the reverse mapping, this allows clients to find the server
    MAC_ID_LOOKUP[value] = conn_id
    
    return (True,None)
  
  # Something is wrong, the RPC call has failed
  else:
    return (False,None)


def _timed_dereg_server(id,mux):
  _safe_close(mux)
  try:
    # Delete the server entry
    del CONNECTIONS[id]
  except KeyError:
    # The mux may have already been cleaned up by the main thread
    pass


# De-registers a server
def deregister_server(conn_id,value=None):
  # Get the server info
  serverinfo = CONNECTIONS[conn_id]
  
  # Make sure this is a server typed connection
  if serverinfo["type"] != "server":
    return (False,None)
    
  # Remove the MAC address reverse lookup
  if "mac" in serverinfo:
    mac = serverinfo["mac"]
    if mac in MAC_ID_LOOKUP:
      del MAC_ID_LOOKUP[mac]
  
  # Close the multiplexer
  if "mux" in serverinfo:
    mux = serverinfo["mux"]
  else:
    mux = None
  
  # Set timer to close the multiplexer in WAIT_INTERVAL(3) second
  # This is because we cannot close the connection immediately or the RPC call would fail
  settimer(WAIT_INTERVAL,_timed_dereg_server, [conn_id,mux])    
      
  return (True, None)


# Registers a new wait port
def reg_waitport(conn_id,value):
  # Get the server info
  serverinfo = CONNECTIONS[conn_id]
  
  # Make sure this is a server typed connection
  if serverinfo["type"] != "server":
    return (False,None)
  
  # Get the server ports
  ports = serverinfo["ports"]
  
  # Convert value to int, and append to ports
  ports.add(value)
  
  return (True,None)


# De-register a wait port
def dereg_waitport(conn_id,value):
  # Get the server info
  serverinfo = CONNECTIONS[conn_id]
  
  # Make sure this is a server typed connection
  if serverinfo["type"] != "server":
    return (False,None)
  
  # Get the server ports
  ports = serverinfo["ports"]
  
  # Convert value to int, and append to ports
  ports.discard(value)
  
  return (True,None)


# Exchanges messages between two sockets  
def exchange_mesg(serverinfo, fromsock, tosock):
  try:
    while True:
      mesg = fromsock.recv(RECV_SIZE)
      tosock.send(mesg)
  except Exception, exp:
    # Something went wrong, close both sockets
    _safe_close(fromsock)
    _safe_close(tosock)
    # Decrement the connected client count
    serverinfo["num_clients"] -= 1



# Handle new clients
def new_client(conn_id, value):
  # Get the connection info
  conninfo = CONNECTIONS[conn_id]
  servermac = value["server"]
  port = value["port"]
  
  # Make sure this is a client typed connection
  if conninfo["type"] != "client":
    return (False,None)
  
  # Has the server connected to this forwarder?
  if servermac not in MAC_ID_LOOKUP:
    return (False,NAT_STATUS_NO_SERVER)
  
  # Get the server info dictionary
  serverinfo = CONNECTIONS[MAC_ID_LOOKUP[servermac]]
  
  # Check if we have reach the limit of clients
  if not serverinfo["num_clients"] < MAX_CLIENTS_PER_SERV:
    return (False,NAT_STATUS_BSY_SERVER)
  
  # Check if the server is listening on the desired port
  if not port in serverinfo["ports"]:
    return (False,NAT_STATUS_FAILED)
  
  # Try to get a virtual socket
  try:
    virtualsock = serverinfo["mux"].openconn(serverinfo["ip"], port,localip=conninfo["ip"],localport=conninfo["port"])
    
    # Manually send the confirmation RPC dict, since we will not return to the new_rpc function
    rpc_response = {RPC_REQUEST_STATUS:True,RPC_RESULT:NAT_STATUS_CONFIRMED}
    conninfo["sock"].send(RPC_encode(rpc_response))
    
    # Add 2 client connections (really just 1)
    # This is because each exchange_mesg will decrement num_clients 
    # So there will be 2 decrements
    serverinfo["num_clients"] += 2
    
    # Spawn a thread to exchange the messages between the server and client
    settimer(.2, exchange_mesg,[serverinfo,virtualsock,conninfo["sock"]])
    
    # Call exchange message to do sent the messages between the client and the server
    exchange_mesg(serverinfo,conninfo["sock"],virtualsock)
  
    # We will only reach this point after exchange_mesg terminated, so the socket is closed
    # However, we will return normally, and new_rpc will catch an exceptiton
    return (True,NAT_STATUS_CONFIRMED)
  except:
    return (False,NAT_STATUS_FAILED)



# Handle a remote procedure call
def new_rpc(conn_id, sock):
  # If anything fails, close the socket
  try:
    # Get the RPC object
    rpc_dict = RPC_decode(sock)
    
    # DEBUG
    print getruntime(),"RPC Request:",rpc_dict
    
    # Get the RPC call id
    if RPC_REQUEST_ID in rpc_dict:
      callID = rpc_dict[RPC_REQUEST_ID]
    else:
      callID = 0
    
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
    
    # DEBUG
    # print "RPC Response:",statusdict  
    
    # Encode the RPC response dictionary
    response = RPC_encode(statusdict) 
  
    # Send the response
    sock.send(response)
  
    # Check if there is more RPC calls
    if additional:
      # Recurse
      new_rpc(conn_id, sock)
    else:
      # Wait for the client to receive the response
      sleep(WAIT_INTERVAL)
      
      # Close the socket
      _safe_close(sock)
      
  except Exception, e:
    print "Exception in RPC Layer:",str(e)
    # Something went wrong...
    _safe_close(sock)



# Setup a new server entry
def _connection_entry(id,sock,mux,remoteip,remoteport,type):
  # Register this server/multiplexer
  # Store the ip,port, and set the port set
  info = {"ip":remoteip,"port":remoteport,"sock":sock,"type":type}
  
  # Add type specific data
  if type == "server":
    info["mux"] = mux
    info["num_clients"] = 0
    info["ports"] = set()
    
  CONNECTIONS[id] = info



# Handle new servers
def new_server(remoteip, remoteport, sock, thiscommhandle, listencommhandle):
  # DEBUG
  print getruntime(),"Server Conn.",remoteip,remoteport
  
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
    new_rpc(id, client_sock)
  
  # Set the RPC waitforconn
  mux.waitforconn(RPC_VIRTUAL_IP, RPC_VIRTUAL_PORT, rpc_wrapper)
  
  # Create an entry for the server
  _connection_entry(id,sock,mux,remoteip,remoteport,"server")



# Handles a new incoming connection, for non-servers
# This is for RPC calls and new clients
def inbound_connection(remoteip, remoteport, sock, thiscommhandle, listencommhandle):
  # DEBUG
  # print getruntime(),"Inbound Conn.",remoteip,remoteport
  
  # Get the connection ID
  id = FORWARDER_STATE["Next_Conn_ID"]
  
  # Increment the global ID counter
  FORWARDER_STATE["Next_Conn_ID"] += 1
  
  # Create an entry for the connection
  _connection_entry(id,sock,None,remoteip,remoteport,"client")
  
  # Trigger a new RPC call
  new_rpc(id, sock)
  
  # Cleanup the connection
  del CONNECTIONS[id]
  


# Main function
def main():
  # Forwarder IP
  ip = getmyip()
  FORWARDER_STATE["ip"] = ip
  
  # Setup a port for servers to connect
  server_wait_handle = waitforconn(ip, SERVER_PORT, new_server)
  
  # Setup a port for clients to connect
  client_wait_handle = waitforconn(ip, CLIENT_PORT, inbound_connection)
  
  # DEBUG
  print getruntime(),"Forwarder Started"
  
  # Periodically check the multiplexers, see if they are alive
  while True:
    sleep(CHECK_INTERVAL)
    print getruntime(), "Polling for dead connections."
    
    # Check each multiplexer
    for (id, info) in CONNECTIONS.items():
      # Check server type connections for their status
      if info["type"] == "server":
        mux = info["mux"]
        status = mux.connectionInit
      
        # Check if the mux is no longer initialized
        if not status:
          print "Connection #",id,"dead. Removing..."
          # De-register this server
          deregister_server(id, None)



# Dictionary maps valid RPC calls to internal functions
RPC_FUNCTIONS = {RPC_EXTERNAL_ADDR:connection_info, 
                  RPC_REGISTER_SERVER:register_server,
                  RPC_DEREGISTER_SERVER:deregister_server,
                  RPC_REGISTER_PORT:reg_waitport,
                  RPC_DEREGISTER_PORT:dereg_waitport,
                  RPC_CLIENT_INIT:new_client}


# Check if we are suppose to run
if callfunc == "initialize":
  main()
