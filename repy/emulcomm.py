"""
   Author: Justin Cappos

   Start Date: 27 June 2008

   Description:

   This is a collection of communications routines that provide a programmer 
   with a reasonable environment.   This is used by repy.py to provide a 
   highly restricted (but usable) environment.
"""

import restrictions
import socket

# needed to set threads for recvmess and waitforconn
import threading

# to log errors
import sys

# So I can exit all threads when an error occurs or do select
import nonportable

# So I can print a clean traceback when an error happens
import tracebackrepy

# accounting
import nanny

# give me uniqueIDs for the comminfo table
import idhelper

# for sleep
import time 

# The architecture is that I have a thread which "polls" all of the sockets
# that are being listened on using select.  If a connection
# oriented socket has a connection pending, or a message-based socket has a
# message pending, and there are enough events it calls the appropriate
# function.





# Table of communications structures:
# {'type':'UDP','localip':ip, 'localport':port,'function':func,'socket':s, outgoing:True}
# {'type':'TCP','remotehost':None, 'remoteport':None,'localip':None,'localport':None, 'socket':s, 'function':func, outgoing:False}

comminfo = {}

# If we have a preference for an IP/Interface this flag is set to True
preference = False

# Armon: These ip's and interfaces are allowed
# Both lists can have an "any" key word that allows any ip or any ip on an interface
# By default, its just loopback but the user may add more with the --ip flag
# If no interface or IP is specified, then all ips will be allowed
allowedIPs = ['127.0.0.1'] 
allowedinterfaces = []

# This set caches the allowed IP's
# It is updated at the launch of repy, or by calls to getmyip
allowedcache = []
cachelock = threading.Lock()  # This allows only a single simultaneous cache update


### IP Iteration Stuff
def ip_is_allowed(ip):
  """
  <Purpose>
    Determines if a given IP is allowed, by checking against the cached allowed IP's.
  
  <Arguments>
    ip: The IP address to search for.
  
  <Returns>
    True, if allowed. False, otherwise.
  """
  global allowedcache
  global preference
  
  # If there is no preference, anything goes
  if not preference:
    return True
  
  # Check the set
  return (ip in allowedcache)
  

# This function updates the allowed IP cache
# It iterates through all possible IP's and stores ones which are bindable as part of the allowedcache
def update_ip_cache():
  global allowedcache
  global preference
  global allowedinterfaces
  global allowedIPs
  
  # If there is no preference, this is a no-op
  if not preference:
    return
    
  # Acquire the lock to update the cache
  cachelock.acquire()
    
  # Stores the IP's
  allowed_list = []
  
  # Mini-function because I'm too lazy to keep checking if the element
  # already exists
  # Prohibits adding "127.0.0.1", loopback is always added last
  def unique_append(lst, elem):
    if not (elem == "127.0.0.1") and elem not in lst:
      allowed_list.append(elem)
  
  # Adds all the IP's from an interface    
  def add_nic_ips(nic, lst):
    try:
      # Get the IP's associated with the NIC
      interface_ips = nonportable.osAPI.getInterfaceIPAddresses(nic)
      for interface_ip in interface_ips:
        unique_append(lst, interface_ip)
    except:
      # Catch exceptions if the NIC does not exist
      pass
  
  # Loop through allowed IP's appending to the allowed_list
  for ip in allowedIPs:
      unique_append(allowed_list, ip)
    
  # Loop through the allowed interfaces, appeneding to the allowed_list
  for nic in allowedinterfaces:
    # Handle the 'any' case
    if nic == "any":
      all_interfaces = nonportable.osAPI.getAvailableInterfaces() # Get all the interfaces
      for interface in all_interfaces:
        # Add all associated IP's
        add_nic_ips(interface, allowed_list)
    
      break # This adds all IP's from interfaces, no need to continue
    else:
      # Add all associated IP's
      add_nic_ips(nic, allowed_list)
  
  # This will store all the IP's that we are able to bind to
  bindable_list = []
        
  # Try binding to every ip
  for ip in allowed_list:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
      sock.bind((ip,0))
    except:
      pass # Not a good ip, skip it
    else:
      bindable_list.append(ip) # This is a good ip, store it
    finally:
      sock.close()

  # Add loopback
  bindable_list.append("127.0.0.1")
  
  # Update the global cache
  allowedcache = bindable_list
        
  # Release the lock
  cachelock.release()
  

