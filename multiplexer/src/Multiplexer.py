"""

Author: Armon Dadgar

Start Date: February 16th, 2009

Description:
Provides a means of multiplexing any stream-like connection into a multiple
socket-like connections.

"""

# This is to help send dictionaries as strings
include deserialize.py

# Define Module Constants
# 
# How many digits can be used to indicate header length
MULTIPLEXER_FRAME_HEADER_DIGITS = 3 
MULTIPLEXER_FRAME_DIVIDER = ";" # What character is used to divide a frame header

# These are the valid Message Types
MULTIPLEXER_DATA_FORWARD = 0
MULTIPLEXER_CONN_TERM = 1
MULTIPLEXER_CONN_BUF_SIZE = 2
MULTIPLEXER_INIT_CLIENT = 3
MULTIPLEXER_INIT_STATUS = 4

# Special Case
MULTIPLEXER_FRAME_NOT_INIT = -1

# Valid Multiplexer responses to init
MULTIPLEXER_STATUS_CONFIRMED = "CONFIRMED"
MULTIPLEXER_STATUS_FAILED = "FAILED"

# Core unit of the Specification, this is used for multiplexing a single connection,
# and for initializing connections
class MultiplexerFrame():
  
  # Set the frame instance variables
  def __init__(self):
    self.headerSize = 0
    self.mesgType = MULTIPLEXER_FRAME_NOT_INIT
    self.contentLength = 0
    self.referenceID = 0
    self.content = ""
    
  # So that we display properly  
  def __repr__(self):
    try:
      return self.toString()
    except AttributeError:
      return "<MultiplexerFrame instance, MULTIPLEXER_FRAME_NOT_INIT>"
    
  def initClientFrame(self,requestedID, remotehost, remoteport, localip, localport):
    """
    <Purpose>
      Makes the frame a MULTIPLEXER_INIT_CLIENT frame

    <Arguments>
      requestedID:
        The requested Identifier for this new virtual socket
      
      ip:
       Our IP address reported to the partner multiplexer
       
      port:
        Our port reported to the partner multiplexer
      
      
    """    
    # Set the requestedID in the frame
    self.referenceID = requestedID
    
    # Set the content as a dict
    requestDict = {'localip':remotehost,'localport':remoteport,'remoteip':localip,'remoteport':localport}
    self.content = str(requestDict)
    self.contentLength = len(self.content)
    
    # Set the correct frame message type
    self.mesgType = MULTIPLEXER_INIT_CLIENT

    
  def initResponseFrame(self,requestedID,response):
    """
    <Purpose>
      Makes the frame a MULTIPLEXER_INIT_STATUS frame

    <Arguments>
      requestedID:
          A reference to the requestedID of the MULTIPLEXER_INIT_CLIENT message
      
      response:
          The response message.
          
    """
    # Set the requestedID in the frame
    self.referenceID = requestedID

    # Set the frame content
    self.content = response
    
    # Set the content length
    self.contentLength = len(self.content)

    # Set the correct frame message type
    self.mesgType = MULTIPLEXER_INIT_STATUS 

  def initDataFrame(self,referenceID, content):
    """
    <Purpose>
      Makes the frame a MULTIPLEXER_DATA_FORWARD frame

    <Arguments>
      referenceID:
            The referenceID that this frame should be routed to.
      content:
            The content that should be sent to the destination.

    """
    # Strip any colons in the mac address
    self.referenceID = referenceID

    # Set the frame content
    self.content = str(content)

    # Set the content length
    self.contentLength = len(self.content)

    # Set the correct frame message type
    self.mesgType = MULTIPLEXER_DATA_FORWARD
  
  
  def initConnTermFrame(self,referenceID):
    """
    <Purpose>
      Makes the frame a MULTIPLEXER_CONN_TERM frame

    <Arguments>
      referenceID:
            The referenceID of the socket that should be disconnected.
       
    """
    # Strip any colons in the mac address
    self.referenceID = referenceID

    # Set the frame content
    self.content = ""

    # Set the content length
    self.contentLength = 0

    # Set the correct frame message type
    self.mesgType = MULTIPLEXER_CONN_TERM
  
  
    
  def initConnBufSizeFrame(self,referenceID, bufferSize):
    """
    <Purpose>
      Makes the frame a MULTIPLEXER_CONN_BUF_SIZE frame

    <Arguments>
      referenceID:
            The referenceID of the scoket that should be altered.
            
      bufferSize:
            The new buffer size for the client.
    
    """
    # Strip any colons in the mac address
    self.referenceID = referenceID

    # Set the frame content, convert the bufferSize into a string
    self.content = str(bufferSize)

    # Set the content length
    self.contentLength = len(self.content)

    # Set the correct frame message type
    self.mesgType = MULTIPLEXER_CONN_BUF_SIZE
  
  
  
  def initFromSocket(self, inSocket):
    """
    <Purpose>
      Constructs a frame object given a socket which contains only frames.

    <Arguments>
      inSocket:
            The socket to read from.
    
    <Exceptions>
      An EnvironmentError will be raised if an unexpected header is received. This could happen if the socket is closed.
    """    
    # Read in the header frame size
    headerSize = inSocket.recv(MULTIPLEXER_FRAME_HEADER_DIGITS+len(MULTIPLEXER_FRAME_DIVIDER))
    headerSize = headerSize.rstrip(MULTIPLEXER_FRAME_DIVIDER)
    headerSize = int(headerSize)-1
    header = inSocket.recv(headerSize)
    
    if len(header) == headerSize:
      # Setup header
      self._parseStringHeader(header)

      if self.contentLength != 0:
        # Read in the data
        self.content = inSocket.recv(self.contentLength)

    else:
      raise EnvironmentError, "Unexpected Header Size!"
  
  
  
  # Takes a string representing the header, and initializes the frame  
  def _parseStringHeader(self, header):
    # Explode based on the divider
    headerFields = header.split(MULTIPLEXER_FRAME_DIVIDER,2)
    (msgtype, contentlength, ref) = headerFields
    
    # Convert the types
    msgtype = int(msgtype)
    contentlength = int(contentlength)
    
    # Strip the last semicolon off
    ref = int(ref.rstrip(MULTIPLEXER_FRAME_DIVIDER))
    
    # Setup the Frame
    self.mesgType = msgtype
    self.contentLength = contentlength
    self.referenceID = ref
    
    
    
  def toString(self):
    """
    <Purpose>
      Converts the frame to a string.

    <Exceptions>
      Raises an AttributeError exception if the frame is not yet initialized.
      
    <Returns>
      A string based representation of the string.
    """
    if self.mesgType == MULTIPLEXER_FRAME_NOT_INIT:
      raise AttributeError, "Frame is not yet initialized!"
    
    # Create header
    frameHeader = MULTIPLEXER_FRAME_DIVIDER + str(self.mesgType) + MULTIPLEXER_FRAME_DIVIDER + str(self.contentLength) + \
                  MULTIPLEXER_FRAME_DIVIDER + str(self.referenceID) + MULTIPLEXER_FRAME_DIVIDER
    
    # Determine variable header size
    headerSize = str(len(frameHeader)).rjust(MULTIPLEXER_FRAME_HEADER_DIGITS,"0")
    
    if len(headerSize) > MULTIPLEXER_FRAME_HEADER_DIGITS:
      raise AttributeError, "Frame Header too large! Max:"+ MULTIPLEXER_FRAME_HEADER_DIGITS+ " Actual:"+ len(headerSize)
    
    return  headerSize + frameHeader + self.content
    


