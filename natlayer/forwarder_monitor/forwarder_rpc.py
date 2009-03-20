# RJ - using my GENI port '63111' for all ports.
#


# Get the NATLayer
#begin include NATLayer_rpc.py
"""

Author: Armon Dadgar

Start Date: January 22nd, 2009

Description:
Provides a method of transferring data to machines behind firewalls or Network Address Translation (NAT).
Abstracts the forwarding specification into a series of classes and functions.

"""

#begin include forwarder_advertise.py
#begin include centralizedadvertise.repy
""" 
Author: Justin Cappos

Start Date: July 8, 2008

Description:
Advertisements to a central server (similar to openDHT)


"""

#begin include session.repy
# This module wraps communications in a signaling protocol.   The purpose is to
# overlay a connection-based protocol with explicit message signaling.   
#
# The protocol is to send the size of the message followed by \n and then the
# message itself.   The size of a message must be able to be stored in 
# sessionmaxdigits.   A size of -1 indicates that this side of the connection
# should be considered closed.
#
# Note that the client will block while sending a message, and the receiver 
# will block while recieving a message.   
#
# While it should be possible to reuse the connectionbased socket for other 
# tasks so long as it does not overlap with the time periods when messages are 
# being sent, this is inadvisable.

class SessionEOF(Exception):
  pass

sessionmaxdigits = 20

# get the next message off of the socket...
def session_recvmessage(socketobj):

  messagesizestring = ''
  # first, read the number of characters...
  for junkcount in range(sessionmaxdigits):
    currentbyte = socketobj.recv(1)

    if currentbyte == '\n':
      break
    
    # not a valid digit
    if currentbyte not in '0123456789' and messagesizestring != '' and currentbyte != '-':
      raise ValueError, "Bad message size"
     
    messagesizestring = messagesizestring + currentbyte

  else:
    # too large
    raise ValueError, "Bad message size"

  messagesize = int(messagesizestring)
  
  # nothing to read...
  if messagesize == 0:
    return ''

  # end of messages
  if messagesize == -1:
    raise SessionEOF, "Connection Closed"

  if messagesize < 0:
    raise ValueError, "Bad message size"

  data = ''
  while len(data) < messagesize:
    chunk =  socketobj.recv(messagesize-len(data))
    if chunk == '': 
      raise SessionEOF, "Connection Closed"
    data = data + chunk

  return data

# a private helper function
def session_sendhelper(socketobj,data):
  sentlength = 0
  # if I'm still missing some, continue to send (I could have used sendall
  # instead but this isn't supported in repy currently)
  while sentlength < len(data):
    thissent = socketobj.send(data[sentlength:])
    sentlength = sentlength + thissent



# send the message 
def session_sendmessage(socketobj,data):
  header = str(len(data)) + '\n'
  session_sendhelper(socketobj,header)

  session_sendhelper(socketobj,data)




#end include session.repy
servername = "satya.cs.washington.edu"
serverport = 10101

def centralizedadvertise_announce(key, value, ttlval):

  sockobj = openconn(servername,serverport)
  try:
    session_sendmessage(sockobj, "PUT|"+str(key)+"|"+str(value)+"|"+str(ttlval))
    response = session_recvmessage(sockobj)
    if response != 'OK':
      raise Exception, "Centralized announce failed '"+response+"'"
  finally:
    sockobj.close()
  
  return True
      



def centralizedadvertise_lookup(key, maxvals=100):
  sockobj = openconn(servername,serverport)
  try:
    session_sendmessage(sockobj, "GET|"+str(key)+"|"+str(maxvals))
    recvdata = session_recvmessage(sockobj)
    # worked
    if recvdata.endswith('OK'):
      return recvdata[:-len('OK')].split(',')
    raise Exception, "Centralized lookup failed"
  finally:
    sockobj.close()
      



#end include centralizedadvertise.repy

"""

Author: Dennis Ding

Start date: January 22, 2009

Description: Provides the implentation to register and lookup the IP address of potential forwarders

"""


# forwarder advertise registers all forwarder ip addresses under the key 'forwarder' 
# does not have open DHT
    
def forwarder_advertise(waittime = 300):
  myip = getmyip()

  while True:	
    #try:
    centralizedadvertise_announce('forwarder', myip, 600)
    #except:
    sleep(waittime)


