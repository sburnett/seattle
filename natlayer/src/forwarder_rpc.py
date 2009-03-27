"""
Author: Armon Dadgar, Eric Kimbrel

Date: Feb 2009

Description: 
  This forwarder uses the NATLayer protocol to multiplex connections between
  servers and clients, with the goal of providing communication with nodes
  behind a NAT

  Servers connect via a multiplexer while clients connect with real sockets.
  A virtual socket from the server and a real socekt from the client are
  put together in an exchance message method where data is exchanged.


"""


# Get the NATLayer
include NATLayer_rpc.py

# Get the RPC constants
include RPC_Constants.py

FORWARDER_STATE = {"ip":"127.0.0.1","Next_Conn_ID":0}
MAX_CLIENTS_PER_SERV = 8*2 # How many clients per server, the real number is this divided by 2
MAX_SERVERS = 8 # How man servers can connect
WAIT_INTERVAL = 3    # How long to wait after sending a status message before closing the socket
RECV_SIZE = 1024 # Size of chunks to exchange
CHECK_INTERVAL = 15  # How often to cleanup our state, e.g. remove dead multiplexers

# Lock for CONNECTIONS dictionary
CONNECTIONS_LOCK = getlock()

# Dictionary that maps Connection ID -> Dictionary of data about the connection
CONNECTIONS = {}

# Enumeration of Connection types
TYPE_MUX = 1    # Server type, or multiplexed connections
TYPE_SOCK = 2   # Single socket, client or RPC type

# Lock for MAC_ID_LOOKUP dictionary
MAC_ID_LOCK = getlock()

# Allows a reverse lookup of MAC to Connection ID
MAC_ID_LOOKUP = {}

# Controls Debug messages
DEBUG1 = True  # Prints general debug messages
DEBUG2 = True  # Prints verbose debug messages
DEBUG3 = False  # Prints Ultra verbose debug messages

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
  
  return (True, info)


# Registers a new server
def register_server(conn_id, value):
  # The value is the MAC address to register under
  # Check if this is already registered
  if value not in MAC_ID_LOOKUP:
    # Get the server info, assign the MAC
    servermacs = CONNECTIONS[conn_id]["mac"]
    servermacs.add(value)
    
    # Setup the reverse mapping, this allows clients to find the server
    MAC_ID_LOCK.acquire()  
    MAC_ID_LOOKUP[value] = conn_id
    MAC_ID_LOCK.release()
    
    return (True,None)
  
  # Something is wrong, the RPC call has failed
  else:
    return (False,None)


def _timed_dereg_server(id,mux):
  # DEBUG
  if DEBUG3: print getruntime(), "De-registering server ID#",id
  
  _safe_close(mux)
  
  CONNECTIONS_LOCK.acquire()
  try:
    # Delete the server entry
    del CONNECTIONS[id]
  except KeyError:
    # The mux may have already been cleaned up by the main thread
    pass
  
  CONNECTIONS_LOCK.release()


# De-registers a server
# If srvmac is None, totally de-register immediately
def deregister_server(conn_id,srvmac):
  # Get the server info
  serverinfo = CONNECTIONS[conn_id]
    
  # Remove the MAC address reverse lookup
  if srvmac in serverinfo["mac"]:
    # Discard this MAC address
    serverinfo["mac"].discard(srvmac)
    
    # Remove the reverse lookup
    if srvmac in MAC_ID_LOOKUP:
      MAC_ID_LOCK.acquire()  
      del MAC_ID_LOOKUP[srvmac]
      MAC_ID_LOCK.release()
 
  elif srvmac == None:
    MAC_ID_LOCK.acquire()  
    # Iterate through every mac, removing it
    for mac in serverinfo["mac"]:
      del MAC_ID_LOOKUP[mac]
    MAC_ID_LOCK.release()
    
    # Clear the set
    serverinfo["mac"].clear()
    
    
  # Close the multiplexer if there are no remaining mappings
  if len(serverinfo["mac"]) == 0:
    # Get the multiplexer
    if "mux" in serverinfo:
      mux = serverinfo["mux"]
    else:
      mux = None
  
    # Set timer to close the multiplexer in WAIT_INTERVAL(3) second
    # This is because we cannot close the connection immediately or the RPC call would fail
    settimer(WAIT_INTERVAL,_timed_dereg_server, [conn_id,mux])
  
    # DEBUG    
    if DEBUG3: print getruntime(), "Set timer to de-register server ID#",conn_id,"Time:",WAIT_INTERVAL
      
  return (True, None)