########################### SocketSelector functions #########################



# used to lock the methods that check to see if the thread is running
selectorlock = threading.Lock()

# is the selector thread started...
selectorstarted = False


#### helper functions

# return the table entry for this socketobject
def find_socket_entry(socketobject):
  for commhandle in comminfo.keys():
    if comminfo[commhandle]['socket'] == socketobject:
      return comminfo[commhandle], commhandle
  raise KeyError, "Can't find commhandle"





# wait until there is a free event
def wait_for_event(eventname):
  while True:
    try:
      nanny.tattle_add_item('events',eventname)
      break
    except Exception:
      # They must be over their event limit.   I'll sleep and check later
      time.sleep(.1)



def should_selector_exit():
  global selectorstarted

  # Let's check to see if we should exit...   False means "nonblocking"
  if selectorlock.acquire(False):

    # Check that selector started is true.   This should *always* be the case
    # when I enter this function.   This is to test for bugs in my code
    if not selectorstarted:
      # This will cause the program to exit and log things if logging is
      # enabled. -Brent
      tracebackrepy.handle_internalerror("SocketSelector is started when" +
          ' selectorstarted is False', 39)

    # Got the lock...
    for comm in comminfo.values():
      # I'm listening and waiting so all is well
      if not comm['outgoing']:
        break
    else:
      # there is no listening function so I should exit...
      selectorstarted = False
      # I'm exiting...
      nanny.tattle_remove_item('events',"SocketSelector")
      selectorlock.release()
      return True

    # I should continue
    selectorlock.release()
  return False
    




# This function starts a thread to handle an entry with a readable socket in 
# the comminfo table
def start_event(entry, handle,eventhandle):
  if entry['type'] == 'UDP':
    # some sort of socket error, I'll assume they closed the socket or it's
    # not important
    try:
      # NOTE: is 4096 a reasonable maximum datagram size?
      data, addr = entry['socket'].recvfrom(4096)
    except socket.error:
      # they closed in the meantime?
      nanny.tattle_remove_item('events',eventhandle)
      return

    # wait if we're over the limit
    if data:
      if is_loopback(entry['localip']):
        nanny.tattle_quantity('looprecv',len(data))
      else:
        nanny.tattle_quantity('netrecv',len(data))
    else:
      # no data...   Let's stop this...
      nanny.tattle_remove_item('events',eventhandle)
      return

      
    try:
      EventDeliverer(entry['function'],(addr[0], addr[1], data, handle), eventhandle).start()
    except:
      # This is an internal error I think...
      # This will cause the program to exit and log things if logging is
      # enabled. -Brent
      tracebackrepy.handle_internalerror("Can't start UDP EventDeliverer", 29)



  # or it's a TCP accept event...
  elif entry['type'] == 'TCP':
    try:
      realsocket, addr = entry['socket'].accept()
    except socket.error:
      # they closed in the meantime?
      nanny.tattle_remove_item('events',eventhandle)
      return

    # put this handle in the table
    newhandle = idhelper.getuniqueid()
    safesocket = emulated_socket(newhandle)
    comminfo[newhandle] = {'type':'TCP','remotehost':addr[0], 'remoteport':addr[1],'localip':entry['localip'],'localport':entry['localport'],'socket':realsocket,'outgoing':True}
    # I don't think it makes sense to count this as an outgoing socket, does 
    # it?

    try:
      EventDeliverer(entry['function'],(addr[0], addr[1], safesocket, newhandle, handle),eventhandle).start()
    except:
      # This is an internal error I think...
      # This will cause the program to exit and log things if logging is
      # enabled. -Brent
      tracebackrepy.handle_internalerror("Can't start TCP EventDeliverer", 23)


  else:
    # Should never get here
    # This will cause the program to exit and log things if logging is
    # enabled. -Brent
    tracebackrepy.handle_internalerror("In start event, Unknown entry type", 51)





