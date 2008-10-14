""" 
Author: Justin Cappos

Start Date: July 8, 2008

Description:
Advertises availability to openDHT...

This code is partially adapted from the example openDHT code.

"""

import socket
import threading
import random
import urllib

import sha
try:
  import xmlrpclib
except ImportError:
  # Python 3.0 portability fix...
  import xmlrpc.client as xmlrpclib



proxylist = []
currentproxy = None

def announce(key, value, ttlval):
  global proxylist
  global currentproxy

  # convert ttl to an int
  ttl = int(ttlval)

#  print "Announce key:",key,"value:",value, "ttl:",ttl
  while True:
    # if we have an empty proxy list and no proxy, get more
    if currentproxy == None and proxylist == []:
      proxylist = get_proxy_list()
      # we couldn't get any proxies
      if proxylist == []:
        return False


    # if there isn't a proxy we should use, get one from our list
    if currentproxy == None and proxylist != []:
      currentproxy = proxylist[0]
      del proxylist[0]


    # This code block is adopted from put.py from OpenDHT
    pxy = xmlrpclib.ServerProxy(currentproxy)
    keytosend = xmlrpclib.Binary(sha.new(str(key)).digest())
    valtosend = xmlrpclib.Binary(value)

    try:
      # In the current version of xmlrpclib, an obsolescence warning will be 
      # printed here.   This is problem with the standard lib, not this code...
      pxy.put(keytosend, valtosend, ttl, "put.py")
      # if there isn't an exception, we succeeded
      break
    except (socket.error, socket.gaierror):
      # Let's avoid this proxy.   It seems broken
      currentproxy = None

  return True
      



def lookup(key, maxvals=100):
  global proxylist
  global currentproxy

  while True:
    # if we have an empty proxy list and no proxy, get more
    if currentproxy == None and proxylist == []:
      proxylist = get_proxy_list()
      # we couldn't get any proxies
      if proxylist == []:
        raise Exception, "Lookup failed"


    # if there isn't a proxy we should use, get one from our list
    if currentproxy == None and proxylist != []:
      currentproxy = proxylist[0]
      del proxylist[0]


    # This code block is adopted from get.py from OpenDHT
    pxy = xmlrpclib.ServerProxy(currentproxy)
    maxvalhash = int(maxvals)  
    # I don't know what pm is for but I assume it's some sort of generator / 
    # running counter
    pm = xmlrpclib.Binary("")
    keyhash = xmlrpclib.Binary(sha.new(str(key)).digest())


    listofitems = []
    while True:
      try:
        # In the current version of xmlrpclib, an obsolescence warning will be 
        # printed here.   This is problem with the standard lib, not this code...
        vals, pm = pxy.get(keyhash, maxvalhash, pm, "get.py")
        # if there isn't an exception, we succeeded

        # append the .data part of the items, the other bits are:
        # the ttl and hash / hash algorithm.
        for item in vals:
          listofitems.append(item.data)
    
        # reached the last item.  We're done!
        if pm.data == "":
          return listofitems

      except (socket.error, socket.gaierror):
        # Let's avoid this proxy.   It seems broken
        currentproxy = None

      


serverlist = []

# check to see if a server is up and ready for OpenDHT...
class ServerTest(threading.Thread):
  def __init__(self, servername):
    threading.Thread.__init__(self)
    self.servername = servername

  def run(self):
    global serverlist
    try: 
      ip = socket.gethostbyname(self.servername)
      # try three times.   Why three?   Arbitrary value
      for junkcount in range(3):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2.0)
        s.connect((ip, 5851))
        s.close()

      # this list is the "return value".   Add ourselves if no problems...
      serverlist.append(ip)
    except:
      pass


# Loosely based on find-gateway.py from the OpenDHT project...
def get_proxy_list(numberofattempts=30):
  global serverlist
  
  # populate server list
  urlfo = urllib.urlopen('http://opendht.org/servers.txt')
  # throw away the header line
  urlfo.readline()
  # get the server list
  servers = []
  for line in urlfo:
    # The lines look like:
    # 4:	134.121.64.7:5850	planetlab2.eecs.wsu.edu
    # The third field is the server name
    servers.append(line.split()[2])

  if len(servers)< numberofattempts:
    raise Exception, "Insufficient servers in server list"

  serverstocheck = random.sample(servers, numberofattempts)

  serverthreads = []
  for server in serverstocheck:
    serverthreads.append(ServerTest(server))


  # empty the server list
  serverlist = []

  # start checking...
  for thread in serverthreads:
    thread.start()

  # wait until all are finished
  for thread in serverthreads:
    thread.join()


  retlist = []
  for serverip in serverlist:
    # make it look like the right sort of url...
    retlist.append("http://"+serverip+":5851/")


  return retlist