def forwarder_lookup(maxvals = 100):
  # get the list of forwarders
  flist = centralizedadvertise_lookup('forwarder', maxvals)
	
  # grab random forwarder
  index = int(randomfloat() * len(flist))
	
	
  # store the value
  mycontext['currforwarder'] = flist[index]

# below is code for starting the forwarder advertise thread in repy

#if callfunc == 'initialize':
#	mycontext['forwarderip'] = getmyip()
#	settimer(0, fadvertise, [] )


#end include forwarder_advertise.py
#begin include server_advertise.py
#begin include centralizedadvertise.repy
#already included centralizedadvertise.repy
#end include centralizedadvertise.repy


# both sadvertise and slookup takes a mac address as key

def server_advertise(key, waittime = 180):
  while True:
    # register current forwader under key
    centralizedadvertise_announce(key, mycontext['currforwarder'], waittime * 2)

    sleep(waittime)

def server_lookup(key, maxvals = 100):

  # given a key, e.g. mac address, finds the currforwarder of target user
  mycontext['targetforwarder'] =  centralizedadvertise_lookup(key)
	


#below is the code for starting the server advertise thread in repy
	
#if callfunc == 'initialize':
#	settimer(0, sadvertise, [mycontext['forwarderip']] )

#end include server_advertise.py
#begin include Multiplexer.py
"""

Author: Armon Dadgar

Start Date: February 16th, 2009

Description:
Provides a means of multiplexing any stream-like connection into a multiple
socket-like connections.

Details:
There are 3 main objects in the Multiplexer
++ MultiplexerFrame
-- This objects is like a meta-"packet" in that it encapsulates a some data with a header
-- The header allows the Multiplexer to route the data to the correct destination

++ Multiplexer
-- This object is takes a single stream-like object that has the properties of being
-- in-order and lossless and multiplexes that single connection into any number of virtual connections.
-- At its heart, there is one thread the socketReader which reads all incoming data and either evaluates control messages
-- or buffers data for clients

++ MultiplexerSocket
-- When the multiplexer creates virtual sockets, a MultiplexerSocket is returned. This socket is tied to its parent multiplexer
-- since that parent buffers all of the incoming data for this socket. 

These three objects are wrapped in several mux_* functions, which abstract the details of the Multiplexer
and provide a repy like interface for easily multiplexing a normal TCP connection. mux_remap can be used to
multiplex any type of connection.

"""

# This is to help send dictionaries as strings
#begin include deserialize.py
"""

Author: Armon Dadgar

Start Date: February 16th, 2009

Description:
Functions to reconstruct objects from their string representation.

"""
# Constants for the types, these are the supported object types
DERSERIALIZE_DICT = 1
DERSERIALIZE_LIST = 2
DERSERIALIZE_TUPLE = 3

# Convert a string, which either a boolean, None, floating point number,
# long, or int to a primitive, not string type
def deserialize_stringToPrimitive(inStr):
  try:
    # Check if it is None
    if inStr == "None":
      return None
      
    # Check if it is boolean
    if inStr == "True":
      return True
    elif inStr == "False":
      return False
    
    # Check if it is floating point
    if inStr.find(".") != -1:
      val = float(inStr)
  
    # It must be a long/int
    else:
      # It is a long if it has an L suffix
      if inStr[-1] == 'L':
        val = long(inStr)
      else:
        val = int(inStr)
  except:
    return inStr
  
  return val

# Returns an array with the index of the search char
def deserialize_findChar(char, str):
  indexes = []
  
  # Look for all starting braces
  location = 0
  first = True
  while first or index != -1:
    # Turn first off
    if first:
      first = False

    # Search for sub dictionaries
    index = str.find(char,location)

    # Add the index, update location
    if index != -1:
      indexes.append(index)
      location = index+1   
  
  return indexes
      
