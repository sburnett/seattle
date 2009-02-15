"""

Author: Armon Dadgar

Start Date: January 22nd, 2009

Description:
Provides a method of transferring data to machines behind firewalls or Network Address Translation (NAT).
Abstracts the forwarding specification into a series of classes and functions.

"""

include forwarder_advertise.py
include server_advertise.py

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
    # Strip colons
    clientMac = clientMac.replace(":","")
    serverMac = serverMac.replace(":","")
    
    # Check for input sanity
    if len(clientMac) != 12 or len(serverMac) != 12:
      raise ValueError, "Input MAC addresses must be 12 characters (not including colons)!"
    
    # Strip out any colons
    # Set the client mac in the frame
    self.frameMACAddress = clientMac
    
    # set serverMac as the content, set the content length
    self.frameContent = serverMac
    self.frameContentLength = len(self.frameContent)
    
    # Set the correct frame message type
    self.frameMesgType = INIT_CLIENT
  
  
  def initAsServer(self,serverMac,buf):
    """
    <Purpose>
      Prepares the frame to be used for a server initiation.

    <Arguments>
      serverMAC:
            The MAC address of the server (this machine). This should be a string representation.

      buf:
            The default incoming and outgoing buffer size will be set to this. When they reach 0, they will be expanded by this amount. -1 indicates buffering is disabled.
    <Exceptions>
            Raises an ValueError exception if the MAC(s) are not of proper length.
            
    <Side Effects>
      The frame will be altered.
    """
    # Strip colons
    serverMac = serverMac.replace(":","")
    
    # Check for input sanity
    if len(serverMac) != 12:
      raise ValueError, "Input MAC addresses must be at least 12 characters (not including colons)!"
    if buf <= 0 and buf != -1:
      raise ValueError, "Invalid buffer size! Must be a positive value, or -1!"
      
    # Strip out any colons
    # Set the client mac in the frame
    self.frameMACAddress = serverMac

    # Set the content and length
    self.frameContent = str(buf)
    self.frameContentLength = len(self.frameContent)

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
    # Strip colons
    destinationMAC = destinationMAC.replace(":","")
    
    # Check for input sanity
    if len(destinationMAC) != 12:
      raise ValueError, "Input MAC addresses must be at least 12 characters (not including colons)!"
      
    # Strip any colons in the mac address
    self.frameMACAddress = destinationMAC

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
    # Strip colons
    targetMAC = targetMAC.replace(":","")
    
    # Check for input sanity
    if len(targetMAC) != 12:
      raise ValueError, "Input MAC addresses must be at least 12 characters (not including colons)!"
      
    # Strip any colons in the mac address
    self.frameMACAddress = targetMAC

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
    # Strip colons
    targetMAC = targetMAC.replace(":","")
    
    # Check for input sanity
    if len(targetMAC) != 12:
      raise ValueError, "Input MAC addresses must be at least 12 characters (not including colons)!"
    if bufferSize <= 0:
      raise ValueError, "Invalid buffer size! Must be a positive value!"
          
    # Strip any colons in the mac address
    self.frameMACAddress = targetMAC

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
  # Keeps track of the last error during init client/server
  # After a successful init (client or server) it becomes a list
  # recvTuple appends all non-handled frames (e.g. non- DATA_FORWARD)
  error = None 
  ourMAC = "" # What is our MAC?
  connectionInit = False # Is everything setup?

  # Default incoming and outgoing buffer size expansion value
  # Defaults to 128 kilobytes
  # -1 to disable
  defaultBufSize = 128*1024
  
  # This is the main socket
  socket = None 
  
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
  # This dictionary has 6 indexes, "lock" which is a lock for: "data" which is just a string, "closed" is wheter the socket is closed
  # "nodatalock" is locked when there is no data, this allows the NATConnection to unblock a thread that is waiting for data
  # "incomingAvailable", bytes receivable
  # "outgoingAvailable", bytes sendable
  # "outgoingLock" is locked if the outgoingAvailable is 0
  clientDataBuffer = None
  clientDataLock = None
  
  # Signals that the _socketReader should terminate if true
  stopSocketReader = False
  
  # If socketReader recieves a frame after a stopcom, it will be stored here
  # Recv checks if this is set to None, or returns this instead of reading
  socketReaderUnhandledFrame = None
  
  def __init__(self, mac, forwarderIP, forwarderPort, timeout=10):
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
      
      timeout:
        How long before we timeout connecting to the forwarder.
        
    <Exceptions>
        As from socket.connect, etc.
    """
    # Save our mac address
    self.ourMAC = mac.replace(":","")

    # Input checking
    if len(self.ourMAC) != 12:
      raise ValueError, "Input MAC addresses must be at least 12 characters (not including colons)!"
    
    # Setup the socket
    if self.ourMAC == FORWARDER_MAC:
      listenHandle = waitforconn(forwarderIP, forwarderPort, self._incomingFrame)
      self.connectionInit = True
    else:
      self.socket = openconn(forwarderIP, forwarderPort, timeout=timeout)
      
    # Setup socket locks
    self.readLock = getlock()
    self.writeLock = getlock()
  
  # Closes the NATConnection, and cleans up
  def close(self):
    """
    <Purpose>
      Closes the NATConnection object. Also closes all sockets associated with this connection.
      
    """
    # Prevent more reading or writing
    try:
      self.readLock.release()
    except:
      # See below
      pass
    finally:
      self.readLock.acquire()
    
    try:
      self.writeLock.release()
    except:
      # Exception is thrown if the lock is already unlocked
      pass
    finally:
      self.writeLock.acquire()
    
    self.connectionInit = False
    
    # Stop the internal listner
    if self.listenHandle != None:
      stopcomm(self.listenHandle)
      self.listenHandle = None
      
    # Get the buffer lock, and close everything if it exists
    if self.clientDataLock != None:
      self.stopSocketReader = True # Tell the socket reader to quit
      
      self.clientDataLock.acquire()
    
      # Close each individual socket
      for clt in self.clientDataBuffer:
        self._closeCONN(clt,True)
    
      # Release the buffer lock
      self.clientDataLock.release()
      
    # Close the real socket
    if self.socket != None:
      self.socket.close()
      self.socket = None
      
  # Stops additional listener threads
  def stopcomm(self):
    """
    <Purpose>
      Stops the listener thread from waitforconn.
      
    <Side effects>
      The virtual sockets will no longer get data buffered. Incoming frames will not be parsed.
      
    """
    # Instruct the socket reader to stop      
    self.stopSocketReader = True
    
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
      self.error = []
      return self.socket
      
    # Otherwise, set the error message, and return none
    # Also, close the socket.  
    else:
      self.error = frResp.frameContent
      return None
    
  # Initializes connection to forwarder as a server
  def initServerConnection(self,buf=128*1024):
    """
    <Purpose>
      Initializes TCP socket to multiplex data between server and forwarder

    <Arguments>
      buf:
        The default incoming and outgoing buffer expansion size.
        The buffer will be expanded by this much when it reaches 0.
        Defaults to 128 kilobytes. Set to -1 to disable.
        
    <Exceptions>
      Throws an EnvironmentError if an unexpected response is received.
      
    <Returns>
      True if the connection succedded, False on failure.
      Check NATConnection.error to see the error.
    """
    # Setup the buffer
    self.defaultBufSize = buf
    
    # Make sure we have all the locks
    self.readLock.acquire()
    self.writeLock.acquire()
    
    # Create init frame
    frInit = NATFrame()
    frInit.initAsServer(self.ourMAC,buf)
    
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
      self.error = []
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
    
    # Check if there is an unhandled frame left over
    # If so, return that instead of reading the socket
    if self.socketReaderUnhandledFrame != None:
      frame = self.socketReaderUnhandledFrame
      self.socketReaderUnhandledFrame = None
      # DEBUG
      #print "NATConnection.recv.UnhandledFrame: ", frame
      return frame
            
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
    
    # DEBUG
    #print "NATConnection.recv: ", frame
    
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
    
    # Only return a data frame
    while True:
      # Read in a frame
      frame = self.recv()
      
      # Append the frame to the error array
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
        The function to call. It should take three arguments: (remotemac, socketlikeobj, thisnatcon).
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
    
    # Create dictionary
    self.clientDataBuffer = {}
    
    # Create lock
    self.clientDataLock = getlock()
    
    # Set stopSocketReader to false
    self.stopSocketReader = False
    
    # Launch event to handle this
    settimer(0, self._socketReader, ())
  
  
  # Handles a client closing a connection
  # force is used to avoid checking if client is connected,
  # this is used on NATConnection.close to avoid deadlocking
  def _closeCONN(self,fromMac,force=False):
    # Check if this client is even connected
    if force or self._isConnected(fromMac):    
      # We just need to set the closed flag, since the socket will detect that and close itself
      # Lock the client
      self.clientDataBuffer[fromMac]["lock"].acquire()
    
      # Set it to be closed
      self.clientDataBuffer[fromMac]["closed"] = True
    
      # Release the lock now, even with no data, so that we hit the closed check
      try:
        self.clientDataBuffer[fromMac]["nodatalock"].release() 
      except:
        pass
      
      # Release the lock now, even with no data, so that we hit the closed check
      try:
        self.clientDataBuffer[fromMac]["outgoingLock"].release()
      except:
        pass
        
      # Unlock
      self.clientDataBuffer[fromMac]["lock"].release()

  # Handles a forwarder CONN_BUF_SIZE message
  # Increases the amount we can send out
  def _conn_buf_size(self,fromMac, num):
    # Return if we are not buffering
    if (self.defaultBufSize == -1):
      return
    
    # Only do this if the client is connected...
    if self._isConnected(fromMac):  
      # Lock the client
      self.clientDataBuffer[fromMac]["lock"].acquire()
    
      # Set it to the new amount
      self.clientDataBuffer[fromMac]["outgoingAvailable"] = num
    
      # Release the outgoing lock, this unblocks socket.send
      try:
        self.clientDataBuffer[fromMac]["outgoingLock"].release()
      except:
        # That means the lock was already released, which means we have an unexpected 
        # CONN_BUF_SIZE message...
        pass
    
      # Unlock
      self.clientDataBuffer[fromMac]["lock"].release()
  
  # Handles a new client connecting
  def _new_client(self, fromMac, frame):
    # If there is no user function to handle this, then just return
    if self.frameHandler == None:
      return
      
    # If the client is already connected, then just return
    if self._isConnected(fromMac):
      return
    
    # Get the main dictionary lock
    self.clientDataLock.acquire()
    
    # Create the entry for it, add the data to it
    self.clientDataBuffer[fromMac] = {
    "lock":getlock(), # This is a general lock, so that only one thread is accessing this dict
    "data":"", # This is the real buffer
    "closed":False, # This signals that the virtual socket should be closed on the next recv/send operation (it will clean up, and then throw an exception)
    "nodatalock":getlock(), # This lock is used to block socket.recv when there is no data in the buffer, it greatly improves efficiency
    "incomingAvailable":self.defaultBufSize, # Amount the forwarder can still send us
    "outgoingAvailable":self.defaultBufSize, # Amount we can send the forwarder
    "outgoingLock":getlock()} # This allows us to block socket.send while we wait for a CONN_BUF_SIZE message from the forwarder.
    
    # By default there is no data, so set the lock
    self.clientDataBuffer[fromMac]["nodatalock"].acquire()
    
    # If the frame is a data frame, add the data
    if frame.frameMesgType == DATA_FORWARD:
      self._incoming_client_data(fromMac, frame)
    
    # Create a new socket
    # Disables buffering if self.defaultBufSize is -1
    socketlike = NATSocket(self, fromMac, (self.defaultBufSize != -1))
    
    # Make sure the user code is safe, launch an event for it
    try:
      settimer(0,self.frameHandler, (fromMac, socketlike, self))
    except:      
      # Close the socket
      socketlike.close()
    finally:
      # Release the main dictionary lock
      self.clientDataLock.release()
  
  # Handles incoming data for an existing client
  def _incoming_client_data(self, fromMac, frame):
    # Use the socket lock so that this is thread safe
    self.clientDataBuffer[fromMac]["lock"].acquire()
    
    # Append the new data
    self.clientDataBuffer[fromMac]["data"] += frame.frameContent
    
    # Release the lock now that there is data
    try:
      self.clientDataBuffer[fromMac]["nodatalock"].release() 
    except:
      # This just means that there was still data in the buffer
      pass
    
    self.clientDataBuffer[fromMac]["lock"].release()
  
  # Simple function to determine if a client is connected
  def _isConnected(self,fromMac):
    # Get the main dictionary lock
    self.clientDataLock.acquire()
    status = fromMac in self.clientDataBuffer
    
    # Release the main dictionary lock
    self.clientDataLock.release()     
    return status
     
  # This is launched as an even for waitforconn
  def _socketReader(self):
    # This thread is responsible for reading all incoming frames,
    # so it pushes data into the buffers, initializes new threads for each new client
    # and handles all administrative frames
    while True:
      # Should we quit?
      if self.stopSocketReader or not self.connectionInit:
        break
      
      # Read in a frame
      try:
        frame = self.recv()
        fromMac = frame.frameMACAddress
        frameType = frame.frameMesgType
        #DEBUG
        #print "NATConnection._socketReader: ", frame
      except:
        # This is probably because the socket is now closed, so lets loop around and see
        continue
      
      # It is possible we recieved a stopcomm while doing recv, so lets check again and handle this
      if self.stopSocketReader:
        # Save the frame
        self.socketReaderUnhandledFrame = frame
        break 
      
      # Handle INIT_CLIENT
      if frameType == INIT_CLIENT:
        self._new_client(fromMac, frame)
            
      # Handle CONN_TERM
      elif frameType == CONN_TERM:
        self._closeCONN(fromMac)
      
      # Handle CONN_BUF_SIZE
      elif frameType == CONN_BUF_SIZE:
        self._conn_buf_size(fromMac, int(frame.frameContent))
          
      # Handle DATA_FORWARD
      elif frameType == DATA_FORWARD:
        # Does this client socket exists? If so, append to their buffer
        if self._isConnected(fromMac):
          self._incoming_client_data(fromMac, frame)
        
        # This is a new client, we need to call the user callback function
        else:
          self._new_client(fromMac, frame)
      
      # We don't know what this is, so panic    
      else:
        raise Exception, "Unhandled Frame type: ", frameType

# A socket like object with an understanding that it is part of a NAT Connection
# Has the same functions as the socket like object in repy
class NATSocket():
  # Pointer to the master NAT Connection
  natcon = None
  
  # Connected client mac
  clientMac = ""
  
  # Flags whether buffering limits are enabled
  # This determines whether or not the socket respects incomingAvailable and
  # outgoingAvailable
  BUFFERING = True
  
  def __init__(self, natcon, clientMac,buf=True):
    self.natcon = natcon
    self.clientMac = clientMac
    self.BUFFERING = buf
  
  def close(self):
    """
    <Purpose>
      Closes the socket. This will close the client connection if possible.
      
    <Side effects>
      The socket will no longer be usable. Socket behavior is undefined after calling this method,
      and most likely Runtime Errors will be encountered.
    """
    # If the NATConnection is still initialized, then lets send a close message
    if self.natcon.connectionInit:
      # Create termination frame
      termFrame = NATFrame()
      termFrame.initAsConnTermMsg(self.clientMac)
      
      # Tell the forwarder to terminate the client connection
      self.natcon.sendFrame(termFrame)
    
    # Clean-up
    self.natcon.clientDataLock.acquire() # Get the main lock, since we are modifying the dict
    self.natcon.clientDataBuffer[self.clientMac]["lock"].acquire() # Probably not necessary, but oh well
    self.natcon.clientDataBuffer[self.clientMac]["data"] = "" # Clear the buffer, again probably unnecessary
    del self.natcon.clientDataBuffer[self.clientMac] # Remove the entry 
    self.natcon.clientDataLock.release()

    # Remove connection to natcon, to prevent trying to send or recv again
    self.natcon = None
    
  def recv(self,bytes):
    """
    <Purpose>
      To read data from the socket. This operation will block until some data is available. It will not block if some, non "bytes" amount is available. 
    
    <Arguments>
      bytes:
        Read up to "bytes" input. Positive integer.
    
    <Exceptions>
      If the socket is closed, an EnvironmentError will be raised. If bytes is a non-positive integer, a ValueError will be raised.
        
    <Returns>
      A string with length up to bytes
    """
    # Check input sanity
    if bytes <= 0:
      raise ValueError, "Must read a positive integer number of bytes!"
        
    # Block until there is data
    # This lock is released whenever new data arrives, or if there is data remaining to be read
    self.natcon.clientDataBuffer[self.clientMac]["nodatalock"].acquire()
    try:
      self.natcon.clientDataBuffer[self.clientMac]["nodatalock"].release()
    except:
      # Some weird timing issues can cause an exception, but it is harmless
      pass
    
    # Check if the socket is closed, raise an exception
    if self.natcon.clientDataBuffer[self.clientMac]["closed"]:
      self.close() # Clean-up
      raise EnvironmentError, "The socket has been closed!"
            
    # Get our own lock
    self.natcon.clientDataBuffer[self.clientMac]["lock"].acquire()
  
    # Read up to bytes
    data = self.natcon.clientDataBuffer[self.clientMac]["data"][:bytes] 
  
    # Reduce amount of incoming data available
    self.natcon.clientDataBuffer[self.clientMac]["incomingAvailable"] -= len(data)
    
    # Remove what we read from the buffer
    self.natcon.clientDataBuffer[self.clientMac]["data"] = self.natcon.clientDataBuffer[self.clientMac]["data"][bytes:] 
  
    # Check if there is more incoming buffer available, if not, send a CONN_BUF_SIZE
    # This does not count against the outgoingAvailable quota
    if self.BUFFERING and self.natcon.clientDataBuffer[self.clientMac]["incomingAvailable"] <= 0:
      # Create CONN_BUF_SIZE frame
      buf_frame = NATFrame()
      buf_frame.initAsConnBufSizeMsg(self.clientMac, self.natcon.defaultBufSize)
      
      # Send it to the Forwarder
      self.natcon.sendFrame(buf_frame)
      
      # Increase our incoming buffer
      self.natcon.clientDataBuffer[self.clientMac]["incomingAvailable"] = self.natcon.defaultBufSize
    
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
      If the data input is empty, a ValueError will be raised.
      
    """
    # Input sanity
    if len(data) == 0:
      raise ValueError, "Cannot send a null data-set!"
    
    # Send chunks of data until it is all sent
    while True:
      # Make sure we have available outgoing bandwidth
      self.natcon.clientDataBuffer[self.clientMac]["outgoingLock"].acquire()
      try:
        self.natcon.clientDataBuffer[self.clientMac]["outgoingLock"].release()
      except:
        # Some weird timing issues can cause an exception, but it is harmless
        pass
      
      # Check if the socket is closed, raise an exception
      if self.natcon.clientDataBuffer[self.clientMac]["closed"]:
        self.close() # Clean-up
        raise EnvironmentError, "The socket has been closed!"
        
      # Get our own lock
      self.natcon.clientDataBuffer[self.clientMac]["lock"].acquire()
      
      # How much outgoing traffic is available?
      outgoingAvailable = self.natcon.clientDataBuffer[self.clientMac]["outgoingAvailable"]
      
      # If we can, just send it all at once
      if not self.BUFFERING or len(data) < outgoingAvailable:
        # Instruct the NATConnection object to send our data
        self.natcon.send(self.clientMac, data)
        
        if self.BUFFERING:
          # Reduce the size of outgoing avail
          self.natcon.clientDataBuffer[self.clientMac]["outgoingAvailable"] -= len(data)
        
        # Release the lock
        self.natcon.clientDataBuffer[self.clientMac]["lock"].release()
          
        # We need to explicitly leave the loop
        break
        
      # We need to send chunks, while waiting for more outgoing B/W
      else:
        # Get a chunk of data, and send it
        chunk = data[:outgoingAvailable]
        self.natcon.send(self.clientMac, chunk)
      
        # Reduce the size of outgoing avail
        self.natcon.clientDataBuffer[self.clientMac]["outgoingAvailable"] = 0

        # Lock the outgoing lock, so that we block until the forwarder
        # sends us a CONN_BUF_SIZE message
        self.natcon.clientDataBuffer[self.clientMac]["outgoingLock"].acquire()
      
        # Trim data to only what isn't sent syet
        data = data[outgoingAvailable:]
    
        # Release the lock
        self.natcon.clientDataBuffer[self.clientMac]["lock"].release()
        
        # If there is no data left to send, then break
        if len(data) == 0:
          break



