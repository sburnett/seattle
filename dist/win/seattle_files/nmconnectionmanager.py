""" 
Author: Justin Cappos

Module: Node Manager connection handling.   This does everything up to handling
        a request (i.e. accept connections, handle the order they should be
        processed in, etc.)   Requests will be handled one at a time.

Start date: August 28th, 2008

This is the node manager for Seattle.   It ensures that sandboxes are correctly
assigned to users and users can manipulate those sandboxes safely.   

The design goals of this version are to be secure, simple, and reliable (in 
that order).   

The basic design of the node manager is that the "accept thread" (implemented
using waitforconn) accepts 
connections and checks basic things about them such as there aren't too many 
connections from a single source.   This thread places valid connections into
an ordered list.   This thread handles meta information like sceduling requests
and preventing DOS attacks that target admission.

Another thread (the worker thread) processes the first element in the list.  
The worker thread is responsible for handling an individual request.   This
ensures that the request is validly signed, prevents slow connections from 
clogging the request stream, etc.


Right now I ensure that only one worker thread is active at a time.   In the 
future, it would be possible to have multiple threads that are performing 
disjoint operations to proceed in parallel.   This may allow starvation attacks
if it involves reordering the list of connections.   As a result, it is punted 
to future work.

I'm going to use "polling" by the worker thread.   I'll sleep when the 
list is empty and periodically look to see if a new element was added.
"""

# needed to have separate threads for accept / the worker
import threading

# need to get connections, etc.
import socket

# needed for sleep
import time

# does the actual request handling
import nmrequesthandler

# the global list of connections waiting to be serviced
# each item is a tuple of (socketobj, IP)
connection_list = []

portused = None









# Accept thread
# some of this code is adapted from emulcomm, so if a bug exists here, check 
# there as well...
class AcceptThread(threading.Thread):
  listeningsocket = None
  
  def __init__(self, myip, possiblelistenports):
    global portused
    # get the socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # reuse the socket if it's "pseudo-availible"  
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # try the ports in the list...
    for listenport in possiblelistenports:
   
      try:
        # bind it to the port
        s.bind((myip, listenport))
      except socket.error:
        continue

      portused = listenport
      break

    else:
      # This only happens when we can't use any port.   The main thread will 
      # restart us and hopefully we will have a free port by then.
      raise socket.error, "Cannot find a port to use"

    # listen for connections (allow 5 pending)
    # BUG: is it okay to leave this small since I'm going to be doing accept in
    # a small loop?   The concern is that someone could flood me with
    # connection requests and block legitimate users.
    s.listen(5)

    self.listeningsocket = s
    threading.Thread.__init__(self, name="AcceptThread")

  def run(self):
    while True:
      # get the connection.   I'm not catching errors because I believe they
      # should not occur
      connection,addr = self.listeningsocket.accept()

      # okay, I have the connection.   I want to insert it if there aren't 3
      # already from this IP.
      # I might have a race here where while I check a connection is removed.
      # it's benign and only prevents me from handling a connection from a
      # client with many connections

      # first count the connections in the connection_list
      connectioncount = 0
      for junksocket, IP in connection_list[:]:
        # I don't care about the port, only the IP.
        if IP == addr[0]:
          connectioncount = connectioncount + 1

      # Now add the connections that have been removed by the worker
      # I use a try, except block here to prevent a race condition on checking
      # the key is in the dict and looking at the list (i.e. the worker might 
      # delete the list in the meantime)
      try:
        # the IP is the only thing we care about
        connectioncount = connectioncount + len(connection_dict[addr[0]])

      except KeyError:
        # this means there are no connections from this IP.   That's fine.
        pass

      if connectioncount > 3:
        # we're rejecting to prevent DOS by grabbing lots of connections
        connection.close()
        continue

      # All is well!   add the socket and IP to the list
      connection_list.append((connection,addr[0]))
      


##### ORDER IN WHICH CONNECTIONS ARE HANDLED

# Each connection should be handled after all other IP addresses with this
# number of connections.   So if the order of requests is IP1, IP1, IP2 then 
# the ordering should be IP1, IP2, IP1.   
# For example, if there are IP1, IP2, IP3, IP1, IP3, IP3 then IP4 should be
# handled after the first IP3.   If IP2 adds a request, it should go in the 
# third to last position.   IP3 cannot currently queue another request since 
# it has 3 pending.



# This is a list that has the order connections should be handled in.   This
# list contains IP addresses (corresponding to the keys in the connection_dict)
connection_dict_order = []

# this is dictionary that contains a list per IP.   Each key in the dict 
# maps to a list of connections that are pending for that IP.
connection_dict = {}


# I look at the connection_list and add the new items to the connection_dict
# and connection_dict_order
def add_requests():
  while len(connection_list) > 0:
    # items are added to the back (and removed from the front)
    thisconn, thisIP = connection_list[0]

    # it's not in the list, let's initialize!
    if thisIP not in connection_dict_order:
      connection_dict_order.append(thisIP)
      connection_dict[thisIP] = []

    # we should add this connection to the list
    connection_dict[thisIP].append(thisconn)
    
    # I've finished processing and can safely remove the item.  If I removed it 
    # earlier, they might be able to get more than 3 connections because they
    # might not have seen it in the connection_list or the connection_dict)
    del connection_list[0]
  

# get the first request
def pop_request():
  if len(connection_dict)==0:
    raise ValueError, "Internal Error: Popping a request for an empty connection_dict"

  # get the first item of the connection_dict_order... 
  nextIP = connection_dict_order[0]
  del connection_dict_order[0]

  # ...and the first item of this list
  therequest = connection_dict[nextIP][0]
  del connection_dict[nextIP][0]

  # if this is the last connection from this IP, let's remove the empty list 
  # from the dictionary
  if len(connection_dict[nextIP]) == 0:
    del connection_dict[nextIP]
  else:
    # there are more.   Let's append the IP to the end of the dict_order
    connection_dict_order.append(nextIP)

  # and return the request we removed.
  return therequest
  


# this class is the worker thread.   It pulls connections off of the 
# connection_list and categorizes them.   
class WorkerThread(threading.Thread):
  sleeptime = None
  def __init__(self,st):
    self.sleeptime = st
    threading.Thread.__init__(self, name="WorkerThread")

  def run(self):

    while True:
      # if there are any requests, add them to the dict.
      add_requests()
      
      if len(connection_dict)>0:
        # get the "first" request
        conn = pop_request()
        nmrequesthandler.handle_request(conn)
      else:
        # check at most twice a second (if nothing is new)
        time.sleep(self.sleeptime)
 