# Find sub-objects
def deserialize_findSubObjs(str):
  # Object types
  objectStarts = {"{":DERSERIALIZE_DICT,"[":DERSERIALIZE_LIST,"(":DERSERIALIZE_TUPLE}
  objectEnds = {"}":DERSERIALIZE_DICT,"]":DERSERIALIZE_LIST,")":DERSERIALIZE_TUPLE}
  
  # Location of the start and end braces
  startIndexes = []
  for (start, type) in objectStarts.items():
    startIndexes += deserialize_findChar(start, str)
  startIndexes.sort()
  
  # Check if any sub-dicts exist    
  if len(startIndexes) == 0:
    return []
  
  endIndexes = []
  for (end, type) in objectEnds.items():
    endIndexes += deserialize_findChar(end, str)          
  endIndexes.sort()
  
  # Partitions of the string
  partitions = []
  
  startindex = 0
  endindex = 0
  
  while True:    
    maxStartIndex = len(startIndexes) - 1
    
    if maxStartIndex == -1:
      break
      
    if maxStartIndex == startindex or endIndexes[endindex] < startIndexes[startindex+1]:
      partitions.append([startIndexes[startindex],endIndexes[endindex],startindex,objectStarts[str[startIndexes[startindex]]]])
      del startIndexes[startindex]
      del endIndexes[endindex]
      startindex = 0
      endindex = 0
    else:
      startindex += 1
  
  return partitions
  
# Returns an object from the string filler
def deserialize_partitionedObj(value, partitions):
  index = int(value.lstrip("#"))
  return partitions[index]

# Modifies the start and end indexes of all elements in the array
# by indexOffset if they are greater than the start index
def deserialize_indexOffsetAdjustment(array, start, indexOffset):
  index = 0
  
  while index < len(array):
    if array[index][0] > start:
      array[index][0] -= indexOffset
    if array[index][1] > start:
      array[index][1] -= indexOffset
    index += 1
    
# Removes all string objects from a larger string
def deserialize_removeStringObjects(strIn, partitions):
  # Get strings starting with a single quote
  substrings1 = deserialize_findChar("'",strIn)
  
  # Get strings starting with a double quote
  substrings2 = deserialize_findChar("\"",strIn)
  
  # Calculate the lengths
  num1 = len(substrings1)
  num2 = len(substrings2)    
  partitionIndex = len(partitions)
  
  # Actual top level strings
  substrings = []
  
  # Filter out strings inside other strings
  subIndex1 = 0
  subIndex2 = 0
  if num1 != 0 and num2 != 0:
    while True:
      # Get the indexes of both lists
      start1 = substrings1[subIndex1]
      start2 = substrings2[subIndex2]
    
      # If the start index of one is lower than the other, then 
      # remove all members until we reach the closing quote
      if start1<start2:
        # Get the index value of the closing quote
        endIncrement = substrings1[subIndex1+1]
      
        # While there are strings between the starting and closing quote, remove them
        while num2 != 0 and endIncrement > start2:
          del substrings2[subIndex2]
          num2 -= 1
          if num2 == subIndex2:
            break
          start2 = substrings2[subIndex2]
      
        # Add the current start and end to the list of substrings
        substrings.append([start1,endIncrement])
        subIndex1 += 2
        
      elif start2<start1:
        # Get the index value of the closing quote
        endIncrement = substrings2[subIndex2+1]
      
        # While there are strings between the starting and closing quote, remove them
        while num1 != 0 and endIncrement > start1:
          del substrings1[subIndex1]
          num1 -= 1
          if num1 == subIndex1:
            break
          start1 = substrings1[subIndex1]
      
        # Add the current start and end to the list of substrings
        substrings.append([start2,endIncrement])
        subIndex2 += 2
    
      # Break if we've hit the end of either list
      if subIndex1 >= num1 or subIndex2 >= num2:
        break
  
  # Add any remaining substrings, that were not nested
  while subIndex1+1 < num1:
    substrings.append([substrings1[subIndex1],substrings1[subIndex1+1]])
    subIndex1 += 2
  while subIndex2+1 < num2:
    substrings.append([subIndex2[subIndex2],subIndex2[subIndex2+1]])
    subIndex2 += 2
  
  # Cleanup
  substrings1 = None
  substrings2 = None
    
  # Remove every substring and store as an object
  for sub in substrings:
    # Get the info for the string
    (start,end) = sub
    
    # Extract the real string, store it
    actualstr = strIn[start+1:end] # Add one to the start to avoid including the single quotes
    partitions.append(actualstr)
    
    # Replace the string in the larger string with a filler
    addIn = "#"+str(partitionIndex)
    partitionIndex += 1
    strIn = strIn[0:start]+addIn+strIn[end+1:]
    
    # Modify the indexes of the existing strings
    indexOffset = 1+end-start
    indexOffset -= len(addIn)
    deserialize_indexOffsetAdjustment(substrings, start, indexOffset)
    
  return strIn  

