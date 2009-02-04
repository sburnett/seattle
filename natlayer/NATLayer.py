"""

Author: Armon Dadgar

Start Date: January 22nd, 2009

Description:
Provides a method of transferring data to machines behind firewalls or Network Address Translation (NAT).
Abstracts the forwarding specification into a series of classes and functions.

"""

# Define Module Constants
FORWARDER_MAC = "FFFFFFFFFFFF"
FRAME_DIVIDER = ";" # What character is used to divide a frame header
CONTENT_LENGTH_DIGITS = 10 # Force content length string to this size, pad with 0's

# What is the fixed size of the header?
# This is the content length string, 3 dividers, a 12 digit MAC, and a 1 digit message type
HEADER_SIZE = CONTENT_LENGTH_DIGITS + 3*len(FRAME_DIVIDER) + 13

# These are the valid Message Types
DATA_FORWARD = 0
CONN_TERM = 1
CONN_BUF_SIZE = 2
INIT_SERVER = 3
INIT_CLIENT = 4
INIT_STATUS = 5

# Special Case
FRAME_NOT_INIT = -1

# Valid Forwarder responses to init
STATUS_NO_SERVER = "NO_SERVER"
STATUS_BSY_SERVER = "BSY_SERVER"
STATUS_CONFIRMED = "CONFIRMED"