# Check for sockets using select and fire up user event threads as needed.
#
# This class holds nearly all of the complexity in this module.   It's 
# basically just a loop that gets pending sockets (using select) and then
# fires up events that call user provided functions
class SocketSelector(threading.Thread):
  
  def __init__(self):
    threading.Thread.__init__(self, name="SocketSelector")





  def run(self):
    while True:

      # I'll stop myself only when there are no active threads to monitor
      if should_selector_exit():
        return

      # get the list of socket objects we might have a pending request on
      requestlist = []
      for comm in comminfo.values():
        if not comm['outgoing']:
          requestlist.append(comm['socket'])

      # nothing to request.   We should loop back around and check if all 
      # sockets have been closed
      if requestlist == []:
        continue

      # I'd like to see if we have a pending request.   
      # wait for up to 1/2 second
      readylist = nonportable.select_sockets(requestlist, 0.5)

      # go through the pending sockets, grab an event and then start a thread
      # to handle the connection
      for thisitem in readylist:
        try: 
          commtableentry,commhandle = find_socket_entry(thisitem)
        except KeyError:
          # let's skip this one, it's likely it was closed in the interim
          continue

        # now it's time to get the event...   I'll loop until there is a free
        # event
        eventhandle = idhelper.getuniqueid()
        wait_for_event(eventhandle)

        # wait if already oversubscribed
        if is_loopback(commtableentry['localip']):
          nanny.tattle_quantity('looprecv',0)
        else:
          nanny.tattle_quantity('netrecv',0)

        # Now I can start a thread to run the user's code...
        start_event(commtableentry,commhandle,eventhandle)
        






# this gives an actual event to the user's code
class EventDeliverer(threading.Thread):
  func = None
  args = None
  eventid = None

  def __init__(self, f, a,e):
    self.func = f
    self.args = a
    self.eventid = e
    threading.Thread.__init__(self)

  def run(self):
    try:
      self.func(*(self.args))
    except:
      # we probably should exit if they raise an exception in a thread...
      tracebackrepy.handle_exception()
      nonportable.harshexit(14)

    finally:
      # our event is going away...
      nanny.tattle_remove_item('events',self.eventid)
      




        
#### used by other threads to interact with the SocketSelector...


# private.   Check if the SocketSelector is running and start it if it isn't
def check_selector():
  global selectorstarted

  # acquire the lock. 
  if selectorlock.acquire():
    # If I've not started, then start me...
    if not selectorstarted:
      # wait until there is a free event...
      wait_for_event("SocketSelector")
      selectorstarted = True
      SocketSelector().start()

    # verify a thread with the name "SocketSelector" is running
    for threadobj in threading.enumerate():
      if threadobj.getName() == "SocketSelector":
        # all is well
        selectorlock.release()
        return
  
    # this is bad.   The socketselector went away...
    # This will cause the program to exit and log things if logging is
    # enabled. -Brent
    tracebackrepy.handle_internalerror("SocketSelector died", 59)




# return the table entry for this type of socket, ip, port 
def find_tip_entry(socktype, ip, port):
  for commhandle in comminfo.keys():
    if comminfo[commhandle]['type'] == socktype and comminfo[commhandle]['localip'] == ip and comminfo[commhandle]['localport'] == port:
      return comminfo[commhandle], commhandle
  return (None,None)



# Find a commhandle, given TIPO: type, ip, port, outgoing
def find_tipo_commhandle(socktype, ip, port, outgoing):
  for commhandle in comminfo.keys():
    if comminfo[commhandle]['type'] == socktype and comminfo[commhandle]['localip'] == ip and comminfo[commhandle]['localport'] == port and comminfo[commhandle]['outgoing'] == outgoing:
      return commhandle
  return None









######################### Simple Public Functions ##########################



# Public interface
def gethostbyname_ex(name):
  """
   <Purpose>
      Provides information about a hostname.   Calls socket.gethostbyname_ex()

   <Arguments>
      name:
         The host name to get information about

   <Exceptions>
      As from socket.gethostbyname_ex()

   <Side Effects>
      None.

   <Returns>
      A tuple containing (hostname, aliaslist, ipaddrlist).   See the 
      python docs for socket.gethostbyname_ex()
  """

  restrictions.assertisallowed('gethostbyname_ex',name)

  # charge 4K for a look up...   I don't know the right number, but we should
  # charge something.   We'll always charge to the netsend interface...
  nanny.tattle_quantity('netsend',4096) 
  nanny.tattle_quantity('netrecv',4096)
  return socket.gethostbyname_ex(name)