#########################################################################
###  Wrappers around the NAT Objects
###  These should integrate lookup methods

# Wrapper function around the NATLayer for clients        
# TODO: DO SOMETHING SMART WITH localmac
def nat_openconn(destmac, destport, localmac="001122334455", localport=None, timeout = 5, forwarderIP=None,forwarderPort=None):
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

  # Create NATConnection to forwarder
  natcon = NATConnection(localmac, forwarderIP, forwarderPort,timeout)
  # Connect to desired server, get socket
  socket = natcon.initClientConnection(destmac)
  
  # Check if we were successful
  if socket == None:
    raise EnvironmentError, "Failed to connect to server!"
    
  return socket

# Wrapper function around the NATLayer for servers  
def nat_waitforconn(localmac, localport, function, forwarderIP=None, forwarderPort=None):
  """
  <Purpose>
    Allows a server to accept connections from behind a NAT.
    
  <Arguments>
    localmac:
        The unique MAC used to identify this server
        
    localport:
        N/A, used for compatibility
        
    function:
        User function to call when a client connects.
        The function to call. It should take five arguments: 
          (remotemac, remoteport, socketlikeobj, thiscommhandle, listencommhandle)
          If your function has an uncaught exception, 
          the socket-like object it is using will be closed.
        
        * remoteport will be None, since it is N/A
        * thiscommhandle will be None, since it is N/A

    forwarderIP:
      Force a forwarder to connect to. This will be automatically resolved if None.
      forwarderPort must be specified if this is None.
      
    forwarderPort:
      Force a forwarder port to connect to. This will be automatically resolved if None.
      forwarderIP must be specified if this is None.           
  
  <Side Effects>
    An event will be used to monitor new connections
    
  <Returns>
    A NATConnection object, this can be used with nat_stopcomm to stop listening.      
  """
  if forwarderIP == None or forwarderPort == None:
    forwarder_lookup() 
    settimer(0, server_advertise, [localmac],)
    forwarderIP = mycontext['currforwarder']
    forwarderPort = 12345 
  
  # Create NATConnection to forwarder
  natcon = NATConnection(localmac, forwarderIP, forwarderPort)
  natcon.initServerConnection()
  
  # Compatibility wrapper
  # NATCon calls with (remotemac, socketlikeobj, thisnatcon)
  # We call user function with remotemac, None, socketlikeobj, None, thisnatcon
  def waitCompatibility(remotemac, socketlikeobj, thisnatcon):
    function(remotemac, None, socketlikeobj, None, thisnatcon)   
  
  # Setup waitforconn, use compatibility wrapper
  natcon.waitforconn(waitCompatibility)
  
  # Return the natcon, for stopcomm
  return natcon

# Stops the socketReader for the given natcon  
def nat_stopcomm(natcon):
  """
  <Purpose>
    Stops listening on a NATConnection, opened by nat_waitforconn
    
  <Arguments>
    natcon:
        NATConnection object, also returned by nat_waitforconn.
  
  <Remarks>
    If any clients are connected to the server (e.g. sockets remain open), calling this will prevent them
    from receiving new data.
  """
  natcon.stopcomm()
  