# Core unit of the Specification, this is used for multiplexing a single connection,
# and for initializing connection to the forwarder
class NATFrame():
  frameMesgType = FRAME_NOT_INIT
  frameContentLength = 0
  frameMACAddress = ""
  frameContent = ""

  # So that we display properly  
  def __repr__(self):
    try:
      return self.toString()
    except AttributeError:
      return "<NATFrame instance, FRAME_NOT_INIT>"
    
  def initAsClient(self,clientMac, serverMac):
    """
    <Purpose>
      Prepares the frame to be used for a client initiation.

    <Arguments>
      clientMAC:
             The MAC address of the client (this machine). This should be a string representation.
      serverMAC:
            The MAC address of the remote client (the server). This should be a string representation.

    <Exceptions>
            Raises an ValueError exception if the MAC(s) are not of proper length.
            
    <Side Effects>
      The frame will be altered.
    """
    # Check for input sanity
    if len(clientMac) < 12 or len(serverMac) < 12:
      raise ValueError, "Input MAC addresses must be at least 12 characters!"
    
    # Strip out any colons
    # Set the client mac in the frame
    self.frameMACAddress = clientMac.replace(":","")
    
    # set serverMac as the content, set the content length
    self.frameContent = serverMac.replace(":","")
    self.frameContentLength = len(self.frameContent)
    
    # Set the correct frame message type
    self.frameMesgType = INIT_CLIENT
  
  
  def initAsServer(self,serverMac):
    """
    <Purpose>
      Prepares the frame to be used for a server initiation.

    <Arguments>
      serverMAC:
            The MAC address of the server (this machine). This should be a string representation.

    <Exceptions>
            Raises an ValueError exception if the MAC(s) are not of proper length.
            
    <Side Effects>
      The frame will be altered.
    """
    # Check for input sanity
    if len(serverMac) < 12:
      raise ValueError, "Input MAC addresses must be at least 12 characters!"
      
    # Strip out any colons
    # Set the client mac in the frame
    self.frameMACAddress = serverMac.replace(":","")

    # Set the content length
    self.frameContent = ""
    self.frameContentLength = 0

    # Set the correct frame message type
    self.frameMesgType = INIT_SERVER
    
  def initAsForwarderResponse(self,response):
    """
    <Purpose>
      Prepares the frame to be used for a forwarder response to initiation.

    <Arguments>
      response:
            The forwarder response message.
          
    <Side Effects>
      The frame will be altered.
    """
    # Set the forwarder mac in the frame
    self.frameMACAddress = FORWARDER_MAC

    # Set the frame content
    self.frameContent = response
    
    # Set the content length
    self.frameContentLength = len(self.frameContent)

    # Set the correct frame message type
    self.frameMesgType = INIT_STATUS 

  def initAsDataFrame(self,destinationMAC, content):
    """
    <Purpose>
      Prepares the frame to be used for a data transfer.

    <Arguments>
      destinationMAC:
            The MAC address that this frame should be routed to. Alternatively, if this is being sent to a server, the MAC should reflect that of the sender.
      content:
            The content that should be sent to the destination. Must be a string, or
            can be converted to one by the str() command.

    <Exceptions>
            Raises an ValueError exception if the MAC(s) are not of proper length.
          
    <Side Effects>
      The frame will be altered.
    """
    # Check for input sanity
    if len(destinationMAC) < 12:
      raise ValueError, "Input MAC addresses must be at least 12 characters!"
      
    # Strip any colons in the mac address
    self.frameMACAddress = destinationMAC.replace(":","")

    # Set the frame content
    self.frameContent = str(content)

    # Set the content length
    self.frameContentLength = len(self.frameContent)

    # Set the correct frame message type
    self.frameMesgType = DATA_FORWARD
  
  def initAsConnTermMsg(self,targetMAC):
    """
    <Purpose>
      Prepares the frame to be used to terminate a connection to a client.

    <Arguments>
      targetMAC:
            The MAC address of the client that should be disconnected.

    <Exceptions>
            Raises an ValueError exception if the MAC(s) are not of proper length.
                  
    <Side Effects>
      The frame will be altered.
    """
    # Check for input sanity
    if len(targetMAC) < 12:
      raise ValueError, "Input MAC addresses must be at least 12 characters!"
      
    # Strip any colons in the mac address
    self.frameMACAddress = targetMAC.replace(":","")

    # Set the frame content
    self.frameContent = ""

    # Set the content length
    self.frameContentLength = 0

    # Set the correct frame message type
    self.frameMesgType = CONN_TERM
    
  def initAsConnBufSizeMsg(self,targetMAC, bufferSize):
    """
    <Purpose>
      Prepares the frame to be used to adjust a clients TCP buffer size.

    <Arguments>
      targetMAC:
            The MAC address of the client that should be altered.
            
      bufferSize:
            The new buffer size for the client.
    
    <Exceptions>
            Raises an ValueError exception if the MAC(s) are not of proper length.
       
    <Side Effects>
      The frame will be altered.
    """
    # Check for input sanity
    if len(targetMAC) < 12:
      raise ValueError, "Input MAC addresses must be at least 12 characters!"
      
    # Strip any colons in the mac address
    self.frameMACAddress = targetMAC.replace(":","")

    # Set the frame content, convert the bufferSize into a string
    self.frameContent = str(bufferSize)

    # Set the content length
    self.frameContentLength = len(self.frameContent)

    # Set the correct frame message type
    self.frameMesgType = CONN_BUF_SIZE
  
  def initFromSocket(self, inSocket):
    """
    <Purpose>
      Constructs a frame object given a socket which contains only frames.

    <Arguments>
      inSocket:
            The socket to read from.

    <Side Effects>
      The frame will be altered.
    
    <Exceptions>
      An EnvironmentError will be raised if an unexpected header is received. This could happen if the socket is closed.
    """    
    # Read in the header
    header = inSocket.recv(HEADER_SIZE)
    
    if len(header) == HEADER_SIZE:
      # Setup header
      self._parseStringHeader(header)

      if self.frameContentLength != 0:
        # Read in the data
        self.frameContent = inSocket.recv(self.frameContentLength)

    else:
      raise EnvironmentError, "Unexpected Header Size!"
  
  def initFromFile(self, fHandle):
    """
    <Purpose>
      Constructs a frame object given a file handle which contains only frames.

    <Arguments>
      fHandle:
            The file handle to read from.

    <Side Effects>
      The frame will be altered.
      
    <Returns>
      True if successful and the frame has been updated. False if the frame has not been updated.
    """
    # Read in the header
    header = fHandle.read(HEADER_SIZE)
    
    if len(header) == HEADER_SIZE:
      # Setup header
      self._parseStringHeader(header)
    
      if self.frameContentLength != 0:
        # Read in the data
        self.frameContent = fHandle.read(self.frameContentLength)
      
      return True
    else:
      return False
  
  # Takes a string representing the header, and initializes the frame  
  def _parseStringHeader(self, header):
    # Check to make sure the header is the right size
    if len(header) != HEADER_SIZE:
      raise ValueError, "Cannot parse header of wrong size!"
    
    # Explode based on the divider
    headerFields = header.split(FRAME_DIVIDER,2)
    (msgtype, contentlength, mac) = headerFields
    
    # Convert the types
    msgtype = int(msgtype)
    contentlength = int(contentlength)
    
    # Strip the last semicolon off
    mac = mac.rstrip(FRAME_DIVIDER)
    
    # Setup the Frame
    self.frameMesgType = msgtype
    self.frameContentLength = contentlength
    self.frameMACAddress = mac
    
  def toString(self):
    """
    <Purpose>
      Converts the frame to a string.

    <Exceptions>
      Raises an AttributeError exception if the frame is not yet initialized,
       e.g. its Message type is FRAME_NOT_INIT.
      
    <Returns>
      A string based representation of the string.
    """
    if self.frameMesgType == FRAME_NOT_INIT:
      raise AttributeError, "NAT Frame is not yet initialized!"
    
    return str(self.frameMesgType) + FRAME_DIVIDER + \
      str(self.frameContentLength).rjust(CONTENT_LENGTH_DIGITS,"0") + FRAME_DIVIDER + \
      self.frameMACAddress + FRAME_DIVIDER + \
      self.frameContent

