""" 
Author: Justin Cappos

Start Date: October 14, 2008

Description:
A stub that allows different announcement types.   I'd make this smarter, but
the user won't configure it, right?

"""

from repyportability import *

import openDHTadvertise
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

skipDHT = 0
previousDHTskip = 1
skipcentral = 0
previouscentralskip = 1

def announce(key, value, ttlval):
  global skipDHT
  global previousDHTskip
  global skipcentral
  global previouscentralskip

  
  if skipcentral == 0:
    try:
      centralizedadvertise_announce(key, value, ttlval)
      previouscentralskip = 1
    except Exception, e:
      print 'centralized:',e
      skipcentral = previouscentralskip + 1
      previouscentralskip = min(previouscentralskip * 2, 16)
      
  else:
    skipcentral = skipcentral - 1


  if skipDHT==0:
    try:
      openDHTadvertise.announce(key, value, ttlval)
      previousDHTskip = 1
    except Exception, e:
      print 'openDHT:',e
      skipDHT = previousDHTskip + 1
      previousDHTskip = min(previousDHTskip * 2, 16)
  else:
    skipDHT = skipDHT - 1



def uniq(a):
  retlist = []
  for item in a:
    if item not in retlist:
      retlist.append(item)

  return retlist



def lookup(key, maxvals=100):
  try:
    centralans = centralizedadvertise_lookup(key, maxvals)
  except Exception, e:
    centralans = []

  try:
    dhtans = openDHTadvertise.lookup(key, maxvals)
  except Exception, e:
    dhtans = []

  return uniq(centralans + dhtans)

