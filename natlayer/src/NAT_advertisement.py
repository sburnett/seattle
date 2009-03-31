"""
Author: Armon Dadgar, Eric Kimbrel

Start date: March 27, 2009

Description: Abstracts the task of looking up and advertising servers and forwarders.

"""

include centralizedadvertise.repy
include deserialize.py

# What should we register as?
NAT_FORWARDER_ADVERTISE_KEY = "__NAT__FORWARDER__"
NAT_SRV_PREFIX = "__NAT_SRV__"

# Limit of forwarder lookups
NAT_MAX_LOOKUP = 50

NAT_ADVERTISE_INTERVAL = 30
NAT_ADVERTISE_TTL = 3*NAT_ADVERTISE_INTERVAL

# Pools the advertisements, so that they can be done in one thread
# Maps key-> value
NAT_ADVERTISE_POOL = {}

# Enable allows toggling of periodic advertisement
# Run controls the advertisement thread, False will stop the thread
NAT_ADVERTISE_STATE = {"enable":False,"run":False}

# Registers the forwarder so that clients using the NATLayer can find us
def nat_forwarder_advertise(ip, serverport, clientport):
  # Generate the value to advertise
  value = ip+"*"+str(serverport)+"*"+str(clientport)
  
  # Add to the advertising pool
  NAT_ADVERTISE_POOL[NAT_FORWARDER_ADVERTISE_KEY] = value


# Advertises a server, so that other NATLayer users can connect
def nat_server_advertise(key, forwarderIP, forwarderCltPort):
  # Generate the value to advertise
  value = forwarderIP+'*'+str(forwarderCltPort)

  # Alter the key, add the prefix
  key = NAT_SRV_PREFIX + key

  # Add to the advertising pool
  NAT_ADVERTISE_POOL[key] = value

# Stops advertising a server key    
def nat_stop_server_advertise(key):
  # Alter the key, add the prefix
  key = NAT_SRV_PREFIX + key
  
  if key in NAT_ADVERTISE_POOL:
    del NAT_ADVERTISE_POOL[key]
    
# Lookup a forwarder so that we can connect
def nat_forwarder_lookup():
  # Get the list of forwarders
  forwarders = centralizedadvertise_lookup(NAT_FORWARDER_ADVERTISE_KEY, NAT_MAX_LOOKUP)

  # Safety check..
  if len(forwarders) <= 1 and forwarders[0] == '':
    raise Exception, "No forwarders could be found!"
  
  # Grab a random forwarder
  index = int(randomfloat() * (len(forwarders)-1))

  # Get the info
  forwarderInfo = forwarders[index]
  
  try:
    (ip,server_port,client_port) = forwarderInfo.split('*')
  except ValueError:
    raise Exception, 'Forwarder lookup returned unexpected value'
  

  # Return a tuple containing the IP and port for server and client
  return (ip,int(server_port),int(client_port))


# Finds a server using the NATLayer
def nat_server_lookup(key):
  # Get the proper key, add the prefix
  key = NAT_SRV_PREFIX + key

  # Fetch all the keys
  lst = centralizedadvertise_lookup(key, NAT_MAX_LOOKUP)
  num = len(lst)
  
  # Safety check...
  assert(num <= 1)
  if num == 0 or (num == 1 and lst[0] == ''):
    raise Exception, "Host could not be found!"

  # Get the information about the server
  info = lst[0]

  try:
    (forwarder_ip,clt_port) = info.split('*')
  except ValueError:
    raise 'Unexpected value recieved from server lookup'

  # Return a tuple of the forwarder IP port
  return (forwarder_ip, int(clt_port))


# Toggles advertisement
# Enable: allows or disallows advertisement of the pool
# threadRun: allows/starts or stops the advertisement thread
def nat_toggle_advertisement(enabled, threadRun=True): 
  NAT_ADVERTISE_STATE["enable"] = enabled
  
  # Start the advertisement thread if necessary
  if not NAT_ADVERTISE_STATE["run"] and threadRun:
    settimer(.1, _nat_advertise_thread, ())
  
  NAT_ADVERTISE_STATE["run"] = threadRun

  
# Launch this thread with settimer to handle the advertisement  
def _nat_advertise_thread():
  while True:
    # Check if advertising is enabled:
    if NAT_ADVERTISE_STATE["enable"]:
      # Advertise everything in the pool
      for (key, val) in NAT_ADVERTISE_POOL.items():
        try:
          centralizedadvertise_announce(key, val, NAT_ADVERTISE_TTL)
        except:
          pass
    
    # Sleep for a while
    sleep(NAT_ADVERTISE_INTERVAL)
              
    # Check if we should terminate
    if not NAT_ADVERTISE_STATE["run"]:
      break