# This helps abstract the details of a NAT connection    
class NATConnection():
  error = None # Keeps track of the last error
  ourMAC = "" # What is our MAC?
  connectionInit = False # Is everything setup?
  socket = None # This is the main socket
  
  # This is a handle to the connection listener
  # If this is not None, then we are a forwarder
  listenHandle = None 
  
  # Callback function that is passed a socket object and frame when it is received
  # This needs to be set by the forwarder, this is also used by waitforconn
  frameHandler = None
  
  # Locks, this is to make sure only one thread is reading or writing at any time
  readLock = None
  writeLock = None
  
  # This is so that client data can be buffered for the sockets
  # This is used for waitforconn, to handle recieving data out of requested order
  # e.g. socket A does a recv but we recieve 5 frames for socket B first
  # 
  # Each client is represented by their string mac, which corresponds to another dictionary
  # This dictionary has 4 indexes, "lock" which is a lock for: "data" which is just a string, "closed" is wheter the socket is closed
  # "nodatalock" is locked when there is no data, this allows the NATConnection to unblock a thread that is waiting for data
  clientDataBuffer = {}
  clientDataLock = None
  
  def __init__(self, mac, forwarderIP, forwarderPort):
    """
    <Purpose>
      Initializes the NATConnection object.
     
    <Arguments>
      mac:
        MAC address of this machine. If this is detected as the FORWARDER_MAC
        then the socket will be established to listen, and the given port will
        be used.
        
      forwarderIP:
        The IP address of the forwarder to connect to. If this is the forwarder,
        then use getmyip().
      
      forwarderPort:
        The port on the forwarder to connect to
   
    <Exceptions>
        As from socket.connect, etc.
    """
    # Save our mac address
    self.ourMAC = mac.replace(":","")

    # Setup the socket
    if self.ourMAC == FORWARDER_MAC:
      listenHandle = waitforconn(forwarderIP, forwarderPort, self._incomingFrame)
      self.connectionInit = True
    else:
      self.socket = openconn(forwarderIP, forwarderPort)
      
    # Setup socket locks
    self.readLock = getlock()
    self.writeLock = getlock()
  
  # Closes the NATConnection, and cleans up
  def close(self):
    """
    <Purpose>
      Closes the NATConnection object.
     
    """
    # Prevent more reading or writing
    self.readLock.acquire()
    self.writeLock.acquire()
    
    self.connectionInit = False
    
    # Close the real socket
    if self.socket != None:
      self.socket.close()
      self.socket = None
    
    # Stop the internal listner
    if self.listenHandle != None:
      stopcomm(self.listenHandle)
      self.listenHandle = None
      
    # Get the buffer lock  
    self.clientDataLock.acquire()
    
    # Close each individual socket
    for clt in self.clientDataBuffer:
      self._closeCONN(clt)
    
    # Release the buffer lock
    self.clientDataLock.release()
      
  # Handles incoming frames
  def _incomingFrame(self,remoteip,remoteport,inSocket,thisCommHandle,listenCommHandle):
    # Initialize Frame
    frame = NATFrame()
    
    # Create frame from the socket
    frame.initFromSocket(inSocket)
    
    # Call the callback function
    if self.frameHandler != None:
      self.frameHandler(inSocket, frame)
  
  # Initializes connection to forwarder and a server,
  # Returns a socket that can be used normally
  def initClientConnection(self, serverMac):
    """
    <Purpose>
      Initializes TCP socket to serve as a client connection to a server
    
    <Arguments>
      serverMAC:
        The MAC address of the server to connect to.
    
    <Exceptions>
      Throws an EnvironmentError if an unexpected response is received.
      
    <Returns>
      A socket object if the connection succedded, None on failure.
      Check NATConnection.error to see the error.
    """
    # Make sure we have all the locks
    self.readLock.acquire()
    self.writeLock.acquire()
    
    # Create init frame
    frInit = NATFrame()
    frInit.initAsClient(self.ourMAC, serverMac)
    
    # Send the frame
    self.socket.send(frInit.toString())
    
    # Get the response frame
    frResp = NATFrame()
    frResp.initFromSocket(self.socket)

    # Release the locks
    self.readLock.release()
    self.writeLock.release()
    
    # Check the response
    if frResp.frameMesgType != INIT_STATUS:
      raise EnvironmentError, "Unexpected Response Frame!"
    
    # Return the socket if everything is ready
    if frResp.frameContent == STATUS_CONFIRMED:
      self.connectionInit = True
      return self.socket
      
    # Otherwise, set the error message, and return none
    # Also, close the socket.  
    else:
      self.error = frResp.frameContent
      return None
    
  # Initializes connection to forwarder as a server
  def initServerConnection(self):
    """
    <Purpose>
      Initializes TCP socket to multiplex data between server and forwarder

    <Exceptions>
      Throws an EnvironmentError if an unexpected response is received.
      
    <Returns>
      True if the connection succedded, False on failure.
      Check NATConnection.error to see the error.
    """
    # Make sure we have all the locks
    self.readLock.acquire()
    self.writeLock.acquire()
    
    # Create init frame
    frInit = NATFrame()
    frInit.initAsServer(self.ourMAC)
    
    # Send the frame
    self.socket.send(frInit.toString())
    
    # Get the response frame
    frResp = NATFrame()
    frResp.initFromSocket(self.socket)

    # Release the locks
    self.readLock.release()
    self.writeLock.release()
    
    # Check the response
    if frResp.frameMesgType != INIT_STATUS:
      raise EnvironmentError, "Unexpected Response Frame!"
    
    # Return the socket if everything is ready
    if frResp.frameContent == STATUS_CONFIRMED:
      self.connectionInit = True
      return True
      
    # Otherwise, set the error message, and return none
    # Also, close the socket.  
    else:
      self.error = frResp.frameContent
      return False
     
  def recv(self):
    """
    <Purpose>
      Receives a frame and returns it. If you want a socket-like interface, with 
      more abstraction, see waitforconn.
    
    <Exceptions>
      If the socket is closed, an EnvironmentError is raised.
      If the connection is not initialized, an AttributeError is raised.
    
    <Remarks>
      This function will return all types of incoming frames.
      
    <Returns>
      A frame object. None on failure.
    """
    # Check if we are initialized
    if not self.connectionInit:
      raise AttributeError, "NAT Connection is not yet initialized!"
            
    # Init frame
    frame = NATFrame()
    
    try:
      # Get the read lock
      self.readLock.acquire()
      
      # Construct frame, this blocks
      frame.initFromSocket(self.socket)
    finally:
      # Release the lock
      self.readLock.release()
    
    # Return the frame
    return frame
    
  def recvTuple(self):
    """
    <Purpose>
      Receives a frame and returns it as a tuple.

    <Exceptions>
      If the socket is closed, an EnvironmentError is raised.
      If the connection is not initialized, an AttributeError is raised.

    <Remarks>
      This function will only return when it receives a valid DATA_FORWARD frame.
      All other frame types will be added to the NATConnection.error array.
      
    <Returns>
      A tuple, (fromMac, content)
    """
    # Check if we are initialized
    if not self.connectionInit:
      raise AttributeError, "NAT Connection is not yet initialized!"

    # Set the error field to an array, append all non-data forward frames
    self.error = [] 
    
    # Only return a data frame
    while True:
      # Read in a frame
      frame = self.recv()
      
      if frame.frameMesgType != DATA_FORWARD:
        self.error.append(frame)
      else:
        break

    # Return the frame
    return (frame.frameMACAddress, frame.frameContent)
  
  def sendFrame(self,frame):
    """
    <Purpose>
      Sends a frame over the socket.
      
    <Arguments>
      frame:
        The frame to send over the network
    
    <Exceptions>
      If the connection is not initialized, an AttributeError is raised.  Socket error can be raised if the socket is closed during transmission.
    """
    # Check if we are initialized
    if not self.connectionInit:
      raise AttributeError, "NAT Connection is not yet initialized!"
    
    try:
      # Get the send lock
      self.writeLock.acquire()
        
      # Send the frame!
      self.socket.send(frame.toString())
    finally:
      # release the send lock
      self.writeLock.release()
    
  def send(self,targetMac, data):
    """
    <Purpose>
      Sends data as a frame over the socket.
      
    <Arguments>
      targetMac:
        The target to send the data to.
       
      data:
        The data to send to the target.
        
    <Exceptions>
      If the connection is not initialized, an AttributeError is raised. Socket error can be raised if the socket is closed during transmission.
    """
    # Check if we are initialized
    if not self.connectionInit:
      raise AttributeError, "NAT Connection is not yet initialized!"
      
    # Build the frame
    frame = NATFrame()
    
    # Initialize it
    frame.initAsDataFrame(targetMac, data)
    
    # Send it!
    self.sendFrame(frame)

  def waitforconn(self, function):
    """
    <Purpose>
    Waits for a connection to a port. Calls function with a socket-like object if it succeeds.

    <Arguments>
      function:
        The function to call. It should take five arguments: (remotemac, socketlikeobj, thisnatcon).
        If your function has an uncaught exception, the socket-like object it is using will be closed.

    <Side Effects>
      Starts an event handler that listens for connections.

    <Returns>
      Nothing
    """
    # Check if we are initialized
    if not self.connectionInit:
      raise AttributeError, "NAT Connection is not yet initialized!"
      
    # Setup the user function to call if there is a new client
    self.frameHandler = function
    
    # Create lock
    self.clientDataLock = getlock()
    
    # Launch event to handle this
    settimer(0, self._socketReader, ())
  
  
  # Handles a client closing a connection
  def _closeCONN(fromMac):
    # Lock the client
    self.clientDataBuffer[fromMac]["lock"].acquire()
    
    # Set it to be closed
    self.clientDataBuffer[fromMac]["closed"] = True
    
    # Unlock
    self.clientDataBuffer[fromMac]["lock"].release()
      
  # This is launched as an even for waitforconn
  def _socketReader(self):
    while True:
      # Read in a frame
      frame = self.recv()
      fromMac = frame.frameMACAddress
      
      # Handle CONN_TERM
      if frame.frameMesgType == CONN_TERM:
        self._closeCONN(fromMac)
        return
        
      # We only want to handle data forwarding requests
      # TODO: fix this
      if frame.frameMesgType != DATA_FORWARD:
        print "unhandled frame type: ", frame.frameMesgType
        return
      
      # Get the lock
      self.clientDataLock.acquire()
      
      # Does this client socket exists? If so, append to their buffer
      if fromMac in self.clientDataBuffer:
        # Use the socket lock so that this is thread safe
        self.clientDataBuffer[fromMac]["lock"].acquire()
        self.clientDataBuffer[fromMac]["data"] += frame.frameContent
        self.clientDataBuffer[fromMac]["nodatalock"].release() # There is now data
        self.clientDataBuffer[fromMac]["lock"].release()
        
      # This is a new client, we need to call the user callback function
      else:
        # Create a new socket
        socketlike = NATSocket(self, fromMac)
        
        # Create the entry for it, add the data to it
        self.clientDataBuffer[fromMac] = {"lock":getlock(),"data":"","closed":False, "nodatalock":getlock()}
        self.clientDataBuffer[fromMac]["data"] = frame.frameContent
        
        # Make sure the user code is safe, launch an event for it
        try:
          settimer(0,self.frameHandler, (fromMac, socketlike, self))
        except:
          # Close the socket
          socketlike.close()
        
      self.clientDataLock.release()
       
       
