"""
<Program Name>
  geni_xmlrpc_server.py

<Started>
  6/3/2009

<Author>
  Jason Chen
  jchen@cs.washington.edu

<Purpose>
  XML-RPC Server for "core" functions that provide GENI functionality.
"""

import sys
import traceback

from django.db import connection
from django.db import transaction
from django.contrib.auth import authenticate

from geni.control.models import User, VesselPort, VesselMap
import geni.control.repy_dist.vessel_operations
import geni_xmlrpc_faults

import SocketServer
import SimpleXMLRPCServer

# A threaded XMLRPC server class
#class ThreadedXMLRPCServer(SocketServer.ThreadingMixIn, SimpleXMLRPCServer.SimpleXMLRPCServer):

LISTENPORT = 9001

def xmlrpc_acquire_resources(auth, rspec):
  """
  <Purpose>
    Acquires resources, designed for XML-RPC clients.
    Calls from the web should be to web_acquire_resources() in 
    resource_operations.py instead.
    
  <Arguments>
    auth:
      Authentication structure containing auth info.
    rspec:
      A dictionary of resource specifications: 
      {'rspec_type':rspec_type, 'number_of_nodes':number_of_nodes}
    
      rspec_type can be 'lan', 'wan', or 'random'
      number_of_nodes must be a non-negative integer value.
    
  <Exceptions>
    Raises an XMLRPC Fault, Code 1, with the faultString containing "TypeError"
      if the given values are of incorrect type.
    Raises an XMLRPC Fault, Code 1, with the faultString containing "ValueError"
      if rspec is not of an understood type.

    Raises an XMLRPC Fault, Code 102, a "GENI_NotEnoughCredits"
      if the user doesn't have enough credits to acquire num vessels.
    Raises an XMLRPC Fault, Code 103, a "GENI_NoAvailNodes" 
      if there are no available nodes to acquire.
    Raises an XMLRPC Fault, Code 100, a "GENI_OpError"
      if the operation fails due to some GENI internal error.
  
  <Side Effects>
    Modifies the geni database, reflecting updated acquired vessel counts.

  <Returns>
  A list of dictionaries, where the dicts are of the form:
    {'node_ip':ip, 'node_port':port, 'vessel_id':vessel_id, 
    'node_id':node_id, 'handle':handle}
  
  See the XML-RPC API for more details.
  """
  env_type_func_map = {"lan" : geni.control.repy_dist.vessel_operations.acquire_lan_vessels,
                       "wan" : geni.control.repy_dist.vessel_operations.acquire_wan_vessels,
                       "random" : geni.control.repy_dist.vessel_operations.acquire_rand_vessels}
                       
  connection.cursor().execute('set transaction isolation level read committed')

  # are types correct?
  resource_type = rspec['rspec_type']
  resource_num = rspec['number_of_nodes']
  if not isinstance(resource_type, str) or not isinstance(resource_num, int):
    raise TypeError("Invalid data types in rspec. Please check your rspec.")
  
  # are values valid?
  if (resource_type != "lan" and resource_type != "wan" and \
    resource_type != "random") or resource_num < 1:
    raise ValueError("Invalid values in rspec. Please check your rspec.")
  
  geni_user = __auth__(auth)
  
  __charge_user__(geni_user, resource_num)
  credit_limit = geni_user.only_vessel_credit_limit()
  
  if geni_user.num_acquired_vessels > credit_limit:
    # user wants too much
    __charge_user__(geni_user, (-1 * resource_num))
    raise geni_xmlrpc_faults.GENI_NotEnoughCredits
    
  if resource_num == 1:
    # acquiring 1 node is equivalent to using a random node type
    acquire_func = env_type_func_map['random']
  else:
    acquire_func = env_type_func_map[resource_type]
    
  try:
    # attempt to acquire resources
    success, ret = acquire_func(geni_user, resource_num)
    
  except:
    # internal operation failed
    summary = "xmlrpc_acquire_resources: Failed to acquire vessel(s). Internal Error."
    summary += ''.join(traceback.format_exception(sys.exc_info()[0],sys.exc_info()[1],sys.exc_info()[2]))
    print '-'*60
    print summary
    print '-'*60
    raise geni_xmlrpc_faults.GENI_OpError(summary)
  else:
    if not success:
    # no more nodes available
      __charge_user__(geni_user, (-1 * resource_num))
      raise geni_xmlrpc_faults.GENI_NoAvailNodes
    
    # acquired vessels, deserialize return info
    summary, explanation, acquired = ret
    # construct list of dicts for return
    acquired_dictlist = __construct_info_dictlist__(acquired)
    return acquired_dictlist



