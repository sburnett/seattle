"""

Author: Armon Dadgar

Start Date: January 22nd, 2009

Description:
Provides a method of transferring data to machines behind firewalls or Network Address Translation (NAT).
Abstracts the forwarding specification into a series of classes and functions.

"""

include forwarder_advertise.py
include server_advertise.py
include Multiplexer.py
include RPC_Constants.py

# MAC Address length

# Fixed length mac address for initialization
NAT_MAC_LENGTH = 32

# Fixed length port for client initialization
NAT_PORT_LENGTH = 5

# Pad character for forwarder response and mac addresses
NAT_PAD_CHAR = "_"

# Character to split for server mac + server port
# during client init
NAT_SPLIT_CHAR = ";"

# Valid Forwarder responses to init
NAT_STATUS_LENGTH = 12

# Set the messages, justified to the proper length
NAT_STATUS_NO_SERVER = "NO_SERVER".rjust(NAT_STATUS_LENGTH, NAT_PAD_CHAR)
NAT_STATUS_BSY_SERVER = "BSY_SERVER".rjust(NAT_STATUS_LENGTH, NAT_PAD_CHAR)
NAT_STATUS_CONFIRMED = "CONFIRMED".rjust(NAT_STATUS_LENGTH, NAT_PAD_CHAR)
NAT_STATUS_FAILED = "FAILED".rjust(NAT_STATUS_LENGTH, NAT_PAD_CHAR)


# Dictionary holds NAT_Connection state
NAT_STATE_DATA = {}
NAT_STATE_DATA["mux"] = None # Initialize to nothing

# Holds the ports we are listening on
NAT_LISTEN_PORTS = {}

#########################################################################
###  Wrappers around the NAT Objects
###  These should integrate lookup methods

# Wrapper function around the NATLayer for clients        
def nat_openconn(destmac, destport, localport=None, timeout = 5, forwarderIP=None,forwarderPort=None):
  """
  <Purpose>
    Opens a connection to a server behind a NAT.
  
  <Arguments>
    destmac:
      The MAC address of the destination server
    
    destport:
      N/A, for compatibility reasons
    
    localmac:
      The MAC address used to identify this client
    
    localport:
      N/A, for compatibility reasons
    
    timeout:
      How long before timing out the forwarder connection
    
    forwarderIP:
      Force a forwarder to connect to. This will be automatically resolved if None.
      forwarderPort must be specified if this is None.
      
    forwarderPort:
      Force a forwarder port to connect to. This will be automatically resolved if None.
      forwarderIP must be specified if this is None.
      
  <Returns>
     A socket-like object that can be used for communication. 
     Use send, recv, and close just like you would an actual socket object in python.
  """ 
  # TODO: Dennis you need to tie in here to get a real forwarder IP and port
  if forwarderIP == None or forwarderPort == None:
    server_lookup(localmac)
    forwarderIP = mycontext['currforwarder'][0]
    forwarderPort = 12345

  # Create a real connection to the forwarder
  socket = openconn(forwarderIP, forwarderPort)

  # Transmit our desired MAC address and port
  destmac = destmac.rjust(NAT_MAC_LENGTH,NAT_PAD_CHAR) # Pad the mac
  destport = str(destport).rjust(NAT_PORT_LENGTH,NAT_PAD_CHAR) # Pad the port
  init_str = destmac + NAT_SPLIT_CHAR + destport # Combine the mac and port using a split character

  socket.send(init_str) # Send it

  # Get the response
  response = socket.recv(NAT_STATUS_LENGTH)
  
  # Check the response 
  if response == NAT_STATUS_CONFIRMED:
    # Everything is good to go
    return socket
  
  # Handle no server at the forwarder  
  elif response == NAT_STATUS_NO_SERVER:
    raise EnvironmentError, "Connection Refused! No server at the forwarder!"
    
  # Handle busy forwarder
  elif response == NAT_STATUS_BSY_SERVER:
    raise EnvironmentError, "Connection Refused! Forwarder Busy."
  
  # General error    
  else:  
    raise EnvironmentError, "Connection Refused!"

# Does an RPC call, returns status
def _nat_rpc_call(mux, rpc_dict):
  # Get a virtual socket
  rpcsocket = mux.openconn(RPC_VIRTUAL_IP, RPC_VIRTUAL_PORT)
  
  # Get message encoding
  rpc_mesg = RPC_encode(rpc_dict)
  
  # Request, get the response
  rpcsocket.send(rpc_mesg)
  response = RPC_decode(rpcsocket,blocking=True)
  
  # Close the socket
  try:
    rpcsocket.close()
  except:
    pass
  
  # Return the status  
  return response[RPC_REQUEST_STATUS]
  