# Removes all lists and dictionary objects from the string, begins deserializing
# objects from the innermost depth upward
def deserialize_removeObjects(strIn, partitions=[]):  
  # Find all the sub objects
  subObjs = deserialize_findSubObjs(strIn)
  
  # Get the current length of the partitions
  partitionIndex = len(partitions)
    
  # Determine maximum depth
  maxDepth = 0
  for obj in subObjs:
    maxDepth = max(maxDepth, obj[2])
  
  # Start at the lowest depth and work upward
  while maxDepth >= 0:
    for obj in subObjs:
      (start,end,depth,type) = obj
      if depth == maxDepth:
        # Switch deserialization method on type
        if type == DERSERIALIZE_DICT:
          realObj = deserialize_dictObj(strIn[start:end+1],partitions)
        elif type == DERSERIALIZE_LIST:
          realObj = deserialize_listObj(strIn[start:end+1],partitions)
        elif type == DERSERIALIZE_TUPLE:
          realObj = deserialize_tupleObj(strIn[start:end+1],partitions)
        
        # Store the real object
        partitions.append(realObj)
        
        # Replace the string representation of the object with a filler
        addIn = "#"+str(partitionIndex)
        partitionIndex += 1
        strIn = strIn[0:start]+addIn+strIn[end+1:]
        
        # Modify the indexes now that the string length has changed
        indexOffset = 1+end-start
        indexOffset -= len(addIn)
        deserialize_indexOffsetAdjustment(subObjs, start, indexOffset)
    
    # Go up to a higher depth        
    maxDepth -= 1
  
  return strIn
          
# Convert a string representation of a Dictionary back into a dictionary
def deserialize_dictObj(strDict, partitions):
  # Remove dict brackets
  strDict = strDict[1:len(strDict)-1]
    
  # Get key/value pairs by exploding on commas
  keyVals = strDict.split(", ")

  # Create new dictionary
  newDict = {}

  # Process each key/Value pair
  for pair in keyVals:
    (key, value) = pair.split(": ",1)
    
    # Convert key to primitive
    if (key[0] == "#"):
      key = deserialize_partitionedObj(key,partitions)
    else:
      key = deserialize_stringToPrimitive(key)
    
    # Convert value to primitive
    if (value[0] == "#"):
      value = deserialize_partitionedObj(value,partitions)
    else:
      value = deserialize_stringToPrimitive(value)
  
    # Add key/value pair
    newDict[key] = value

  return newDict

# Convert a string representation of a list back into a list
def deserialize_listObj(strList, partitions):
  # Remove list brackets
  strList = strList[1:len(strList)-1]

  # Get values by exploding on commas
  values = strList.split(", ")

  # Create new list
  newList = []

  # Process each value
  for value in values:
    # Check for a sub-object filler
    if (value[0] == "#"):
      value = deserialize_partitionedObj(value,partitions)

    # Else this is a primitive type
    else:
      value = deserialize_stringToPrimitive(value)

    # Store the element
    newList.append(value)

  return newList
      
# Convert a string representation of a tuple back into a tuple
def deserialize_tupleObj(strList, partitions):
  # Remove tuple brackets
  strList = strList[1:len(strList)-1]

  # Get values by exploding on commas
  values = strList.split(", ")

  # Create new tuple
  newTuple = ()

  # Process each value
  for value in values:
    # Check for a sub-object filler
    if (value[0] == "#"):
      value = deserialize_partitionedObj(value,partitions)
    
    # Else this is a primitive type
    else:
      value = deserialize_stringToPrimitive(value)
      
    # Store the element
    newTuple += (value,)

  return newTuple  