@transaction.commit_manually
def __charge_user__(geni_user, num):
  # charge the user for requested resources
  geni_user.num_acquired_vessels += num
  geni_user.save()
  transaction.commit()



def xmlrpc_release_resources(auth, list_of_handles):
  """
  <Purpose>
    Releases resources, designed for XML-RPC clients.
    Calls from the web should be to web_release_resources() in 
    resource_operations.py instead.
    
  <Arguments>
    auth:
      Authentication structure containing auth info.
    list_of_handles:
      A list of handles that were returned by acquire_resources.
      
  <Exceptions>
    Raises an XMLRPC Fault, Code 1, with the faultString containing "TypeError"
      if the given values are of incorrect type or invalid.
    Raises an XMLRPC Fault, Code 100, a "GENI_OpError",
      if the operation fails due to some GENI internal error.
    
  <Side Effects>
    Releases given vessels.

  <Returns>
    None. If no exception is thrown, then the operation succeded.
    
    See the XML-RPC API for more details.
  """
  
  geni_user = __auth__(auth)
  
  # is list_of_handles valid?
  for handle in list_of_handles:
    # split handle into [0]: pubkey, [1]: vesselname
    handle_parts = handle.split(':')
    # TODO: rigorously check handle info
  
  # get all vessels, then release if vessel is in list_of_handles
  vessels_to_release = []
  my_vessels = []
  my_vmaps = VesselMap.objects.all()
  #my_vmaps = VesselMap.objects.filter(user=geni_user)
  for vmap in my_vmaps:
    my_vessels.append(vmap.vessel_port.vessel)
    
  for vessel in my_vessels:
    v_vesselid = vessel.name
    v_nodeid = vessel.donation.pubkey
    v_handle = v_nodeid + ":" + v_vesselid
    if v_handle in list_of_handles:
      vessels_to_release.append(vessel)
  
  resultdict = geni.control.repy_dist.vessel_operations.release_vessels(vessels_to_release)
  
  # cycle through release results, and make sure releasing succeeded
  for vessel, (success, msg) in resultdict.iteritems():
    if not success:
      # release_resource failed for some vessel... should we worry?
      continue
    else:
      # update user's acquired vessels count
      __charge_user__(geni_user, -1)



def xmlrpc_get_resource_info(auth):
  """
  <Purpose>
    Gets resources associated with geni_user, designed for XML-RPC clients.

  <Arguments>
    auth:
      Authentication structure containing auth info.
      
  <Exceptions>
    None?
    
  <Side Effects>
    None.

  <Returns>
    None. If no exception is thrown, then the operation succeded.
    
    See the XML-RPC API for more details.
  """
  
  geni_user = __auth__(auth)
  
  my_vessels = []
  my_vmaps = VesselMap.objects.filter(user=geni_user).order_by('expiration')
  for vmap in my_vmaps:
    my_vessels.append(vmap.vessel_port.vessel)
    
  return __construct_info_dictlist__(my_vessels)



def xmlrpc_get_account_info(auth):
  """
  <Purpose>
    Gets geni_user's account info, designed for XML-RPC clients.

  <Arguments>
    auth:
      Authentication structure containing auth info.
      
  <Exceptions>
    None?
    
  <Side Effects>
    None.

  <Returns>
    None. If no exception is thrown, then the operation succeded.
    
    See the XML-RPC API for more details.
  """
  
  geni_user = __auth__(auth)
  
  user_port = geni_user.port
  user_name = geni_user.www_user.username
  urlinstaller = ""
  private_key_exists = True
  if geni_user.privkey == "":
    private_key_exists = False
  max_vessel = geni_user.vessel_credit_limit()
  user_affiliation = geni_user.affiliation
  
  infodict = {'user_port':user_port, 'user_name':user_name,
        'urlinstaller':urlinstaller, 
        'private_key_exists':private_key_exists,
        'max_vessel':max_vessel,
        'user_affiliation':user_affiliation}
  return infodict