# A socket like object with an understanding that it is part of a NAT Connection
# Has the same functions as the socket like object in repy
class NATSocket():
  # Pointer to the master NAT Connection
  natcon = None
  
  # Connected client mac
  clientMac = ""
  
  def __init__(self, natcon, clientMac):
    self.natcon = natcon
    self.clientMac = clientMac
  
  def close(self):
    """
    <Purpose>
      Closes the socket. This will close the client connection if possible.
      
    <Side effects>
      The socket will no longer be usable.
    """
    # If the NATConnection is still initialized, then lets send a close message
    if self.natcon.connectionInit:
      # Tell the forwarder to terminate the client connection
      self.natcon.sendFrame(NATFrame().initAsConnTermMsg(self.clientMac))
    
    # Clean-up
    self.natcon.clientDataLock.acquire() # Get the main lock
    self.natcon.clientDataBuffer[self.clientMac]["lock"].acquire() # Probably not necessary, but oh well
    self.natcon.clientDataBuffer[self.clientMac]["data"] = "" # Clear the buffer
    del self.natcon.clientDataBuffer[self.clientMac] # Remove the entry 
    self.natcon.clientDataLock.release()

    # Remove connection to natcon
    self.natcon = None
    
  def recv(self,bytes):
    """
    <Purpose>
      To read data from the socket. This operation will block until some data is available. It will not block if some, non "bytes" amount is available. 
    
    <Arguments>
      bytes:
        Read up to "bytes" input
    
    <Exceptions>
      If the socket is closed, an EnvironmentError will be raised.
        
    <Returns>
      A string with length up to bytes
    """
    # Check if the socket is closed, raise an exception
    if self.natcon.clientDataBuffer[self.clientMac]["closed"]:
      self.close() # Clean-up
      raise EnvironmentError, "The socket has been closed!"
        
    # Block until there is data
    # This lock is released whenever new data arrives, or if there is data remaining to be read
    self.natcon.clientDataBuffer[self.clientMac]["nodatalock"].acquire()
    self.natcon.clientDataBuffer[self.clientMac]["nodatalock"].release()
    
    # Get our own lock
    self.natcon.clientDataBuffer[self.clientMac]["lock"].acquire()
  
    # Read up to bytes
    data = self.natcon.clientDataBuffer[self.clientMac]["data"][:bytes] 
  
    # Strip bytes from the string
    self.natcon.clientDataBuffer[self.clientMac]["data"] = self.natcon.clientDataBuffer[self.clientMac]["data"][bytes:] 
  
    # Set the no data lock if there is none
    if len(self.natcon.clientDataBuffer[self.clientMac]["data"]) == 0:
      self.natcon.clientDataBuffer[self.clientMac]["nodatalock"].acquire()
      
    # Release the lock
    self.natcon.clientDataBuffer[self.clientMac]["lock"].release() 
    
    return data

  def send(self,data):
    """
    <Purpose>
      To send data over the socket. This operation will block. 
    
    <Arguments>
      data:
        Send string data over the socket.
    
    <Exceptions>
      If the socket is closed, an EnvironmentError will be raised.
        
    """
    # Check if the socket is closed, raise an exception
    if self.natcon.clientDataBuffer[self.clientMac]["closed"]:
      self.close() # Clean-up
      raise EnvironmentError, "The socket has been closed!"
    
    # Instruct the NATConnection object to send our data
    # to the client specified for this socket
    
    self.natcon.send(self.clientMac, data)
    