# Does an RPC call to the forwarder to register a port
def _nat_reg_port_rpc(mux, port):
  rpc_dict = {RPC_REQUEST_ID:1,RPC_FUNCTION:RPC_REGISTER_PORT,RPC_PARAM:port}
  return _nat_rpc_call(mux,rpc_dict)

# Does an RPC call to the forwarder to deregister a port
def _nat_dereg_port_rpc(mux, port):
  rpc_dict = {RPC_REQUEST_ID:2,RPC_FUNCTION:RPC_DEREGISTER_PORT,RPC_PARAM:port}
  return _nat_rpc_call(mux,rpc_dict)

# Does an RPC call to the forwarder to register a server
def _nat_reg_server_rpc(mux, mac):
  rpc_dict = {RPC_REQUEST_ID:3,RPC_FUNCTION:RPC_REGISTER_SERVER,RPC_PARAM:mac}
  return _nat_rpc_call(mux,rpc_dict)

# Does an RPC call to the forwarder to deregister a server
def _nat_dereg_server_rpc(mux):
  rpc_dict = {RPC_REQUEST_ID:4,RPC_FUNCTION:RPC_DEREGISTER_SERVER}
  return _nat_rpc_call(mux,rpc_dict)  
  
# Wrapper function around the NATLayer for servers  
def nat_waitforconn(localmac, localport, function, forwarderIP=None, forwarderPort=None):
  """
  <Purpose>
    Allows a server to accept connections from behind a NAT.
    
  <Arguments>
    See wait for conn.

    forwarderIP:
      Force a forwarder to connect to. This will be automatically resolved if None.
      forwarderPort must be specified if this is None.
      
    forwarderPort:
      Force a forwarder port to connect to. This will be automatically resolved if None.
      forwarderIP must be specified if this is None.           
  
  <Side Effects>
    An event will be used to monitor new connections
    
  <Returns>
    A handle, this can be used with nat_stopcomm to stop listening.      
  """
  if forwarderIP == None or forwarderPort == None:
    forwarder_lookup() 
    settimer(0, server_advertise, [localmac],)
    forwarderIP = mycontext['currforwarder']
    forwarderPort = 12345 
  
  # Do we already have a mux? If not create a new one
  if NAT_STATE_DATA["mux"] == None:
    # Create a real connection to the forwarder
    socket = openconn(forwarderIP, forwarderPort)
  
    # Immediately create a multiplexer from this connection
    mux = Multiplexer(socket, {"localip":localmac, "localport":localport})

    # Register us as a server
    status = _nat_reg_server_rpc(mux, localmac)
    if not status:
      # Something is wrong, raise Exception, close socket
      socket.close()
      raise EnvironmentError, "Failed to begin listening!"
        
    # Setup the waitforconn
    mux.waitforconn(localmac, localport, function)

    # Register our wait port on the forwarder
    status = _nat_reg_port_rpc(mux, localport)
    if not status:
      # Something is wrong, raise Exception, close socket
      socket.close()
      raise EnvironmentError, "Failed to begin listening!"
     
    # Add the multiplexer to our state
    NAT_STATE_DATA["mux"] = mux
   
    # Register this port
    NAT_LISTEN_PORTS[localport] = True
   
    # Return the localport, for stopcomm
    return localport
    
  
  # We already have a mux, so just add a new listener
  else:
    # Get the mux
    mux = NAT_STATE_DATA["mux"]
    
    # Setup the waitforconn
    mux.waitforconn(localmac, localport, function)
     
    # Register our wait port on the forwarder
    _nat_reg_port_rpc(mux, localport)
      
    # Register this port
    NAT_LISTEN_PORTS[localport] = True
    
    # Return the localport, for stopcomm
    return localport
     
    
# Stops the socketReader for the given natcon  
def nat_stopcomm(port):
  """
  <Purpose>
    Stops listening on a NATConnection, opened by nat_waitforconn
    
  <Arguments>
    port:
        Handle returned by nat_waitforconn.
  
  """
  # Get the mux
  mux = NAT_STATE_DATA["mux"]
  
  if mux != None:
    if port in NAT_LISTEN_PORTS:
      mux.stopcomm(port)
      del NAT_LISTEN_PORTS[port]
    
      # De-register our port from the forwarder
      _nat_dereg_port_rpc(mux, port)
    
      # Are we listening on any ports?
      numListen = len(NAT_LISTEN_PORTS)
      if numListen == 0:
        # De-register the server entirely
        _nat_dereg_server_rpc(mux)
      
        # Close the mux, and set it to Null
        mux.close()
        NAT_STATE_DATA["mux"] = None
  
