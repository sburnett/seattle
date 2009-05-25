"""

Author: Armon Dadgar

Start Date: January 22nd, 2009

Description:
Provides a method of transferring data to machines behind firewalls or Network Address Translation (NAT).
Abstracts the forwarding specification into a series of classes and functions.

"""

include NAT_advertisement.py
include deserialize.py
include Multiplexer.py
include RPC_Constants.py

# How long we should stall nat_waitforconn after we create the mux to check its status
NAT_MUX_STALL = 2  # In seconds

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

# Wrapper function around the NATLayer for clients        
def nat_openconn(destmac, destport, localip=None, localport=None, timeout = 5, forwarderIP=None,forwarderPort=None):
  """
  <Purpose>
    Opens a connection to a server behind a NAT.
  
  <Arguments>
    destmac:
      The MAC address of the destination server
    
    destport:
      The port on the host to connect to.
    
    localip:
      See openconn.
    
    localport:
      See openconn.
    
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
  # If we don't get an ip/port explicitly, then locate the server
  if forwarderIP == None or forwarderPort == None:
   forwarderIP, forwarderPort = nat_server_lookup(destmac)

  # Create a real connection to the forwarder
  socket = openconn(forwarderIP, forwarderPort, localip, localport, timeout)

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
  

# Simple wrapper function to determine if we are still waiting
# e.g. if the multiplexer is still alive
def nat_waitforconn_alive():
  """
  <Purpose>
    Informs the caller of the current state of the NAT waitforconn.
    
  <Returns>
    True if the connection to the forwarder is established and alive, False otherwise.    
  """
  return NAT_STATE_DATA["mux"] != None and NAT_STATE_DATA["mux"].isAlive()
  

# Wrapper function around the NATLayer for servers  
def nat_waitforconn(localmac, localport, function, forwarderIP=None, forwarderPort=None, forwarderCltPort=None, errdel=None):
  """
  <Purpose>
    Allows a server to accept connections from behind a NAT.
    
  <Arguments>
    See wait for conn.

    forwarderIP:
      Force a forwarder to connect to. This will be automatically resolved if None.
      All forwarder information must be specified if this is set.
      
    forwarderPort:
      Force a forwarder port to connect to. This will be automatically resolved if None.
      All forwarder information must be specified if this is set.           
  
    forwarderCltPort:
      The port for clients to connect to on the explicitly specified forwarder.
      All forwarder information must be specified if this is set.
      
    errdel:
      Sets the Error Delegate for the underlying multiplexer. See Multiplexer.setErrorDelegate.
      Argument should be a function pointer, the function should take 3 parameters, (mux, location, exception)
      
  <Side Effects>
    An event will be used to monitor new connections
    
  <Returns>
    A handle, this can be used with nat_stopcomm to stop listening.      
  """  
  # Check if our current mux is dead (if it exists)
  if NAT_STATE_DATA["mux"] != None and not NAT_STATE_DATA["mux"].isAlive():
    # Delete the mux
    NAT_STATE_DATA["mux"] = None
  
  # Do we already have a mux? If not create a new one
  if NAT_STATE_DATA["mux"] == None:
    
    # Get a forwarder to use
    if forwarderIP == None or forwarderPort == None or forwarderCltPort == None:
      forwarderIP, forwarderPort, forwarderCltPort = nat_forwarder_lookup()
    
    # Save this information
    NAT_STATE_DATA["forwarderIP"] = forwarderIP
    NAT_STATE_DATA["forwarderPort"] = forwarderPort
    NAT_STATE_DATA["forwarderCltPort"] = forwarderCltPort

    try:  
      # Create a real connection to the forwarder
      socket = openconn(forwarderIP, forwarderPort)
    except:
      raise EnvironmentError, "Failed to connect to forwarder. Please try again."
  
    # Immediately create a multiplexer from this connection
    mux = Multiplexer(socket, {"localip":getmyip(), "localport":localport})

    # Stall for a while then check the status of the mux
    sleep(NAT_MUX_STALL)
    
    # If the mux is no longer initialized, or never could initialize, then raise an exception
    if not mux.isAlive():
      raise EnvironmentError, "Failed to begin listening!"
    
    # Add the multiplexer to our state
    NAT_STATE_DATA["mux"] = mux
  else:
    # Get the mux
    mux = NAT_STATE_DATA["mux"]

  # If the error delegate is assigned, set up error delegation
  if errdel != None:
    mux.setErrorDelegate(errdel)
        
  # Register us as a server, if necessary
  if not localmac in NAT_LISTEN_PORTS:
    success = _nat_reg_server_rpc(mux, localmac)
    if success:
      # Create a set for the ports
      NAT_LISTEN_PORTS[localmac] = set()
      
      # Setup an advertisement
      nat_server_advertise(localmac, NAT_STATE_DATA["forwarderIP"], NAT_STATE_DATA["forwarderCltPort"])
      nat_toggle_advertisement(True)
    
    else:
      # Something is wrong, raise Exception
      raise EnvironmentError, "Failed to begin listening!"
      
  # Setup the waitforconn
  mux.waitforconn(localmac, localport, function)

  # Register our wait port on the forwarder, if necessary
  if not localport in NAT_LISTEN_PORTS[localmac]:
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
  
  # Check the status of the mux, is it alive?
  if mux != None and not mux.isAlive():
    # Delete the mux, and stop listening on everything
    NAT_STATE_DATA["mux"] = None
    NAT_LISTEN_PORTS.clear()
    mux = None
  
  # Unpack the handle
  (localmac, localport) = handle
  
  if mux != None and localmac in NAT_LISTEN_PORTS and localport in NAT_LISTEN_PORTS[localmac]:
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
      
      # Stop advertising
      nat_stop_server_advertise(localmac)
      
      # Cleanup
      del NAT_LISTEN_PORTS[localmac]
    
    # Are we listening as any server?
    if len(NAT_LISTEN_PORTS) == 0:
      # Close the mux, and set it to Null
      mux.close()
      NAT_STATE_DATA["mux"] = None
      
      # Disable advertisement
      nat_toggle_advertisement(False, False)
  

# Pings a forwarder to get our external IP
def getmy_external_ip(forwarderIP=None,forwarderCltPort=None):
  """
  <Purpose>
    Allows a vessel to determine its external IP address. E.g. this will differ from getmyip if you are on a NAT.
  
  <Arguments>
    forwarderIP/forwarderPort:
      If None, a forwarder will be automatically selected. They can also be explicitly specified.
      forwarderPort must be a client port.
  
  <Side Effects>
    This operation will use a socket while it is running.
  
  <Returns>
    A string IP address
  """
  # If we don't have an explicit forwarder, pick a random one
  if forwarderIP == None or forwarderCltPort == None:
    forwarderIP, forwarderPort, forwarderCltPort = nat_forwarder_lookup()

  # Create a real connection to the forwarder
  try:
    rpcsocket = openconn(forwarderIP, forwarderCltPort)
  except:
    raise EnvironmentError, "Failed to connect to forwarder. Please try again."
  
  # Now connect to a forwarder, and get our external ip/port
  # Create a RPC dictionary
  rpc_request = {RPC_FUNCTION:RPC_EXTERNAL_ADDR}
  
  # Send the RPC message
  rpcsocket.send(RPC_encode(rpc_request))
  
  # Get the response
  response = RPC_decode(rpcsocket)
  
  # Close the socket
  rpcsocket.close()
  
  # Return the IP
  return response[RPC_RESULT]["ip"]


# Determines if you are behind a NAT (Network-Address-Translation)
def behind_nat(forwarderIP=None,forwarderCltPort=None):
  """
  <Purpose>
    Determines if the currently executing node is behind a Network-Address-Translation device
  
  <Arguments>
    forwarderip:
      Defaults to None. This can be set for explicitly forcing the use of a forwarder
    
    forwarderport:
      Defaults to None. This can be set for explicitly forcing the use of a port on a forwarder.
      This must be the client port, not the server port.
  
  <Exceptions>
    This may raise various network related Exceptions if not connected to the internet.
  
  <Returns>
    True if behind a nat, False otherwise.
  """
  # Get "normal" ip
  ip = getmyip()
  
  # Get external ip
  externalip = getmy_external_ip(forwarderIP, forwarderCltPort)
  
  return (ip != externalip)
  