# Public interface
def getmyip():
  """
   <Purpose>
      Provides the external IP of this computer.   Does some clever trickery.

   <Arguments>
      None

   <Exceptions>
      As from socket.gethostbyname_ex()

   <Side Effects>
      None.

   <Returns>
      The localhost's IP address
      python docs for socket.gethostbyname_ex()
  """

  restrictions.assertisallowed('getmyip')
  # I got some of this from: http://groups.google.com/group/comp.lang.python/browse_thread/thread/d931cdc326d7032b?hl=en
  
  # Update the cache and return the first allowed IP
  if preference:
    update_ip_cache()
    # Return the first allowed ip, there is always at least 1 element (loopback)
    return allowedcache[0]
  
  # Open a connectionless socket
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

  # Tell it to connect to google (we assume that the DNS entry for this works)
  # however, using port 0 causes some issues on FreeBSD!   I choose port 80 
  # instead...
  try:
    s.connect(('google.com', 80))
  except Exception, e:
    # I reraise the exception from here because exceptions raised by connect
    # are treated as "from a string" which confuses the traceback printer
    # unless I re-raise it here (then it lists my line which is culled)
    raise e

  # and the IP of the interface this connects on is the first item of the tuple
  (myip, localport) = s.getsockname() 
  
  s.close()


  if myip == '' or myip == '0.0.0.0':
    # It's possible on some platforms (Windows Mobile) that the IP will be
    # 0.0.0.0 even when I have a public IP and google is up.   However, if
    # I get a real connection with SOCK_STREAM, then I should get the real
    # answer.   
    # I'll do much the same as before, only using SOCK_STREAM, which 
    # unfortunately will actually connect
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
      s.connect(('google.com', 80))
    except Exception, e:
      raise e
    (myip, localport) = s.getsockname() 
  
    s.close()

  if myip == '' or myip == '0.0.0.0':
    # hmm, SOCK_STREAM failed too.   Let's raise an exception...
    raise Exception, "Cannot get external IP despite successful name resolution.  Sockets do not seem to behave properly"
  

  return myip








###################### Shared message / connection items ###################


# Used to decide if an IP is the loopback IP or not.   This is needed for 
# accounting
def is_loopback(host):
  if not host.startswith('127.'):
    return False
  if len(host.split('.')) != 4:
    return False

  for number in host.split('.'):
    for char in number:
      if char not in '0123456789':
        return False

    try:
      if int(number) > 255 or int(number) < 0:
        return False
    except ValueError:
      return False
 
  return True









# Public interface !!!
def stopcomm(commhandle):
  """
   <Purpose>
      Stop handling events for a commhandle.   This works for both message and
      connection based event handlers.

   <Arguments>
      commhandle:
         A commhandle as returned by recvmess or waitforconn.

   <Exceptions>
      None.

   <Side Effects>
      This has an undefined effect on a socket-like object if it is currently
      in use.

   <Returns>
      None.
  """

  # if it has already been cleaned up, exit.
  if commhandle not in comminfo:
    return

  restrictions.assertisallowed('stopcomm',comminfo[commhandle])

  cleanup(commhandle)



# Armon: How frequently should we check for the availability of the socket?
RETRY_INTERVAL = 0.2 # In seconds

# Private
def cleanup(handle):
  try:
    comminfo[handle]['socket'].close()
  except:
    pass

  # if it's in the table then remove the entry and tattle...
  if handle in comminfo:    
    info = comminfo[handle]  # Store the info
    del comminfo[handle]

    if info['outgoing']:
      nanny.tattle_remove_item('outsockets', handle)
    else:
      nanny.tattle_remove_item('insockets', handle)
      
      # Armon: Block while the socket is not yet cleaned up
      # Get the socket info
      ip = info['localip']
      port = info['localport']
      socketType = info['type']
      tcp = (socketType == 'TCP') # Check if this is a TCP typed connection
      
      # Loop until the socket no longer exists
      while nonportable.osAPI.existsListeningNetworkSocket(ip,port, tcp):
        time.sleep(RETRY_INTERVAL)
        




####################### Message sending #############################



