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
NAT_STATUS_NO_SERVER = "NO_SERVER"
NAT_STATUS_BSY_SERVER = "BSY_SERVER"
NAT_STATUS_CONFIRMED = "CONFIRMED"
NAT_STATUS_LENGTH = 12

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

  response = socket.recv(NAT_STATUS_LENGTH)
  response = response.lstrip(NAT_PAD_CHAR) # Strip the pad character
  
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
  
    # Transmit our MAC address
    localmac = localmac.rjust(NAT_MAC_LENGTH,NAT_PAD_CHAR) # Pad the mac
    socket.send(localmac) # Send it
  
    response = socket.recv(NAT_STATUS_LENGTH)
    response = response.lstrip(NAT_PAD_CHAR) # Strip the pad character
   
    # Check the response 
    if response == NAT_STATUS_CONFIRMED:
      # Immediately create a multiplexer from this connection
       mux = Multiplexer(socket, {"localip":localmac, "localport":localport})

       # Setup the waitforconn
       mux.waitforconn(localmac, localport, function)
  
       # Add the multiplexer to our state
       NAT_STATE_DATA["mux"] = mux
     
       # Register this port
       NAT_LISTEN_PORTS[localport] = True
     
       # Return the localport, for stopcomm
       return localport
    
    # Something is wrong, raise Exception
    else:
      # Close the socket
      socket.close()
    
      raise EnvironmentError, "Failed to begin listening!"
  
  # We already have a mux, so just add a new listener
  else:
    # Get the mux
    mux = NAT_STATE_DATA["mux"]
    
    # Setup the waitforconn
    mux.waitforconn(localmac, localport, function)
     
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
    mux.stopcomm(port)
    del NAT_LISTEN_PORTS[port]
    
    # Are we listening on any ports?
    numListen = len(NAT_LISTEN_PORTS)
    if numListen == 0:
      # Close the mux, and set it to Null
      mux.close()
      NAT_STATE_DATA["mux"] = None
  