# Converts a string representation of a list or dictionary 
# back into the real object. This works with sub-lists, sub-dictionaries,
# as well as strings, longs, ints, floats, and bools
def deserialize(string):
  # Array of partitions
  partitions = []
  
  # If there is an error, try to give specific feedback
  # Remove the sub-strings
  try:
    string = deserialize_removeStringObjects(string, partitions)
  except:
    raise ValueError, "Complicated sub-strings failed to parse!"
  
  # Remove the sub-objects
  try:
    string = deserialize_removeObjects(string, partitions)
  except:
    raise ValueError, "Complicated sub-objects failed to parse!"
    
  # Retrieve the top level object
  try:
    root = deserialize_partitionedObj(string, partitions)
  except:
    raise ValueError, "Failed to retrieve top-level object!"
  
  return root
  


#end include deserialize.py

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
     
    # Close each individual socket
    for refID, sock in self.virtualSockets.items():
      self._closeCONN(sock, refID) 
    
    # Close the real socket
    if closeSocket and self.socket != None:
      self.socket.close()
      self.socket = None
    
    # Cancel all pending sockets, this is so they get
    # connection refused instead of timed out
    for refID, info in self.pendingSockets.items():
      # Cancel the timeout timer
      canceltimer(info[2])
    
      # Set the handle to None, so that Connection Refused is infered
      info[2] = None
    
      # Unblock openconn
      try:
        info[1].release()
      except:
        pass

      
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
      raise AttributeError, "Multiplexer is not yet initialized or is closed!"
            
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
      raise AttributeError, "Multiplexer is not yet initialized or is closed!"
    
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
      raise AttributeError, "Multiplexer is not yet initialized or is closed!"
    
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
      raise AttributeError, "Multiplexer is not yet initialized or is closed!"
      
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
    socket.socketLocks["send"].acquire()
    
    # Increase the buffer size
    socket.bufferInfo["outgoing"] = num
    
    # Release the outgoing lock, this unblocks socket.send
    try:
      socket.socketLocks["outgoing"].release()
    except:
      # That means the lock was already released
      pass
    
    # Release the socket
    socket.socketLocks["send"].release()
    
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
    socket.socketLocks["recv"].acquire()
    
    # Increase the buffer size
    socket.buffer += frame.content
    
    # Release the outgoing lock, this unblocks socket.send
    try:
      socket.socketLocks["nodata"].release()
    except:
      # That means the lock was already released
      pass
    
    # Release the socket
    socket.socketLocks["recv"].release()
    
  
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
    # If this thread crashes, close the multiplexer
    try:
      # This thread is responsible for reading all incoming frames,
      # so it pushes data into the buffers, initializes new threads for each new client
      # and handles all administrative frames
      while True:
        # Should we quit?
        if not self.connectionInit:
          break
      
        # Read in a frame
        try:
          frame = self._recvFrame()
          refID = frame.referenceID
          frameType = frame.mesgType
        except:
          # This is probably because the socket is now closed, so lets loop around and see
          continue
      
        # It is possible we recieved a close command while doing recv, so lets check again and handle this
        if not self.connectionInit:
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
    
    # We caught an exception, close the multiplexer and exit
    except Exception, err:
      # Close
      self.close()
      

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
    self.socketLocks = {"recv":getlock(),"send":getlock(),"nodata":getlock(),"outgoing":getlock()}
    
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
    self.socketLocks["recv"].acquire()
  
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
    self.socketLocks["recv"].release() 
    
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
      self.socketLocks["send"].acquire()
      
      # How much outgoing traffic is available?
      outgoingAvailable = self.bufferInfo["outgoing"]
      
      # If we can, just send it all at once
      if len(data) < outgoingAvailable:
        try:
          # Instruct the multiplexer object to send our data
          self.mux._send(self.id, data)
        except AttributeError:
          # The multiplexer may be closed
          # Check if the socket is closed
          self._handleClosed()
        
        # Reduce the size of outgoing avail
        self.bufferInfo["outgoing"] -= len(data)
        
        # Release the lock
        self.socketLocks["send"].release()
          
        # We need to explicitly leave the loop
        break
        
      # We need to send chunks, while waiting for more outgoing B/W
      else:
        # Get a chunk of data, and send it
        chunk = data[:outgoingAvailable]
        try:
          # Instruct the multiplexer object to send our data
          self.mux._send(self.id, chunk)
        except AttributeError:
          # The multiplexer may be closed
          # Check if the socket is closed
          self._handleClosed()
      
        # Reduce the size of outgoing avail
        self.bufferInfo["outgoing"] = 0

        # Lock the outgoing lock, so that we block until we get a MULTIPLEXER_CONN_BUF_SIZE message
        self.socketLocks["outgoing"].acquire()
      
        # Trim data to only what isn't sent syet
        data = data[outgoingAvailable:]
    
        # Release the lock
        self.socketLocks["send"].release()
        
        # If there is no data left to send, then break
        if len(data) == 0:
          break