# This helps abstract the details of a Multiplexed connection    
class Multiplexer():
  
  def __init__(self, socket, info={}):
    """
    <Purpose>
      Initializes the Multiplexer object.
     
    <Arguments>
      socket:
        Socket like object that is used for multiplexing
    """    
    # If we are given a socket, assume it is setup
    if socket != None:
      # Is everything setup?
      self.connectionInit = True 

      # Default incoming and outgoing buffer size expansion value
      # Defaults to 128 kilobytes
      self.defaultBufSize = 128*1024

      # This is the main socket
      self.socket = socket 

      # This dictionary contains information about this socket
      # This just has some junk default values, and is filled in during init
      self.socketInfo = {"localip":"127.0.0.1","localport":0,"remoteip":"127.0.0.1","remoteport":0}

      # Locks, this is to make sure only one thread is reading or writing at any time
      self.readLock = getlock()
      self.writeLock = getlock()

      # Callback function that is passed a socket object
      # Maps a port to a function
      self.callbackFunction = {}

      # This dictionary keeps track of sockets we are waiting to open, e.g. openconn has been called
      # but the partner multiplexer has not responded yet
      self.pendingSockets = {}

      # If we want a new client, what number should we request?
      self.nextReferenceID = 0

      # A dictionary that associates reference ID's to their MultiplexerSocket objects
      self.virtualSockets = {}
      self.virtualSocketsLock = getlock()

      # Signals that the _socketReader should terminate if true
      self.stopSocketReader = False      
      
      # Inject or override socket info given to use
      for key, value in info.items():
        self.socketInfo[key] = value
        
      # Launch event to handle the multiplexing
      # Wait 2 seconds so that the user has a change to set waitforconn
      settimer(2, self._socketReader, ())
      
    else:
      raise ValueError, "Must pass in a valid socket!"
  
  # So that we display properly  
  def __repr__(self):
    # Format a nice string with some of our info
    return "<Multiplexer setup:"+str(self.connectionInit)+ \
    " buf_size:"+str(self.defaultBufSize)+ \
    " counter:"+str(self.nextReferenceID)+ \
    " info:"+str(self.socketInfo)+">"
          
  # Closes the Multiplexer, and cleans up
  def close(self, closeSocket=True):
    """
    <Purpose>
      Closes the Multiplexer object. Also closes all virtual sockets associated with this connection.
      
    <Arguments>
      closeSocket:
        If true, the master socket will be closed as well.
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
    
    # The Mux is no longer initialized
    self.connectionInit = False
    
    # Get the buffer lock, and close everything if it exists
    self.stopSocketReader = True # Tell the socket reader to quit
     
    # Close each individual socket
    for refID, sock in self.virtualSockets.items():
      self._closeCONN(sock, refID) 
    
    # Close the real socket
    if closeSocket and self.socket != None:
      self.socket.close()
      self.socket = None

      
  # Stops additional listener threads
  def stopcomm(self,port):
    """
    <Purpose>
      Stops the listener thread from waitforconn.
      
    <Side effects>
      The virtual sockets will no longer get data buffered. Incoming frames will not be parsed.
      
    """
    # Deletes the callback function on the specified port
    if port in self.callbackFunction:
      del self.callbackFunction[port]
    
  # Private: Recieves a single frame 
  def _recvFrame(self):
    # Check if we are initialized
    if not self.connectionInit:
      raise AttributeError, "Multiplexer is not yet initialized!"
            
    # Init frame
    frame = MultiplexerFrame()
    
    try:
      # Get the read lock
      self.readLock.acquire()
      
      # Construct frame, this blocks
      frame.initFromSocket(self.socket)
   
    except Exception, exp:
      # We need to close the multiplexer
      self.close()
      
      # Re-raise the exception
      raise exp

    # Release the lock
    self.readLock.release()
    
    # Return the frame
    return frame

  # Private: Sends a single frame
  def _sendFrame(self,frame):
    # Check if we are initialized
    if not self.connectionInit:
      raise AttributeError, "Multiplexer is not yet initialized!"
    
    try:
      # Get the send lock
      self.writeLock.acquire()

      # Send the frame!
      self.socket.send(frame.toString())
    
    except Exception, exp:
      # We need to close the multiplexer
      self.close()
      
      # Re-raise the exception
      raise exp
        
    # release the send lock
    self.writeLock.release()
   
  def _send(self,referenceID, data):
    """
    <Purpose>
      Sends data as a frame over the socket.
      
    <Arguments>
      referenceID:
        The target to send the data to.
       
      data:
        The data to send to the target.
        
    <Exceptions>
      If the connection is not initialized, an AttributeError is raised. Socket error can be raised if the socket is closed during transmission.
    """
    # Check if we are initialized
    if not self.connectionInit:
      raise AttributeError, "Multiplexer is not yet initialized!"
      
    # Build the frame
    frame = MultiplexerFrame()
    
    # Initialize it
    frame.initDataFrame(referenceID, data)
    
    # Send it!
    self._sendFrame(frame)

  def openconn(self, desthost, destport, localip=None,localport=None,timeout=15):
    """
    <Purpose>
      Opens a connection, returning a socket-like object

    <Arguments>
      See repy's openconn

    <Side Effects>
      None

    <Returns>
      A socket like object.
    """    
    # Check if we are initialized
    if not self.connectionInit:
      raise AttributeError, "Multiplexer is not yet initialized!"
    
    # Check for default values
    if localip == None:
      localip = self.socketInfo["localip"]
      
    if localport == None:
      localport = self.socketInfo["localport"]
    
    # Create an MULTIPLEXER_INIT_CLIENT frame
    frame = MultiplexerFrame()
    
    # Get a new id
    requestedID = self.nextReferenceID
    
    # Increment the counter
    self.nextReferenceID = self.nextReferenceID + 1
    
    # Setup the frame
    frame.initClientFrame(requestedID, desthost, destport, localip, localport)
    
    # Send the request
    self._sendFrame(frame)
    
    # Add this request to the pending sockets, add a bool to hold if this was successful, and a lock that we use for blocking
    # The third element is a timer handle, that is used for the timeout
    self.pendingSockets[requestedID] = [False, getlock(), None]
    
    # Now we block until the request is handled, or until we reach the timeout
    
    # Set a timer to unblock us after a timeout
    self.pendingSockets[requestedID][2] = settimer(timeout, self._openconn_timeout, [requestedID])
    
    # Acquire the lock twice, and wait for it to be release
    self.pendingSockets[requestedID][1].acquire()
    self.pendingSockets[requestedID][1].acquire()
    
    # Were we successful?
    success = self.pendingSockets[requestedID][0]
    
    # Get the timer handle
    handle = self.pendingSockets[requestedID][2]
    
    # Remove the request
    del self.pendingSockets[requestedID]
    
    # At this point we've been unblocked, so were we successful?
    if success:
      # Create info dictionary
      info  = {"localip":localip,"localport":localport,"remoteip":desthost,"remoteport":destport}
      
      # Return a virtual socket
      socket = MultiplexerSocket(requestedID, self, self.defaultBufSize, info)
      
      # By default there is no data, so set the lock
      socket.socketLocks["nodata"].acquire()
      
      # Lock the virtual sockets dictionary
      self.virtualSocketsLock.acquire()
      
      # Create the entry for it, add the data to it
      self.virtualSockets[requestedID] = socket
      
      # Release the dictionary lock
      self.virtualSocketsLock.release()
      
      return socket
      
    # We failed or timed out  
    else:
      if handle == None:
        # Our partner responded, but not with MULTIPLEXER_STATUS_CONFIRMED
        raise EnvironmentError, "Connection Refused!"
      else:
        # Our connection timed out
        raise EnvironmentError, "Connection timed out!"
      
  
  # Unblocks openconn after a timeout
  def _openconn_timeout(self, refID):
    # Release the socket, so that openconn can continue execution
    try:
      self.pendingSockets[refID][1].release()
    except:
      # This is just to be safe
      pass
    
  def waitforconn(self, localip, localport, function):
    """
    <Purpose>
      Waits for a connection to a port. Calls function with a socket-like object if it succeeds.

    <Arguments>
      localip:
        The local IP to listen on

      localport:
        The local port to bind to
    
      function:
        The function to call. It should take four arguments: (remoteip, remoteport, socketlikeobj, None, multiplexer)
        If your function has an uncaught exception, the socket-like object it is using will be closed.

    <Side Effects>
      Starts an event handler that listens for connections.

    <Returns>
      Nothing
    """
    # Check if we are initialized
    if not self.connectionInit:
      raise AttributeError, "Multiplexer is not yet initialized!"
      
    # Setup the user function to call if there is a new client
    self.callbackFunction[localport] = function

  
  
  # Handles a client closing a connection
  def _closeCONN(self,socket, refID):    
    # Close the socket
    socket.socketInfo["closed"] = True
    
    # Release the client sockets nodata and sending locks, so that they immediately see the message
    # Wrap in try/catch since release will fail on a non-acquired lock
    try:
      socket.socketLocks["nodata"].release()
    except:
      pass
    
    try:
      socket.socketLocks["outgoing"].release()
    except:
      pass
    
    

  # Handles a MULTIPLEXER_CONN_BUF_SIZE message
  # Increases the amount we can send out
  def _conn_buf_size(self,socket, num):
    # Acquire a lock for the socket
    socket.socketLocks["main"].acquire()
    
    # Increase the buffer size
    socket.bufferInfo["outgoing"] = num
    
    # Release the outgoing lock, this unblocks socket.send
    try:
      socket.socketLocks["outgoing"].release()
    except:
      # That means the lock was already released
      pass
    
    # Release the socket
    socket.socketLocks["main"].release()
    
  # Handles a new client connecting
  def _new_client(self, frame, refID):
    # Do an internal error check
    if self._virtualSock(refID) != None:
      raise Exception, "Attempting to connect with a used reference ID!"
    
    # Get the request info
    id = frame.referenceID    # Get the ID from the frame
    info = deserialize(frame.content)   # Get the socket info from
    
    # What port are they trying to connect to?
    requestedPort = info["localport"]
      
    # Check for a callback function
    if requestedPort in self.callbackFunction:
      userfunc = self.callbackFunction[requestedPort]
    
    # Send a failure message and return
    else:
      # Respond to our parter, send a failure message
      resp = MultiplexerFrame()
      resp.initResponseFrame(id,MULTIPLEXER_STATUS_FAILED)
      self._sendFrame(resp)
      return
    
    # Get the main dictionary lock
    self.virtualSocketsLock.acquire()
    
    # Create the socket
    socket = MultiplexerSocket(id, self, self.defaultBufSize, info)
    
    # We need to increase our reference counter now, so as to prevent duplicates
    self.nextReferenceID = id + 1
    
    # Respond to our parter, send a success message
    resp = MultiplexerFrame()
    resp.initResponseFrame(id,MULTIPLEXER_STATUS_CONFIRMED)
    self._sendFrame(resp)
    
    # Create the entry for it, add the data to it
    self.virtualSockets[refID] = socket
    
    # By default there is no data, so set the lock
    socket.socketLocks["nodata"].acquire()
    
    # If the frame is a data frame, add the data
    if frame.mesgType == MULTIPLEXER_DATA_FORWARD:
      self._incoming_client_data(frame, socket)
    
    # Release the main dictionary lock
    self.virtualSocketsLock.release()
    
    # Make sure the user code is safe, launch an event for it
    try:
      settimer(0, userfunc, (info["remoteip"], info["remoteport"], socket, None, self))
    except:      
      # Close the socket
      socket.close()
      
  
  # Handles incoming data for an existing client
  def _incoming_client_data(self, frame, socket):
    # Acquire a lock for the socket
    socket.socketLocks["main"].acquire()
    
    # Increase the buffer size
    socket.buffer += frame.content
    
    # Release the outgoing lock, this unblocks socket.send
    try:
      socket.socketLocks["nodata"].release()
    except:
      # That means the lock was already released
      pass
    
    # Release the socket
    socket.socketLocks["main"].release()
    
  
  # Handles MULTIPLEXER_INIT_STATUS messages for a pending client
  def _pending_client(self, frame, refID):
    # Return if the referenced client is not in the pending list
    if not (refID in self.pendingSockets):
      return
    
    # Cancel the timeout timer
    canceltimer(self.pendingSockets[refID][2])
    
    # Set the handle to None
    self.pendingSockets[refID][2] = None
      
    # Has our partner confirmed the connection? If so, then update the pending socket
    if frame.content == MULTIPLEXER_STATUS_CONFIRMED:
      self.pendingSockets[refID][0] = True
    
    # Unblock openconn
    try:
      self.pendingSockets[refID][1].release()
    except:
      pass
  
  # Simple function to determine if a client is connected,
  # and if so returns their virtual socket
  def _virtualSock(self,refID):
    # Get the main dictionary lock
    self.virtualSocketsLock.acquire()
    
    if refID in self.virtualSockets:
      sock = self.virtualSockets[refID]
    else:
      sock = None
    
    # Release the main dictionary lock
    self.virtualSocketsLock.release()
       
    return sock
     
  # This is launched as an event to handle multiplexing the connection
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
        frame = self._recvFrame()
        refID = frame.referenceID
        frameType = frame.mesgType
      except:
        # This is probably because the socket is now closed, so lets loop around and see
        continue
      
      # It is possible we recieved a stopcomm while doing recv, so lets check again and handle this
      if self.stopSocketReader:
        break 
      
      # Get the virtual socket if it exists
      socket = self._virtualSock(refID)
      
      # Handle MULTIPLEXER_INIT_CLIENT
      if frameType == MULTIPLEXER_INIT_CLIENT:
        self._new_client(frame, refID)
      
      # Handle MULTIPLEXER_INIT_STATUS
      elif frameType == MULTIPLEXER_INIT_STATUS:
        self._pending_client(frame, refID)
        
      # Handle MULTIPLEXER_CONN_TERM
      elif frameType == MULTIPLEXER_CONN_TERM:
        # If the socket is none, that means this client is already terminated
        if socket != None: 
          self._closeCONN(socket, refID)
      
      # Handle MULTIPLEXER_CONN_BUF_SIZE
      elif socket != None and frameType == MULTIPLEXER_CONN_BUF_SIZE:
        self. _conn_buf_size(socket, int(frame.content))
          
      # Handle MULTIPLEXER_DATA_FORWARD
      elif frameType == MULTIPLEXER_DATA_FORWARD:
        # Does this client socket exists? If so, append to their buffer
        # This is a new client, we need to call the user callback function
        if socket == None:
          self._new_client(frame, refID)
        else:
          self._incoming_client_data(frame,socket)
      
      # We don't know what this is, so panic    
      else:
        raise Exception, "Unhandled Frame type: "+ str(frame)

# A socket like object with an understanding that it is part of a Multiplexer
# Has the same functions as the socket like object in repy
class MultiplexerSocket():  
  
  def __init__(self, id, mux, buf, info):
    # Initialize
    
    # Reference ID
    self.id = id
    
    # Pointer to the master Multiplexer
    self.mux = mux
    
    # Socket information
    self.socketInfo = {"closed":False,"localip":"","localport":0,"remoteip":"","remoteport":0}
    
    # Actual buffer of unread data
    self.buffer = ""
    
    # Buffering Information
    self.bufferInfo = {"incoming":buf,"outgoing":buf}

    # Various locks used in the socket
    self.socketLocks = {"main":getlock(),"nodata":getlock(),"outgoing":getlock()}
    
    # Inject or override socket info given to use
    for key, value in info.items():
      self.socketInfo[key] = value
  
  def close(self):
    """
    <Purpose>
      Closes the socket. This will close the client connection if possible.
      
    <Side effects>
      The socket will no longer be usable. Socket behavior is undefined after calling this method,
      and most likely Runtime Errors will be encountered.
    """
    # If the Multiplexer is still initialized, then lets send a close message
    if self.mux != None and self.mux.connectionInit:
      # Create termination frame
      termFrame = MultiplexerFrame()
      termFrame.initConnTermFrame(self.id)
      
      # Tell our partner to terminate the client connection
      self.mux._sendFrame(termFrame)
    
    # Remove from the list of virtual sockets
    if self.mux != None:
      self.mux.virtualSocketsLock.acquire()
      del self.mux.virtualSockets[self.id]
      self.mux.virtualSocketsLock.release()
    
    # Clean-up
    self.mux = None
    self.socketInfo = None
    self.buffer = None
    self.bufferInfo = None
    self.socketLocks = None
  
  # Checks if the socket is closed, and handles it
  def _handleClosed(self):
    # Check if the socket is closed, raise an exception
    if self.socketInfo["closed"]:
      self.close() # Clean-up
      raise EnvironmentError, "The socket has been closed!"
    
  def recv(self,bytes,blocking=False):
    """
    <Purpose>
      To read data from the socket. This operation will block until some data is available. It will not block if some, non "bytes" amount is available. 
    
    <Arguments>
      bytes:
        Read up to "bytes" input. Positive integer.
    
      blocking
        Should the operation block until all "bytes" worth of data are read.
        
    <Exceptions>
      If the socket is closed, an EnvironmentError will be raised. If bytes is a non-positive integer, a ValueError will be raised.
        
    <Returns>
      A string with length up to bytes
    """
    # Check input sanity
    if bytes <= 0:
      raise ValueError, "Must read a positive integer number of bytes!"
        
    # Check if the socket is closed
    self._handleClosed()
        
    # Block until there is data
    # This lock is released whenever new data arrives, or if there is data remaining to be read
    self.socketLocks["nodata"].acquire()
    try:
      self.socketLocks["nodata"].release()
    except:
      # Some weird timing issues can cause an exception, but it is harmless
      pass
    
    # Check if the socket is closed
    self._handleClosed()
            
    # Get our own lock
    self.socketLocks["main"].acquire()
  
    # Read up to bytes
    data = self.buffer[:bytes] 
    amountIn = len(data)
    
    # Remove what we read from the buffer
    self.buffer = self.buffer[bytes:] 
  
    # Reduce amount of incoming data available
    self.bufferInfo["incoming"] -= amountIn
  
    # Check if there is more incoming buffer available, if not, send a MULTIPLEXER_CONN_BUF_SIZE
    # This does not count against the outgoingAvailable quota
    if self.bufferInfo["incoming"] <= 0:
      # Create MULTIPLEXER_CONN_BUF_SIZE frame
      buf_frame = MultiplexerFrame()
      buf_frame.initConnBufSizeFrame(self.id, self.mux.defaultBufSize)
      
      # Send it
      self.mux._sendFrame(buf_frame)
      
      # Increase our incoming buffer
      self.bufferInfo["incoming"] = self.mux.defaultBufSize
    
    # Set the no data lock if there is none
    if len(self.buffer) == 0:
      self.socketLocks["nodata"].acquire()
      
    # Release the lock
    self.socketLocks["main"].release() 
    
    # Are we supposed to block?
    if blocking and amountIn < bytes:
      # How much more do we need?
      more = bytes - amountIn
      
      # Try to recieve the extra, recursively call ourself
      moreData = self.recv(more, True)
      
      # Return the original data, plus the extra
      return (data + moreData)
    # Otherwise, just return what we have
    else:
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
      # Check if the socket is closed
      self._handleClosed()
        
      # Make sure we have available outgoing bandwidth
      self.socketLocks["outgoing"].acquire()
      try:
        self.socketLocks["outgoing"].release()
      except:
        # Some weird timing issues can cause an exception, but it is harmless
        pass
      
      # Check if the socket is closed
      self._handleClosed()
        
      # Get our own lock
      self.socketLocks["main"].acquire()
      
      # How much outgoing traffic is available?
      outgoingAvailable = self.bufferInfo["outgoing"]
      
      # If we can, just send it all at once
      if len(data) < outgoingAvailable:
        # Instruct the multiplexer object to send our data
        self.mux._send(self.id, data)
        
        # Reduce the size of outgoing avail
        self.bufferInfo["outgoing"] -= len(data)
        
        # Release the lock
        self.socketLocks["main"].release()
          
        # We need to explicitly leave the loop
        break
        
      # We need to send chunks, while waiting for more outgoing B/W
      else:
        # Get a chunk of data, and send it
        chunk = data[:outgoingAvailable]
        self.mux._send(self.id, chunk)
      
        # Reduce the size of outgoing avail
        self.bufferInfo["outgoing"] = 0

        # Lock the outgoing lock, so that we block until we get a MULTIPLEXER_CONN_BUF_SIZE message
        self.socketLocks["outgoing"].acquire()
      
        # Trim data to only what isn't sent syet
        data = data[outgoingAvailable:]
    
        # Release the lock
        self.socketLocks["main"].release()
        
        # If there is no data left to send, then break
        if len(data) == 0:
          break


# Functional Wrappers for the Multiplexer objects

# This dictionary object links IP's to their respective multiplexer
MULTIPLEXER_OBJECTS = {}

# This dictionary has data about the various multiplexers, and our state
MULTIPLEXER_STATE_DATA = {}

# Setup key entries
# Setup function pointers to be used by the multiplexer wrappers
MULTIPLEXER_STATE_DATA["waitforconn"] = waitforconn
MULTIPLEXER_STATE_DATA["openconn"] = openconn
MULTIPLEXER_STATE_DATA["stopcomm"] = stopcomm

# This dictionary has all of the listener functions to propagate waitforconn to new muxes
# E.g. if a new client connects, it inherits all of the waitforconns on the existing muxes
MULTIPLEXER_WAIT_FUNCTIONS = {}

# Openconn that uses Multiplexers
def mux_openconn(desthost, destport, localip=None,localport=None,timeout=15,virtualport=None):
  """
  <Purpose>
    Opens a multiplexed connection to a remote host, and returns a virtual socket.
  
  <Arguments>
    desthost
      The IP address of the host to connect to.
    
    destport
      The port of the remote host to connect to.
      
    localip
      The localip to use when connecting to the remote host
    
    localport
      The localport to use when connecting to the remote host
    
    timeout
      How long before timing out the connection
  
    virtualport
      Specify a virtual port to connect to, defaults to the destport
      
  <Exceptions>
    See openconn.
  
  <Side effects>
    If this is the first connect to the remote host, an additional event will be used to establish the multiplexing
  
  <Returns>
    A socket-like object that supports close, send, and recv
  
  <Remarks>
    If there is no multiplexed connection pre-established, an attempt will be made to establish a new connection.
    If a connection is already established, then only a virtual socket will be opened.
  """
  # Use the destport by default for the virtualport
  if virtualport == None:
    virtualport = destport
    
  # Check if we already have a real multiplexer
  key = "IP:"+desthost+":"+str(destport)
  if key in MULTIPLEXER_OBJECTS:
    # Since a connection already exists, do a virtual openconn
    return mux_virtual_openconn(desthost, destport, virtualport, localip,localport,timeout)

    # We need to establish a new multiplexer with this host
  else:
    # Get the correct function
    openconn_func = MULTIPLEXER_STATE_DATA["openconn"]

    # Try to get a real socket
    if localport != None and localip != None:
      realsocket = openconn_func(desthost, destport, localip,localport,timeout)
    else:
      realsocket = openconn_func(desthost, destport,timeout=timeout)
      
    # Setup the info for this new mux, give the mux its key
    info = {"remoteip":desthost,"remoteport":destport,"key":key}

    # Get an IP if necessary
    if localip == None:
      try:
        # Otherwise, use getmyip
        info["localip"] = getmyip()
        
        # On failure, use a local loopback ip
      except:
        info["localip"] = "127.0.0.1"

    # If we already have a user given localip, use that
    else:
      info["localip"] = localip

    # Did the use give us a real port?	
    if localport != None:
      info["localport"] = localport

    # Make a mux with this new socket
    mux = Multiplexer(realsocket, info)

    # Add the key entry for this mux
    MULTIPLEXER_OBJECTS[key] = mux

    # Map the old waitforconn's
    _helper_map_existing_waits(mux)
    
    # Now call openconn on the mux to get a virtual socket
    return mux.openconn(desthost, virtualport, localip,localport,timeout)

# Helper function for mux_waitforconn, handles everything then calls user function
def _helper_mux_waitforconn(ip, port, func, remoteip, remoteport, socket, thiscommhandle, listencommhandle):
  # Create key for this new mux
  key = "IP:"+remoteip+":"+str(remoteport)
	
  # Generate connection info
  info = {"remoteip":remoteip,"remoteport":remoteport,"localip":ip,"localport":port,"key":key}
  
  # Create a mux
  mux = Multiplexer(socket, info)
  
  # Add the key entry for this mux
  MULTIPLEXER_OBJECTS[key] = mux
  
  # Map the old waitforconn's
  _helper_map_existing_waits(mux)
    
  # Trigger user function
  mux.waitforconn(ip,port,func)

# Helper function to map pre-existing waitforconn's to a new multiplexer
def _helper_map_existing_waits(mux):
  # Apply the old waitforconns
  for (key, function) in MULTIPLEXER_WAIT_FUNCTIONS.items():
    args = key.split(":")
    mux.waitforconn(args[0],int(args[1]),function)

# Wait for connection to establish new multiplexers and new virtual connections
def mux_waitforconn(localip, localport, function):
  """
  <Purpose>
    Sets up an event handler for an incoming connection. The connection will be multiplexed.
    
  <Arguments>
    localip
      The IP address to listen on
    
    localport
      The port to listen on
    
    function
      The user function to call when a new connection is established. This function should take the following parameters:
        remoteip   : The IP address of the remote host
        remoteport : The port of the remote host for this connection
        socket     : A socket like object that supports close,send,recv
        thiscommhandle   : Nothing, this should not be used
        listencommhandle : A reference to the parent multiplexer
  
  <Exceptions>
    See waitforconn.
  
  <Returns>
    A handle that can be used with mux_stopcomm to stop listening on this port for new connections.
  """
  # Get the key
  key = "LISTEN:"+localip+":"+str(localport) 
  
  # Does this key already exist?
  if key in MULTIPLEXER_STATE_DATA:
    # Stop the last waitforconn, then make a new one
    mux_stopcomm(key)
    
  # Get the correct function
  waitforconn_func = MULTIPLEXER_STATE_DATA["waitforconn"]
  
  # This adds ip and port and function information to help with multiplex waitforconns
  def _add_ip_port_func(remoteip, remoteport, socket, thiscommhandle, listencommhandle):
    _helper_mux_waitforconn(localip, localport, function, remoteip, remoteport, socket, thiscommhandle, listencommhandle)
  
  # Call waitforconn, and trigger our helper
  handle = waitforconn_func(localip, localport, _add_ip_port_func)
  
  # Register the handle
  MULTIPLEXER_STATE_DATA[key] = handle
  
  # Do a virtual waitforconn as well as the real one
  mux_virtual_waitforconn(localip, localport, function)

  # Return the key
  return key


# Stops waiting for new connections
def mux_stopcomm(key):
  """
  <Purpose>
    Stops waiting for new clients
  
  <Arguments>
    key:
      Key returned by mux_waitforconn
  
  <Side effects>
    New connections will no longer trigger the user function.
  
  <Returns>
    None
  """
  # Is this a real handle?
  if key in MULTIPLEXER_STATE_DATA:
    # Retrieve the handle
    handle = MULTIPLEXER_STATE_DATA[key]
    
    # Call stopcomm on it
    stopcomm_func = MULTIPLEXER_STATE_DATA["stopcomm"]
    
    # Stopcomm
    stopcomm_func(handle)

    # Get the values by spliting on colon
    arr = key.split(":")
    ip = arr[1]
    port = arr[2]

    # Propogate this stopcomm virtually
    mux_virtual_stopcomm(ip+":"+port)


# Changes the underlying hooks that the mux wrappers use
def mux_remap(wait, open, stop):
  """
  <Purpose>
    Remaps the underlying calls used by mux_openconn, mux_waitforconn, and mux_stopcomm
    
  <Arguments>
    wait:
      The underlying waitforconn function to use
    
    open:
      The underlying openconn function to use
    
    stop:
      The underlying stopcomm function to use
    
  <Returns>
    None
  """
  MULTIPLEXER_STATE_DATA["waitforconn"] = wait
  MULTIPLEXER_STATE_DATA["openconn"] = open
  MULTIPLEXER_STATE_DATA["stopcomm"] = stop


# This function will only do a virtual opeconn, and will not attempt to establish a new connection
def mux_virtual_openconn(desthost, destport, virtualport, localip=None,localport=None,timeout=15):
  """
  <Purpose>
    Opens a new virtual socket on an existing multiplexed connection.
  
  <Arguments>
    desthost
      The IP address of the host machine, to which there is an existing connection
    
    destport
      The real port of the remote host with the multiplexed connection
    
    virtualport
      The virtualport to connect to on the remote host
    
    localip
      The localip to report to the remote host
    
    localport
      The localport to report to the remote host
    
    timeout
      How long before timing out the connection
  
  <Exceptions>
    Raises a ValueError if there is no pre-existing connection to the requested host
  
  <Returns>
    A socket-like object. See mux_openconn.
  """
  # Get the key to the existing multiplexer
  key = "IP:"+desthost+":"+str(destport)
  
  if key in MULTIPLEXER_OBJECTS:
    # Since a multiplexer already exists, lets just use that objects builtin method
    mux = MULTIPLEXER_OBJECTS[key]

    return mux.openconn(desthost, virtualport, localip,localport,timeout)
  else:
    raise ValueError, "There is no pre-existing connection to the requested host!"
    

# This function will only affect multiplexers, and does not listen on real ports
def mux_virtual_waitforconn(localip, localport, function):
  """
  <Purpose>
    Similar to mux_waitforconn, however it only waits on virtual ports and not on real ports.
  
  <Arguments>
    localip
      The localip to listen on. This will be ignored, and the port will be mapped to all multiplexers.
    
    localport
      What port the multiplexers should respond on
    
    function
      What function should be triggered by connections on localport
  
  <Side effects>
    All multiplexers will begin waiting on the local port
  
  <Returns>
    A handle that can be used with mux_virtual_stopcomm
  """
  # Generate a key
  key = localip+":"+str(localport)
  
  # Register the ip/port function for new multiplexers
  MULTIPLEXER_WAIT_FUNCTIONS[key] = function
  
  # Map this waitforconn to all existing multiplexers
  for (key, mux) in MULTIPLEXER_OBJECTS.items():
    mux.waitforconn(localip, localport, function)
  
  return key
  

# This function will only affect multiplexers, and does not listen on real ports
def mux_virtual_stopcomm(key):
  """
  <Purpose>
    Instructs all multiplexers to stop responding to new connections on the virtual port.

  <Arguments>
    port
      The virtual port to stop listening on

  <Side effects>
    All multiplexers will stop waiting on the local port

  <Returns>
    None
  """
  # Get the values by spliting on colon
  arr = key.split(":")
  ip = arr[0]
  port = int(arr[1])

  # De-register this function for new multiplexers
  del MULTIPLEXER_WAIT_FUNCTIONS[key]
  
  # Map this stopcomm to all existing multiplexers
  for (key, mux) in MULTIPLEXER_OBJECTS.items():
    mux.stopcomm(port)
  