# Public interface!!!
def sendmess(desthost, destport, message,localip=None,localport = 0):
  """
   <Purpose>
      Send a message to a host / port

   <Arguments>
      desthost:
         The host to send a message to
      destport:
         The port to send the message to
      message:
         The message to send
      localhost (optional):
         The local IP to send the message from 
      localport (optional):
         The local port to send the message from (0 for a random port)

   <Exceptions>
      socket.error when communication errors happen

   <Side Effects>
      None.

   <Returns>
      The number of bytes sent on success
  """
  if not localip or localip == '0.0.0.0':
    localip = None

  if type(destport) is not int and type(destport) is not long:
    raise Exception("Destination port number must be an integer")

  if type(localport) is not int and type(localport) is not long:
    raise Exception("Local port number must be an integer")

  restrictions.assertisallowed('sendmess', desthost, destport, message,localip,localport)

  if localport:
    nanny.tattle_check('messport',localport)

  # Armon: Check if the specified local ip is allowed
  # this check only makes sense if the localip is specified
  if localip and not ip_is_allowed(localip):
    raise Exception, "IP '"+str(localip)+"' is not allowed."
  
  # If there is a preference, but no localip, then get one
  elif preference and not localip:
    # Use whatever getmyip returns
    localip = getmyip()

  # this is used to track errors when trying to resend data
  firsterror = None

  if localip and localport:
    # let's see if the socket already exists...
    commtableentry,commhandle = find_tip_entry('UDP',localip,localport)
  else:
    # no, we'll skip
    commhandle = None

  # yes it does! let's use the existing socket
  if commhandle:

    # block in case we're oversubscribed
    if is_loopback(desthost):
      nanny.tattle_quantity('loopsend',0)
    else:
      nanny.tattle_quantity('netsend',0)

    # try to send using this socket
    try:
      bytessent =  commtableentry['socket'].sendto(message,(desthost,destport))
    except socket.error,e:
      # we're going to save this error in case we also get an error below.   
      # This is likely to be the error we actually want to raise
      firsterror = e
      # should I really fall through here?
    else:
      # send succeeded, let's wait and return
      if is_loopback(desthost):
        nanny.tattle_quantity('loopsend',bytessent)
      else:
        nanny.tattle_quantity('netsend',bytessent)
      return bytessent
  

  # open a new socket
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

  # reuse the socket if it's "pseudo-availible"
  s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


  try:
    if localip:
      try:
        s.bind((localip,localport))
      except socket.error, e:
        if firsterror:
          raise Exception, firsterror
        raise Exception, e

    # wait if already oversubscribed
    if is_loopback(desthost):
      nanny.tattle_quantity('loopsend',0)
    else:
      nanny.tattle_quantity('netsend',0)

    bytessent =  s.sendto(message,(desthost,destport))

    if is_loopback(desthost):
      nanny.tattle_quantity('loopsend',bytessent)
    else:
      nanny.tattle_quantity('netsend',bytessent)

    return bytessent

  finally:
    # close no matter what
    try:
      s.close()
    except:
      pass






# Public interface!!!
def recvmess(localip, localport, function):
  """
   <Purpose>
      Registers a function as an event handler for incoming messages

   <Arguments>
      localip:
         The local IP or hostname to register the handler on
      localport:
         The port to listen on
      function:
         The function that messages should be delivered to.   It should expect
         the following arguments: (remoteIP, remoteport, message, commhandle)

   <Exceptions>
      None.

   <Side Effects>
      Registers an event handler.

   <Returns>
      The commhandle for this event handler.
  """
  if not localip or localip == '0.0.0.0':
    raise Exception("Must specify a local IP address")

  if type(localport) is not int and type(localport) is not long:
    raise Exception("Local port number must be an integer")

  restrictions.assertisallowed('recvmess',localip,localport)

  nanny.tattle_check('messport',localport)
  
  # Armon: Check if the specified local ip is allowed
  if not ip_is_allowed(localip):
    raise Exception, "IP '"+localip+"' is not allowed."

  # check if I'm already listening on this port / ip
  # NOTE: I check as though there might be a socket open that is sending a
  # message.   This is nonsense since sendmess doesn't result in a socket 
  # persisting.   This is done so that if sockets for sendmess are cached 
  # later (as seems likely) the resulting code will not break.
  oldhandle = find_tipo_commhandle('UDP', localip, localport, False)
  if oldhandle:
    # if it was already there, update the function and return
    comminfo[oldhandle]['function'] = function
    return oldhandle
    

  handle = idhelper.getuniqueid()

  # we'll need to add it, so add a socket...
  nanny.tattle_add_item('insockets',handle)

  # get the socket
  try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # reuse the socket if it's "pseudo-availible"
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((localip,localport))

    nonportable.preparesocket(s)
  except:
    try:
      s.close()
    except:
      pass
    nanny.tattle_remove_item('insockets',handle)
    raise

  # set up our table entry
  comminfo[handle] = {'type':'UDP','localip':localip, 'localport':localport,'function':function,'socket':s, 'outgoing':False}

  # start the selector if it's not running already
  check_selector()

  return handle