# Functional Wrappers for the Multiplexer objects

# This dictionary object links IP's to their respective multiplexer
MULTIPLEXER_OBJECTS = {}

# This dictionary has data about the underlying waitforconn operations
MULTIPLEXER_WAIT_HANDLES = {}

# This function has the underlying function calls
MULTIPLEXER_FUNCTIONS = {}

# Setup function pointers to be used by the multiplexer wrappers
MULTIPLEXER_FUNCTIONS["waitforconn"] = waitforconn
MULTIPLEXER_FUNCTIONS["openconn"] = openconn
MULTIPLEXER_FUNCTIONS["stopcomm"] = stopcomm

# This dictionary has all of the virtual waitforconn functions to propagate waitforconn to new muxes
# E.g. if a new host connects, it inherits all of the waitforconns on the existing muxes
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
    # Check if the multiplexer is still initialized
    status = MULTIPLEXER_OBJECTS[key].connectionInit
    
    # If the mux is not still initialized, then remove it and call ourselves again
    if not status:
      del MULTIPLEXER_OBJECTS[key]
      
      # Recursive call will re-initialize the mux
      return mux_openconn(desthost, destport, localip,localport,timeout,virtualport)
    
    # Since a connection already exists, do a virtual openconn
    else:
      return mux_virtual_openconn(desthost, destport, virtualport, localip,localport,timeout)

    # We need to establish a new multiplexer with this host
  else:
    # Get the correct function
    openconn_func = MULTIPLEXER_FUNCTIONS["openconn"]

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
  if key in MULTIPLEXER_WAIT_HANDLES:
    # Stop the last waitforconn, then make a new one
    mux_stopcomm(key)
    
  # Get the correct function
  waitforconn_func = MULTIPLEXER_FUNCTIONS["waitforconn"]
  
  # This adds ip and port and function information to help with multiplex waitforconns
  def _add_ip_port_func(remoteip, remoteport, socket, thiscommhandle, listencommhandle):
    _helper_mux_waitforconn(localip, localport, function, remoteip, remoteport, socket, thiscommhandle, listencommhandle)
  
  # Call waitforconn, and trigger our helper
  handle = waitforconn_func(localip, localport, _add_ip_port_func)
  
  # Register the handle
  MULTIPLEXER_WAIT_HANDLES[key] = handle
  
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
  if key in MULTIPLEXER_WAIT_HANDLES:
    # Retrieve the handle
    handle = MULTIPLEXER_WAIT_HANDLES[key]
    
    # Call stopcomm on it
    stopcomm_func = MULTIPLEXER_FUNCTIONS["stopcomm"]
    
    # Stopcomm
    stopcomm_func(handle)
    
    # Delete the handle
    del MULTIPLEXER_WAIT_HANDLES[key]

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
  MULTIPLEXER_FUNCTIONS["waitforconn"] = wait
  MULTIPLEXER_FUNCTIONS["openconn"] = open
  MULTIPLEXER_FUNCTIONS["stopcomm"] = stop


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

    try:
      return mux.openconn(desthost, virtualport, localip,localport,timeout)
    except AttributeError, err:
      if str(err) == "Multiplexer is not yet initialized or is closed!":
        # There has been a fatal error in this multiplexer, delete it
        del MULTIPLEXER_OBJECTS[key]
        
      raise EnvironmentError, "Connection Refused!"
      
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
    try:
      mux.waitforconn(localip, localport, function)
    except AttributeError, err:
      if str(err) == "Multiplexer is not yet initialized or is closed!":
        # There has been a fatal error in this multiplexer, delete it
        del MULTIPLEXER_OBJECTS[key]
      else:
        # Otherwise, it is something else
        raise err

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