def xmlrpc_get_public_key(auth):
  # Gets geni_user's public key.
  
  geni_user = __auth__(auth)
  return geni_user.pubkey



def xmlrpc_get_private_key(auth):
  # Gets geni_user's private key.
  
  geni_user = __auth__(auth)
  return geni_user.privkey



def xmlrpc_delete_private_key(auth):
  # Deletes the user's private key.
  
  geni_user = __auth__(auth)
  privkey = geni_user.privkey
  if not privkey:
    raise geni_xmlrpc_faults.GENI_KeyAlreadyRemoved
  else:
    geni_user.privkey = ""



def xmlrpc_authcheck(auth_info):
  user = authenticate(username=auth_info['username'], password=auth_info['authstring'])
  if user:
    return 0
  else:
    return -1



def __auth__(auth_info):
  user = authenticate(username=auth_info['username'], password=auth_info['authstring'])
  if user:
    getuser_success, getuser_geni_user = User.get_guser_by_username(auth_info['username'])
    if getuser_success:
      return getuser_geni_user
    else:
      raise geni_xmlrpc_faults.GENI_OpError(
      "__auth__: Internal call to get_guser_by_username failed.")
  else:
    raise geni_xmlrpc_faults.GENI_AuthError
    
    

def __temp_auth__(geni_user):
  # temp auth to geni_user
  if(geni_user == 'testacct' or geni_user == 'testacct2' or geni_user == 'testacct3' or geni_user == 'testacct4' or geni_user == 'jchen'):
    getuser_success, getuser_geni_user = User.get_guser_by_username(geni_user)
    if getuser_success:
      geni_user = getuser_geni_user
      return geni_user
    else:
      exc_msg = "Failed to get geni_user (internal, User.get_user failed)"
      print "*** ERROR: " + exc_msg
      raise geni_xmlrpc_faults.GENI_OpError(exc_msg)
  else:
    exc_msg = "Tried to auth as unauthorized user."
    print "*** ERROR: " + exc_msg
    raise geni_xmlrpc_faults.GENI_OpError(exc_msg)



# Private function, used to construct a list of dictionaries full of vessel
# info when given a list of vessels.
def __construct_info_dictlist__(vessellist):
  info_dictlist = []
  for vessel in vessellist:
    v_ip = vessel.donation.ip
    v_port = vessel.donation.port
    v_vesselid = vessel.name  #eg 'v22'
    v_nodeid = vessel.donation.pubkey
    v_handle = v_nodeid + ":" + v_vesselid
    
    temp_dict = {'node_ip':v_ip, 'node_port':v_port,
           'vessel_id':v_vesselid, 'node_id':v_nodeid,
           'handle':v_handle}
    # add this info to the info dictionary list
    info_dictlist.append(temp_dict)
  return info_dictlist



def main():
  #server = ThreadedXMLRPCServer(("127.0.0.1", LISTENPORT), allow_none=True)
  #server = SimpleXMLRPCServer.SimpleXMLRPCServer(("128.208.4.40", LISTENPORT), allow_none=True)
  server = SimpleXMLRPCServer.SimpleXMLRPCServer(("127.0.0.1", LISTENPORT), allow_none=True)
  print "GENI XMLRPC Server up, listening on port "+str(LISTENPORT)+"..."

  #server.register_multicall_functions()
  server.register_function(xmlrpc_acquire_resources, 'acquire_resources')
  server.register_function(xmlrpc_release_resources, 'release_resources')
  server.register_function(xmlrpc_get_resource_info, 'get_resource_info')
  server.register_function(xmlrpc_get_account_info, 'get_account_info')
  server.register_function(xmlrpc_get_public_key, 'get_public_key')
  server.register_function(xmlrpc_get_private_key, 'get_private_key')
  server.register_function(xmlrpc_delete_private_key, 'delete_private_key')
  server.register_function(xmlrpc_authcheck, 'authcheck')
  
  server.serve_forever()

# make main() runnable from the console
if __name__=="__main__":
  main()