# Registers a new wait port
def reg_waitport(conn_id,value):
  # Get the server info
  serverinfo = CONNECTIONS[conn_id]
  
  # Check if this mac has a set of ports, and create one if not
  if not value["server"] in serverinfo["ports"]:
    serverinfo["ports"][value["server"]] = set()
  
  # Get the server ports
  ports = serverinfo["ports"][value["server"]]
  
  # Append to ports
  ports.add(value["port"])
  
  return (True,None)


# De-register a wait port
def dereg_waitport(conn_id,value):
  # Get the server info
  serverinfo = CONNECTIONS[conn_id]
  
  # Check if this mac has a set of ports
  if value["server"] in serverinfo["ports"]:
    # Get the server ports
    ports = serverinfo["ports"][value["server"]]
  
    # Convert value to int, and append to ports
    ports.discard(value["port"])
  
  return (True,None)


# Exchanges messages between two sockets  
def exchange_mesg(serverinfo, fromsock, tosock):
  # DEBUG
  if DEBUG3: print getruntime(), "Exchanging messages between",fromsock,"and",tosock,"for server",serverinfo
  try:
    while True:
      mesg = fromsock.recv(RECV_SIZE)
      tosock.send(mesg)
  except Exception, exp:
    # DEBUG
    if DEBUG3: print getruntime(), "Error exchanging messages between",fromsock,"and",tosock,"Error:",str(exp)
    # Something went wrong, close the read socket
    _safe_close(fromsock)
    # Decrement the connected client count
    serverinfo["num_clients"] -= 1



# Handle new clients
def new_client(conn_id, value):
  # Get the connection info
  conninfo = CONNECTIONS[conn_id]
  servermac = value["server"]
  port = value["port"]
  
  # Has the server connected to this forwarder?
  if servermac not in MAC_ID_LOOKUP:
    return (False,NAT_STATUS_NO_SERVER)
  
  # Get the server info dictionary
  serverinfo = CONNECTIONS[MAC_ID_LOOKUP[servermac]]
  
  # Check if we have reach the limit of clients
  if not serverinfo["num_clients"] < MAX_CLIENTS_PER_SERV:
    return (False,NAT_STATUS_BSY_SERVER)
  
  # Check if the server is listening on the desired port
  if not port in serverinfo["ports"][servermac]:
    return (False,NAT_STATUS_FAILED)
  
  # Try to get a virtual socket
  try:
    virtualsock = serverinfo["mux"].openconn(servermac, port,localip=conninfo["ip"],localport=conninfo["port"])
    
    # Manually send the confirmation RPC dict, since we will not return to the new_rpc function
    rpc_response = {RPC_REQUEST_STATUS:True,RPC_RESULT:NAT_STATUS_CONFIRMED}
    
    # DEBUG
    if DEBUG2: print getruntime(),"Client Conn. Successful",rpc_response
    
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
  except Exception, exp:
    # DEBUG
    if DEBUG3: print getruntime(), "Error while opening virtual socket to ",servermac,"Error:",str(exp)
    
    return (False,NAT_STATUS_FAILED)



# Handle a remote procedure call
def new_rpc(conn_id, sock):
  # If anything fails, close the socket
  try:
    # Get the RPC object
    rpc_dict = RPC_decode(sock)
    
    # DEBUG
    if DEBUG1: print getruntime(),"#"+str(conn_id),"RPC Request:",rpc_dict
    
    # Get the RPC call id
    if RPC_REQUEST_ID in rpc_dict:
      callID = rpc_dict[RPC_REQUEST_ID]
    else:
      callID = None
    
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
      # What type of connection is this?
      conn_type = CONNECTIONS[conn_id]["type"]
      
      # Check the security requirements of this function,
      # Is this connection type allowed to call the function
      allowed = conn_type in RPC_FUNCTION_SECURITY[request]
      
      if allowed:
        # Get the function
        func = RPC_FUNCTIONS[request]
    
        # Give the function the conn_id, and the value to the request
        # Store the status, and the return value
        status,retvalue = func(conn_id,value)
      
      else:
        # The request has failed, not allowed
        status = False
        retvalue = None
  
    # No request made, it has failed
    else:
      status = False
      retvalue = None
    
    # Send the status of the request
    statusdict = {RPC_REQUEST_STATUS:status,RPC_RESULT:retvalue}
    
    # Add identifier if one was specified
    if callID != None:
      statusdict[RPC_REQUEST_ID] = callID
          
    # DEBUG
    if DEBUG2: print getruntime(),"#"+str(conn_id),"RPC Response:",statusdict  
    
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
    # DEBUG
    if DEBUG1: print getruntime(),"#"+str(conn_id),"Exception in RPC Layer:",str(e)
    # Something went wrong...
    _safe_close(sock)