# This functions stops and closes all multiplexer objects
def mux_stopall():
  """
  <Purpose>
    This is a general purpose cleanup routine for the multiplexer library.
    It will stop all multiplexers, remove any virtual and real waitforconn's,
    and close and delete all multiplexers. This will close all virtual sockets in the process.

  <Side effects>
    All multiplexers will stop and be destroyed.

  """ 
  # Map this close to all existing multiplexers
  for (key, mux) in MULTIPLEXER_OBJECTS.items():
    mux.close()
    del MULTIPLEXER_OBJECTS[key]
  
  # Stop all underlying waitforconns
  for key in MULTIPLEXER_WAIT_HANDLES.keys():
    # Map stopcomm to each key
    mux_stopcomm(key)
    
  # Remove all the wait functions
  for key in MULTIPLEXER_WAIT_FUNCTIONS.keys():
    mux_virtual_stopcomm(key) 
  

#end include Multiplexer.py
#begin include RPC_Constants.py
"""
This file declares and sets the constant values used for the forwarder RPC interface

RPC requests are dictionaries that have special fields
A typical request would be like the following:

# Server requests to de-register
rpc_req = {"id":0,"request":"de_reg_serv"}

# Forwarder responds with success message
rpc_resp = {"id":0,"status":True,"value":None}

# To actually transfer this request, the following is necessary:
message = encode_rpc(rpc_req)
sock.send(message)

# Then, to receive a RPC mesg
rpc_mesg = decode_rpc(sock)

"""
# This is used to decode RPC dictionaries
#begin include deserialize.py
#already included deserialize.py
#end include deserialize.py

# General Protocal Constants
RPC_VIRTUAL_IP = "0.0.0.0" # What IP is used for the virtual waitforconn / openconn
RPC_VIRTUAL_PORT = 0 # What virtual port to listen on for Remote Procedure Calls
RPC_FIXED_SIZE = 4   # Size of the RPC dictionary

# Defines fields
RPC_REQUEST_ID = "id"    # The identifier of the RPC request
RPC_FUNCTION = "request" # The remote function to call
RPC_PARAM = "value"      # The parameter to the requested function (if any)
RPC_ADDI_REQ = "additional" # Are there more RPC requests on the socket?
RPC_REQUEST_STATUS = "status" # The boolean status of the request
RPC_RESULT = "value"     # The result value if the RPC request

# Function Names
RPC_EXTERNAL_ADDR = "externaladdr"  # This allows the server to query its ip/port

# This allows a server to register with a forwarder
# This expects a MAC address as a parameter
RPC_REGISTER_SERVER = "reg_serv"    

RPC_DEREGISTER_SERVER = "dereg_serv"# This allows a server to de-register from a forwarder

# The following two functions require an integer port
RPC_REGISTER_PORT = "reg_port"      # THis allows the server to register a wait port
RPC_DEREGISTER_PORT = "dereg_port"  # This allows the server to de-register a wait port

# This instructs the forwarder to begin forwarding data from this socket to a server
# It expects the RPC_PARAM to be a dictionary:
# {"server":"__MAC__","port":50}
RPC_CLIENT_INIT = "client_init"

# Helper Functions
def RPC_encode(rpc_dict):
  """
  <Purpose>
    Encodes an RPC request dictionary
  
  <Arguments>
    rpc_dict:
      A dictionary object
  
  <Returns>
    Returns a string that can be sent over a socket
  """
  rpc_dict_str = str(rpc_dict) # Conver to string
  rpc_length = str(len(rpc_dict_str)).rjust(RPC_FIXED_SIZE, "0") # Get length string
  return rpc_length + rpc_dict_str # Concatinate size with string

def RPC_decode(sock,blocking=False):
  """
  <Purpose>
    Returns an RPC request object from a socket
  
  <Arguments>
    sock:
      A socket that supports recv
    
    blocking:
      If the socket supports the blocking mode of operations, speicify this to be True
  
  <Returns>
    Returns a dictionary object containing the RPC Request
  """
  # Get the dictionary length
  # Then, Get the dictionary
  if blocking:
    length = int(sock.recv(RPC_FIXED_SIZE,blocking=True))
    dict_str = sock.recv(length,blocking=True)
  else:
    length = int(sock.recv(RPC_FIXED_SIZE))
    dict_str = sock.recv(length)
  
  dict_obj = deserialize(dict_str) # Convert to object
  return dict_obj
  