####################### Connection oriented #############################




# Public interface!!!
def openconn(desthost, destport,localip=None, localport=0,timeout=5.0):
  """
   <Purpose>
      Opens a connection, returning a socket-like object

   <Arguments>
      desthost:
         The host to open communcations with
      destport:
         The port to use for communication
      localip (optional):
         The local ip to use for the communication
      localport (optional):
         The local port to use for communication (0 for a random port)
      timeout (optional):
         The maximum amount of time to wait to connect

   <Exceptions>
      As from socket.connect, etc.

   <Side Effects>
      None.

   <Returns>
      A socket-like object that can be used for communication.   Use send, 
      recv, and close just like you would an actual socket object in python.
  """
  if not localip or localip == '0.0.0.0':
    localip = None

  if type(destport) is not int and type(destport) is not long:
    raise Exception("Destination port number must be an integer")

  if type(localport) is not int and type(localport) is not long:
    raise Exception("Local port number must be an integer")

  # Armon: Check if the specified local ip is allowed
  # this check only makes sense if the localip is specified
  if localip and not ip_is_allowed(localip):
    raise Exception, "IP '"+str(localip)+"' is not allowed."

  # If there is a preference, but no localip, then get one
  elif preference and not localip:
    # Use whatever getmyip returns
    localip = getmyip()

  restrictions.assertisallowed('openconn',desthost,destport,localip,localport)

  if localport:
    nanny.tattle_check('connport',localport)

  handle = idhelper.getuniqueid()
  nanny.tattle_add_item('outsockets',handle)

  try:
    s = get_real_socket(localip,localport)

  
    # add the socket to the comminfo table
    comminfo[handle] = {'type':'TCP','remotehost':None, 'remoteport':None,'localip':localip,'localport':localport,'socket':s, 'outgoing':True}
  except:
    # the socket wasn't passed to the user prog...
    nanny.tattle_remove_item('outsockets',handle)
    raise


  try:
    thissock = emulated_socket(handle)
    # We set a timeout before we connect.  This allows us to timeout slow 
    # connections...
    oldtimeout = comminfo[handle]['socket'].gettimeout()
    try:
      comminfo[handle]['socket'].settimeout(timeout)
      comminfo[handle]['socket'].connect((desthost,destport))
    except Exception, e:
      # I reraise the exception from here because exceptions raised by connect
      # are treated as "from a string" which confuses the traceback printer
      # unless I re-raise it here (then it lists my line which is culled)
      raise e
    finally:
      # and restore the old timeout...
      comminfo[handle]['socket'].settimeout(oldtimeout)
    comminfo[handle]['remotehost']=desthost
    comminfo[handle]['remoteport']=destport
  except:
    cleanup(handle)
    raise

  return thissock




# Public interface!!!
def waitforconn(localip, localport,function):
  """
   <Purpose>
      Waits for a connection to a port.   Calls function with a socket-like 
      object if it succeeds.

   <Arguments>
      localip:
         The local IP to listen on
      localport:
         The local port to bind to
      function:
         The function to call.   It should take five arguments:
         (remoteip, remoteport, socketlikeobj, thiscommhandle, maincommhandle)
         If your function has an uncaught exception, the socket-like object it
         is using will be closed.
         
   <Exceptions>
      None.

   <Side Effects>
      Starts an event handler that listens for connections.

   <Returns>
      A handle to the comm object.   This can be used to stop listening
  """
  if not localip or localip == '0.0.0.0':
    raise Exception("Must specify a local IP address")

  if type(localport) is not int and type(localport) is not long:
    raise Exception("Local port number must be an integer")

  restrictions.assertisallowed('waitforconn',localip,localport)

  nanny.tattle_check('connport',localport)

  # Armon: Check if the specified local ip is allowed
  if not ip_is_allowed(localip):
    raise Exception, "IP '"+localip+"' is not allowed."

  # check if I'm already listening on this port / ip
  oldhandle = find_tipo_commhandle('TCP', localip, localport, False)
  if oldhandle:
    # if it was already there, update the function and return
    comminfo[oldhandle]['function'] = function
    return oldhandle
    

  handle = idhelper.getuniqueid()
  # we'll need to add it, so add a socket...
  nanny.tattle_add_item('insockets',handle)

  # get the socket
  try:
    mainsock = get_real_socket(localip,localport)
    # NOTE: Should this be anything other than a hardcoded number?
    mainsock.listen(5)
    # set up our table entry
    comminfo[handle] = {'type':'TCP','remotehost':None, 'remoteport':None,'localip':localip,'localport':localport,'socket':mainsock, 'outgoing':False, 'function':function}
  except:
    nanny.tattle_remove_item('insockets',handle)
    raise


  # start the selector if it's not running already
  check_selector()

  return handle





