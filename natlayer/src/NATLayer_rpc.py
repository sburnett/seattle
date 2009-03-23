"""

Author: Armon Dadgar

Start Date: January 22nd, 2009

Description:
Provides a method of transferring data to machines behind firewalls or Network Address Translation (NAT).
Abstracts the forwarding specification into a series of classes and functions.

"""

include forwarder_advertise.py
include server_advertise.py
include deserialize.py
include Multiplexer.py
include RPC_Constants.py

# Set the messages
NAT_STATUS_NO_SERVER = "NO_SERVER"
NAT_STATUS_BSY_SERVER = "BSY_SERVER"
NAT_STATUS_CONFIRMED = "CONFIRMED"
NAT_STATUS_FAILED = "FAILED"


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
   # server_lookup(localmac)
   # forwarderIP = mycontext['currforwarder'][0]
   # forwarderPort = 12345
   forwarderIP, forwarderPort = server_lookup(localmac)

  # Create a real connection to the forwarder
  socket = openconn(forwarderIP, forwarderPort)

  # Create an RPC request
  rpc_dict = {RPC_FUNCTION:RPC_CLIENT_INIT,RPC_PARAM:{"server":destmac,"port":destport}}

  # Send the RPC request
  socket.send(RPC_encode(rpc_dict)) 

  # Get the response
  response = RPC_decode(socket)
  
  # Check the response 
  if response[RPC_RESULT] == NAT_STATUS_CONFIRMED:
    # Everything is good to go
    return socket
  
  # Handle no server at the forwarder  
  elif response[RPC_RESULT] == NAT_STATUS_NO_SERVER:
    raise EnvironmentError, "Connection Refused! No server at the forwarder!"
    
  # Handle busy forwarder
  elif response[RPC_RESULT] == NAT_STATUS_BSY_SERVER:
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
def _nat_reg_port_rpc(mux, mac, port):
  rpc_dict = {RPC_REQUEST_ID:1,RPC_FUNCTION:RPC_REGISTER_PORT,RPC_PARAM:{"server":mac,"port":port}}
  return _nat_rpc_call(mux,rpc_dict)

# Does an RPC call to the forwarder to deregister a port
def _nat_dereg_port_rpc(mux, mac, port):
  rpc_dict = {RPC_REQUEST_ID:2,RPC_FUNCTION:RPC_DEREGISTER_PORT,RPC_PARAM:{"server":mac,"port":port}}
  return _nat_rpc_call(mux,rpc_dict)

# Does an RPC call to the forwarder to register a server
def _nat_reg_server_rpc(mux, mac):
  rpc_dict = {RPC_REQUEST_ID:3,RPC_FUNCTION:RPC_REGISTER_SERVER,RPC_PARAM:mac}
  return _nat_rpc_call(mux,rpc_dict)

# Does an RPC call to the forwarder to deregister a server
def _nat_dereg_server_rpc(mux, mac):
  rpc_dict = {RPC_REQUEST_ID:4,RPC_FUNCTION:RPC_DEREGISTER_SERVER,RPC_PARAM:mac}
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
  # Do we already have a mux? If not create a new one
  if NAT_STATE_DATA["mux"] == None:
    
    # Get a forwarder to use
    if forwarderIP == None or forwarderPort == None:
 #     forwarder_lookup() 
      forwarderIP, forwarderPort = forwarder_lookup()
      settimer(0, server_advertise, [localmac],)
 #     forwarderIP = mycontext['currforwarder']
 #     forwarderPort = 12345
      
    # Create a real connection to the forwarder
    socket = openconn(forwarderIP, forwarderPort)
  
    # Immediately create a multiplexer from this connection
    mux = Multiplexer(socket, {"localip":getmyip(), "localport":localport})

    # Add the multiplexer to our state
    NAT_STATE_DATA["mux"] = mux
  else:
    # Get the mux
    mux = NAT_STATE_DATA["mux"]

  # Register us as a server, if necessary
  if not localmac in NAT_LISTEN_PORTS:
    success = _nat_reg_server_rpc(mux, localmac)
    if success:
      # Create a set for the ports
      NAT_LISTEN_PORTS[localmac] = set()
    else:
      # Something is wrong, raise Exception
      raise EnvironmentError, "Failed to begin listening!"
      
  # Setup the waitforconn
  mux.waitforconn(localmac, localport, function)

  # Register our wait port on the forwarder
  success = _nat_reg_port_rpc(mux, localmac, localport)
  if success:
    # Register this port
    NAT_LISTEN_PORTS[localmac].add(localport)
  else:
    # Something is wrong, raise Exception
    raise EnvironmentError, "Failed to begin listening!"
   
  
  # Return the localmac and localport, for stopcomm
  return (localmac,localport)
  
     
    
# Stops the socketReader for the given natcon  
def nat_stopcomm(handle):
  """
  <Purpose>
    Stops listening on a NATConnection, opened by nat_waitforconn
    
  <Arguments>
    handle:
        Handle returned by nat_waitforconn.
  
  """
  # Get the mux
  mux = NAT_STATE_DATA["mux"]
  
  # Unpack the handle
  (localmac, localport) = handle
  
  if mux != None:
    if localmac in NAT_LISTEN_PORTS and localport in NAT_LISTEN_PORTS[localmac]:
      # Tell the Mux to stop listening
      mux.stopcomm(str(handle))
      
      # Cleanup
      NAT_LISTEN_PORTS[localmac].discard(localport)
    
      # De-register our port from the forwarder
      _nat_dereg_port_rpc(mux, localmac, localport)
    
      # Are we listening on any ports?
      numListen = len(NAT_LISTEN_PORTS[localmac])
      if numListen == 0:
        # De-register the server entirely
        _nat_dereg_server_rpc(mux, localmac)
        
        # Cleanup
        del NAT_LISTEN_PORTS[localmac]
      
      # Are we listening as any server?
      if len(NAT_LISTEN_PORTS) == 0:
        # Close the mux, and set it to Null
        mux.close()
        NAT_STATE_DATA["mux"] = None
  


# Determines if you are behind a NAT (Network-Address-Translation)
def behind_nat(forwarderIP=None,forwarderPort=None):
  """
  <Purpose>
    Determines if the currently executing node is behind a Network-Address-Translation device
  
  <Arguments>
    forwarderip:
      Defaults to None. This can be set for explicitly forcing the use of a forwarder
    
    forwarderport:
      Defaults to None. This can be set for explicitly forcing the use of a port on a forwarder.
  
  <Exceptions>
    This may raise various network related Exceptions if not connected to the internet.
  
  <Returns>
    True if behind a nat, False otherwise.
  """
  # Get "normal" ip
  ip = getmyip()
  
  # TODO: Dennis you need to tie in here to get a real forwarder IP and port
  if forwarderIP == None or forwarderPort == None:
    forwarderIP, forwarderPort = server_lookup(localmac)
#    server_lookup(localmac)
#    forwarderIP = mycontext['currforwarder'][0]
 #   forwarderPort = 12345

  # Create a real connection to the forwarder
  rpcsocket = openconn(forwarderIP, forwarderPort)
  
  # Now connect to a forwarder, and get our external ip/port
  # Create a RPC dictionary
  rpc_request = {RPC_FUNCTION:RPC_EXTERNAL_ADDR}
  
  # Send the RPC message
  rpcsocket.send(RPC_encode(rpc_request))
  
  # Get the response
  response = RPC_decode(rpcsocket)
  
  return (ip != response[RPC_RESULT]["ip"])
  