#end include RPC_Constants.py

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
    server_lookup(localmac)
    forwarderIP = mycontext['currforwarder'][0]
    forwarderPort = 63111

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
    forwarderPort = 63111
  
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
  
# Determines if you are behind a NAT (Network-Address-Translation)
def behind_nat(forwarderIP=None,forwarderPort=None):
  # Get "normal" ip
  ip = getmyip()
  
  # TODO: Dennis you need to tie in here to get a real forwarder IP and port
  if forwarderIP == None or forwarderPort == None:
    server_lookup(localmac)
    forwarderIP = mycontext['currforwarder'][0]
    forwarderPort = 63111

  # Create a real connection to the forwarder
  rpcsocket = openconn(forwarderIP, forwarderPort)
  
  # Now connect to a forwarder, and get our external ip/port
  # Create a RPC dictionary
  rpc_request = {RPC_REQUEST_ID:5,RPC_FUNCTION:RPC_EXTERNAL_ADDR}
  rpc_mesg = RPC_encode(rpc_request)
  
  # Request, get the response
  rpcsocket.send(rpc_mesg)
  response = RPC_decode(rpcsocket)
  
  return (ip != response[RPC_RESULT]["ip"])
  
#end include NATLayer_rpc.py

# Get the RPC constants
#begin include RPC_Constants.py
#already included RPC_Constants.py
#end include RPC_Constants.py

FORWARDER_STATE = {"ip":"127.0.0.1","Next_Conn_ID":0}
SERVER_PORT = 63111  # What real port to listen on for servers
CLIENT_PORT = 63111  # What real port to listen on for clients
MAX_CLIENTS_PER_SERV = 8*2 # How many clients per server, the real number is this divided by 2
WAIT_INTERVAL = 3    # How long to wait after sending a status message before closing the socket
RECV_SIZE = 1024 # Size of chunks to exchange
CHECK_INTERVAL = 60  # How often to cleanup our state, e.g. remove dead multiplexers

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
DEBUG2 = False  # Prints verbose debug messages
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
    serverinfo = CONNECTIONS[conn_id]
    serverinfo["mac"] = value
    
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
def deregister_server(conn_id,value=None):
  # Get the server info
  serverinfo = CONNECTIONS[conn_id]
    
  # Remove the MAC address reverse lookup
  if "mac" in serverinfo:
    mac = serverinfo["mac"]
    if mac in MAC_ID_LOOKUP:
      MAC_ID_LOCK.acquire()  
      del MAC_ID_LOOKUP[mac]
      MAC_ID_LOCK.release()
  
  # Close the multiplexer
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
  
  # Get the server ports
  ports = serverinfo["ports"]
  
  # Convert value to int, and append to ports
  ports.add(value)
  
  return (True,None)


# De-register a wait port
def dereg_waitport(conn_id,value):
  # Get the server info
  serverinfo = CONNECTIONS[conn_id]
  
  # Get the server ports
  ports = serverinfo["ports"]
  
  # Convert value to int, and append to ports
  ports.discard(value)
  
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
  if not port in serverinfo["ports"]:
    return (False,NAT_STATUS_FAILED)
  
  # Try to get a virtual socket
  try:
    virtualsock = serverinfo["mux"].openconn(serverinfo["ip"], port,localip=conninfo["ip"],localport=conninfo["port"])
    
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
    info["ports"] = set()
    
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


# Handle new servers
def new_server(remoteip, remoteport, sock, thiscommhandle, listencommhandle):
  # DEBUG
  if DEBUG2: print getruntime(),"Server Conn.",remoteip,remoteport
  
  # Get the connection ID
  id = _get_conn_id()
  
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
  server_wait_handle = waitforconn(ip, SERVER_PORT, new_server)
  
  # Setup a port for clients to connect
  client_wait_handle = waitforconn(ip, CLIENT_PORT, inbound_connection)
  
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
  main()