# Private
def get_real_socket(localip=None, localport = None):

  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

  # reuse the socket if it's "pseudo-availible"
  s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


  if localip and localport:
    try:
      s.bind((localip,localport))
    except socket.error, e:
      # don't leak sockets
      s.close()
      raise Exception, e
    except:
      # don't leak sockets
      s.close()
      raise

  return s











# Public.   We pass these to the users for communication purposes
class emulated_socket:
  # This is an index into the comminfo table...

  commid = 0

  def __init__(self, handle):
    self.commid = handle
    return None 




  def close(self,*args):
    # prevent TOCTOU race with client changing the object's properties
    mycommid = self.commid
    restrictions.assertisallowed('socket.close',*args)
    stopcomm(mycommid)



  def recv(self,bytes):
    # prevent TOCTOU race with client changing the object's properties
    mycommid = self.commid
    restrictions.assertisallowed('socket.recv',bytes)

    # I set this here so that I don't screw up accounting with a keyerror later
    try:
      this_is_loopback = is_loopback(comminfo[mycommid]['remotehost'])
    # they likely closed the connection
    except KeyError:
      raise Exception, "Socket closed"

    # wait if already oversubscribed
    if this_is_loopback:
      nanny.tattle_quantity('looprecv',0)
    else:
      nanny.tattle_quantity('netrecv',0)

    datarecvd = 0
    # loop until we recv the information (looping is needed for Windows)
    while True:
      try:
        # the timeout is needed so that if the socket is closed in another 
        # thread, we notice it
        # BUG: What should the timeout be?   What is the right value?
        comminfo[mycommid]['socket'].settimeout(0.2)
        datarecvd = comminfo[mycommid]['socket'].recv(bytes)
        break
      except socket.error, e:
        # In windows either all or no sockets are blocking...   How odd
        if e[0] == 10035 or e[0] == 11:
          # these codes mean the socket would have needed to block
          continue
        # In Mac-OS-X sometimes we get a "resource temporarily unavailable"
        if e[0] == 35:
          continue
        # the socket operation timed out.   Try again
        if e[0] == "timed out":
          continue
        # The system call was interrupted...
	if e[0] == 4:
          continue
        raise

      # they likely closed the connection
      except KeyError:
        raise Exception, "Socket closed"
        

    # do accounting here...
    if this_is_loopback:
      nanny.tattle_quantity('looprecv',len(datarecvd))
    else:
      nanny.tattle_quantity('netrecv',len(datarecvd))

    return datarecvd



  def send(self,*args):
    # prevent TOCTOU race with client changing the object's properties
    mycommid = self.commid
    restrictions.assertisallowed('socket.send',*args)

    # I factor this out because we must do the accounting at the bottom of this
    # function and I want to make sure we account properly even if they close 
    # the socket right after their data is sent
    try:
      this_is_loopback = is_loopback(comminfo[mycommid]['remotehost'])
    except KeyError:
      raise Exception, "Socket closed!"

    # wait if already oversubscribed
    if this_is_loopback:
      nanny.tattle_quantity('loopsend',0)
    else:
      nanny.tattle_quantity('netsend',0)

    # loop until we send the information (looping is needed for Windows)
    while True:
      try:
        bytessent = comminfo[mycommid]['socket'].send(*args)
        break
      except socket.error, e:
        # In windows either all or no sockets are blocking...   How odd
        if e[0] == 10035 or e[0] == 11:
          # these codes mean the socket would have needed to block
          continue
        # In Mac-OS-X sometimes we get a "resource temporarily unavailable"
        if e[0] == 35:
          continue
        # The system call was interrupted...
	if e[0] == 4:
          continue
        raise
      except KeyError:
        raise Exception, "Socket closed!"


    if this_is_loopback:
      nanny.tattle_quantity('loopsend',bytessent)
    else:
      nanny.tattle_quantity('netsend',bytessent)

    return bytessent



# End of emulated_socket class