# Setup a new server entry
def _connection_entry(id,sock,mux,remoteip,remoteport,type):
  # Get the lock
  CONNECTIONS_LOCK.acquire()
  
  # Register this server/multiplexer
  # Store the ip,port, and set the port set
  info = {"ip":remoteip,"port":remoteport,"sock":sock,"type":type}
  
  # DEBUG
  if DEBUG3: print getruntime(), "Adding Connection #",id,info
  
  # Add type specific data
  if type == TYPE_MUX:
    info["mux"] = mux
    info["num_clients"] = 0
    info["ports"] = {} # Maps each host name to a set of listening ports
    info["mac"] = set() # Set of possible MAC addresses
    
  CONNECTIONS[id] = info
  
  # Release the lock
  CONNECTIONS_LOCK.release()


# Lock for get_conn_id
_CONN_ID_LOCK = getlock()

# Returns a connection ID, calls are serialized to prevent races
def _get_conn_id():
  # Get the lock
  _CONN_ID_LOCK.acquire()
  
  # Get the connection ID
  id = FORWARDER_STATE["Next_Conn_ID"]
  
  # Increment the global ID counter
  FORWARDER_STATE["Next_Conn_ID"] += 1
  
  # Release the lock
  _CONN_ID_LOCK.release()
  
  return id


# Handles a multiplexer dieing due to a fatal error
# Targets connection for deregistration, so as to cleanup our state as fast as possible
def _mux_internal_error(mux, errorloc, excep):
  # Extract the connection ID
  conn_id = mux.socketInfo["conn_id"]
  
  # DEGUG
  if DEBUG2: print getruntime(),"#",conn_id,"Multiplexer had fatal error in:",errorloc,"due to:",excep 
  
  # De-register this multiplexer
  deregister_server(conn_id,None)

# Handle new servers
def new_server(remoteip, remoteport, sock, thiscommhandle, listencommhandle):
  # DEBUG
  if DEBUG2: print getruntime(),"Server Conn.",remoteip,remoteport
  

  server_wait_dict = mycontext['server_wait_info']
  server_wait_dict['lock'].acquire()
  # close sockets if the connection handle is not active
  if not server_wait_dict['active']:
    if DEBUG2: print getruntime(), "Too many servers connected, quietly droping new servers"
    sock.close()
    server_wait_dict['lock'].release()
    return
  
  # stop the server wait handle if the max number of servers is connected
  # TODO, stop the forwarder from advertising when the server wait handle is stopped
  if len(CONNECTIONS)+1 >= MAX_SERVERS:
    if DEBUG2: print getruntime(),"Server Limits Reached"
    
    #removed until stopcomm issue is resolved
    #stopcomm(server_wait_dict['handle'])
    server_wait_dict['active'] = False
  
  server_wait_dict['lock'].release()

  # Get the connection ID
  id = _get_conn_id()
  
  # Initialize the multiplexing socket with this socket
  mux = Multiplexer(sock, {"localip":FORWARDER_STATE["ip"], 
                             "localport":mycontext['SERVER_PORT'],
                             "remoteip":remoteip,
                             "remoteport":remoteport,
                             "conn_id":id}) # Inject the ID into the socketInfo, for error handling
  
  # Assign our custom error delegate
  mux.setErrorDelegate(_mux_internal_error)
  
  # Helper wrapper function
  def rpc_wrapper(remoteip, remoteport, client_sock, thiscommhandle, listencommhandle):
    new_rpc(id, client_sock)
  
  # Set the RPC waitforconn
  mux.waitforconn(RPC_VIRTUAL_IP, RPC_VIRTUAL_PORT, rpc_wrapper)
  
  # Create an entry for the server
  _connection_entry(id,sock,mux,remoteip,remoteport,TYPE_MUX)



# Handles a new incoming connection, for non-servers
# This is for RPC calls and new clients
def inbound_connection(remoteip, remoteport, sock, thiscommhandle, listencommhandle):
  # DEBUG
  if DEBUG2: print getruntime(),"Inbound Conn.",remoteip,remoteport
  
  # Get the connection ID
  id = _get_conn_id()
  
  # Create an entry for the connection
  _connection_entry(id,sock,None,remoteip,remoteport,TYPE_SOCK)
  
  # Trigger a new RPC call
  new_rpc(id, sock)
  
  # Cleanup the connection
  CONNECTIONS_LOCK.acquire()
  del CONNECTIONS[id]
  CONNECTIONS_LOCK.release()
  
  # DEBUG
  if DEBUG3: print getruntime(), "Closed inbound connection #",id
  


# Main function
def main():
  # Forwarder IP
  ip = getmyip()
  FORWARDER_STATE["ip"] = ip
  
  # Setup a port for servers to connect
  server_wait_handle = waitforconn(ip, mycontext['SERVER_PORT'], new_server)
  mycontext['server_wait_info']={'handle':server_wait_handle,'active':True,
                                 'servers_connected':0, 'lock':getlock()}

  # Setup a port for clients to connect
  client_wait_handle = waitforconn(ip, mycontext['CLIENT_PORT'], inbound_connection)
  
  # DEBUG
  if DEBUG1: print getruntime(),"Forwarder Started on",ip
  
  # Periodically check the multiplexers, see if they are alive
  while True:
    sleep(CHECK_INTERVAL)
    
    # DEBUG
    if DEBUG2: print getruntime(), "Polling for dead connections."
    
    # Check each multiplexer
    for (id, info) in CONNECTIONS.items():
      # Check server type connections for their status
      if info["type"] == TYPE_MUX:
        mux = info["mux"]
        status = mux.connectionInit
      
        # Check if the mux is no longer initialized
        if not status:
          # DEBUG
          if DEBUG1: print getruntime(),"Connection #",id,"dead. Removing..."
          
          # De-register this server
          deregister_server(id, None)
    
    # if a stopcomm was called check and see if we can do a new waitforconn
    sleep(WAIT_INTERVAL) #make sure servers are disconnected
    server_wait_dict = mycontext['server_wait_info']
    server_wait_dict['lock'].acquire()
    if (not server_wait_dict['active']) and (len(CONNECTIONS) < MAX_SERVERS):
      #commented out until stopcomm issue is resolved
      #server_wait_dict['handle'] = waitforconn(ip,mycontext['SERVER_PORT'],new_server)
      print 'allowing new servers to connect'
      server_wait_dict['active'] = True
    server_wait_dict['lock'].release()



# Dictionary maps valid RPC calls to internal functions
RPC_FUNCTIONS = {RPC_EXTERNAL_ADDR:connection_info, 
                  RPC_REGISTER_SERVER:register_server,
                  RPC_DEREGISTER_SERVER:deregister_server,
                  RPC_REGISTER_PORT:reg_waitport,
                  RPC_DEREGISTER_PORT:dereg_waitport,
                  RPC_CLIENT_INIT:new_client}
                  
# This dictionary defines the security requirements for a function
# So that it is handled in new_rpc rather than in every RPC function
RPC_FUNCTION_SECURITY = {RPC_EXTERNAL_ADDR:set([TYPE_MUX, TYPE_SOCK]), # Both types of connections can use this function
                  RPC_REGISTER_SERVER:set([TYPE_MUX]), # The registration/deregistration functions are only for servers
                  RPC_DEREGISTER_SERVER:set([TYPE_MUX]),
                  RPC_REGISTER_PORT:set([TYPE_MUX]),
                  RPC_DEREGISTER_PORT:set([TYPE_MUX]),
                  RPC_CLIENT_INIT:set([TYPE_SOCK])}  # Only a client socket can call this


# Check if we are suppose to run
if callfunc == "initialize":
  
  if len(callargs) != 2:
    print ' usage: forwarder_rpc.py SERVER_PORT CLIENT_PORT'
    exitall()

  mycontext['SERVER_PORT'] = int(callargs[0])  # What real port to listen on for servers
  mycontext['CLIENT_PORT'] = int(callargs[1])  # What real port to listen on for clients
  
  main()
