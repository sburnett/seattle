"""
<Program Name>
  stat_library.py

<Started>
  January 31, 2010
  
<Author>
  Jeff Rasley
  jeffra45@gmail.com

<Purpose>
  More information visit, https://seattle.cs.washington.edu/wiki/StatsLibrary
  This library is used for two major purposes.
    1) To collect specific data about Seattle nodes/vessels, with the ability 
       to be run automatically if desired. This specifically relates to the
       'poll_data()' method, read below for more details on that method.
    2) Once you have ran poll_data() at least once you can import this specific
       data structure and manipulate it as you see fit.  There are some specific
       methods in this library that help you collect specific information but
       you are free to do what you please with it after you run 'import_data()'.
"""

import os
import sys
import time
import datetime
import pickle
import gzip

#--*Insert Your Path Here (experimentlib location)*----
PATH_TO_EXP_LIB = '/home/jeffra45/' 
PRODUCTION_KEY_PATH = PATH_TO_EXP_LIB + 'stat_lib/production_keys/'
BETA_KEY_PATH = PATH_TO_EXP_LIB + 'stat_lib/beta_keys/'
#----------*Insert Your Path above*--------------------

sys.path.append(PATH_TO_EXP_LIB + 'experimentlibrary')
import experimentlib




class StatLibraryError(Exception):
  """Base class for other exceptions."""




class NodeLocationListEmptyError(StatLibraryError):
  """
  If the 'nodelocation_list' in poll_data() is empty then we can't run a 
  successful poll on any nodes.
  """



  
class MoreThanOneProdBetaKeyError(StatLibraryError):
  """
  A given node has more than one production or beta keys in its associated 
  vessel userkeys. 
  """




class ProductionAndBetaKeyError(StatLibraryError):
  """
  A given node has both a production and beta key in its associated vessel 
  userkey lists.
  """




def poll_data():
  """
  <Purpose>
    This is used to collect and store node/vessel data.
  <Arguments>
    None.
  <Exceptions>
    NodeLocationListEmptyError
      This error will be raised if we are unable to 
      lookup any node locations because there won't 
      be any nodes to look up any information on.
    ExperimentLibError
      If any experiment library errors occur they will
      be logged in 'fail_list.dat.gz' at the end of poll_data()
  <Side Effects>
    Creates a new folder at the users path (specified above) with a timestamp. 
    Inside that folder will exist 2 gzip files one called 'nodes_list.gz' and 
    one called 'fail_list.gz', these are compressed python pickles of the 
    objects used in this script.
  <Returns>
    None.
  """
  
  poll_identity = experimentlib.create_identity_from_key_files(PATH_TO_EXP_LIB +
                                                               "stat_lib/perc20.publickey")

  # Creates a list of IPs that are associated with this identity.
  nodelocation_list = experimentlib.lookup_node_locations_by_identity(poll_identity)

  # The format of the timestamp is of the form:
  # YYYYMMDD_HHMM, with single digits zero padded (5 -> 05).
  curr_time = datetime.datetime.now()
  
  # Converts datetime object to a formated string.
  folder_name = datetime.datetime.strftime(curr_time, "%Y%m%d_%H%M")
  month_folder = datetime.datetime.strftime(curr_time, "%Y_%m")

  # If a folder does not exist for the month of the poll, it is created.
  if not os.path.isdir(PATH_TO_EXP_LIB + "seattle_node_data/" + month_folder):
    os.mkdir(PATH_TO_EXP_LIB + "seattle_node_data/" + month_folder)
  
  # Create the folder for this poll data to be stored.
  data_storage_path = PATH_TO_EXP_LIB + "seattle_node_data/" + month_folder + "/" + folder_name
  os.mkdir(data_storage_path)
  
  # Checks to make sure we have enough node locations to continue with the
  # poll, if not a NodeLocationListEmpty Error is raised.
  if(len(nodelocation_list) < 0):
    raise NodeLocationListEmptyError("Node location list is empty, " +
                                     "poll_data stopped at: " + str(curr_time))
  
  # Creates initial gzip data files to be saved (appends if needed).
  nodes_file = gzip.open(data_storage_path + "/node_list.dat.gz",'ar')
  fail_file = gzip.open(data_storage_path + "/fail_list.dat.gz",'ar')

  # The initial data structures to be pickled.
  total_node_dicts = {}
  fail_dict = {}
  
  for node_ip in nodelocation_list:
    single_node_dict = {}
    single_node_dict['timestamp'] = curr_time
    
    time_before_browsenode = time.time()
    
    # If browse_node fails it will throw an ExperimentLibError which means we 
    # are not able to communicate with the node so it is added to the list 
    # of failed nodes.
    try:
      list_of_vessel_dicts = experimentlib.browse_node(node_ip)
    except experimentlib.SeattleExperimentError, err:
      time_atfail_browsenode = time.time()
      elapsed_time_fail = time_atfail_browsenode - time_before_browsenode
      fail_dict[str(node_ip)] = [err, elapsed_time_fail]
      time_before_browsenode = 0
      time_after_browsenode = 0
      continue
   
    time_after_browsenode = time.time()
    elapsed_time = time_after_browsenode - time_before_browsenode
    
    single_node_dict['responsetime'] = elapsed_time
    single_node_dict['nodelocation'] = node_ip
    single_node_dict['version'] = list_of_vessel_dicts[0].get('version')
    unique_id = list_of_vessel_dicts[0].get('nodeid')
    single_node_dict['nodeid'] = unique_id
    single_node_dict['vessels'] = list_of_vessel_dicts
    total_node_dicts[str(unique_id)] = single_node_dict
    
  # Finally stores the data structures in two separate gzip pickles.
  pickle.dump(total_node_dicts, nodes_file)
  pickle.dump(fail_dict, fail_file)
  
  # Close files.
  nodes_file.close()
  fail_file.close()




def import_data(absolute_path_to_file):
  """
  <Purpose>
    To import a specific data file (in pickle format) 
    that you would like to analyze.
  <Argument>
    absolute_path_to_file
      The absolute path to the data file that 
      you want to import.
  <Exceptions>
    Will raise an IOError if the file you
    are looking for does not exist.
  <Side Effects>
    None.
  <Returns>
    Returns an object of either the nodes dictionary 
    or a list of failed node ips, depending on which gzip
    file you import.
  """

  file_pickle = gzip.open(absolute_path_to_file,'r')
  node_dict = pickle.load(file_pickle)
  file_pickle.close()

  return node_dict




def get_versions(node_dicts):
  """
  <Purpose>
    To filter a list of nodes into separate versions
  <Argument>
    node_dicts
      A dictionary {nodeid:node_dict} of node dictionaries
  <Exceptions>
    None.
  <Side Effects>
    None.
  <Return>
    Returns a dictionary with its keys as versions and its
    contents as a list of nodes with that specific version
  """
  
  version_split = {}
  for nodeid, node in node_dicts.items():
    node_ver = node.get('version')
    if(version_split.has_key(node_ver)):
      version_split.get(node_ver).append(node)
    else:
      version_split[node_ver] = [node]
  return version_split




def get_all_vessels(node_dicts):
  """
  <Purpose>
    To strip off all node information and just deal with the 
    total amount of vessels.
  <Argument>
    node_dicts
      A dictionary {nodeid:node_dict} of node dictionaries
  <Exceptions>
    None.
  <Side Effects>
    None.
  <Return>
    Returns a list of all the vessel dictionaries associated to the 
    dictionary of node dictionaries passed in.
  """
  
  total_vessels = []
  for nodeid, node in node_dicts.items():
    for single_vessel in node.get('vessels'):
      total_vessels.append(single_vessel)
  return total_vessels
  



def production_beta_key_split(node_dicts):
  """
  <Purpose>
    To split nodes into 3 different categories: production,
    beta or other nodes.
  <Argument>
    node_dicts
      A dictionary {nodeid:node_dict} of node dictionaries
  <Exceptions>
    ProductionAndBetaKeyError
      If a production and beta key are found on the same node
      this error will be raised.
  <Side Effects>
    None.
  <Return>
    Returns a dictionary with 3 keys: production, beta
    and other nodes; in the form of {'production':node_dicts}.
    Where each node_dict now has a new key of production, 
    beta or other and its contents being the name of the key.
  """

  prod_keys_dict = _production_keys()
  beta_keys_dict = _beta_keys()
  
  production_node_dicts = {}
  beta_node_dicts = {}
  other_node_dicts = {}
  
  multi_match = {}
  return_dict = {}
  
  for nodeid, single_node_dict in node_dicts.items():
    # Checks to see if the given node is a production or beta node.
    node_is_production = _key_check(single_node_dict['vessels'], prod_keys_dict)
    node_is_beta = _key_check(single_node_dict['vessels'], beta_keys_dict)
    
    # If the type returned by _key_check() is a tuple, there was at
    # least one node that had duplicate keys.
    if node_is_production is not None  and node_is_beta is not None:
      raise ProductionAndBetaKeyError("Node with nodelocation of " +
                                     str(single_node_dict['nodelocation']) +
                                     " has a beta [" + str(node_is_beta) +
                                     "] AND production [" + str(node_is_production) +
                                     "] key, this should never happen.")
    elif (type(node_is_production) is tuple) or (type(node_is_beta) is tuple):
      multi_match['vessels'] = single_node_dict
      multi_match['prod_key'] = node_is_production
      multi_match['beta_key'] = node_is_beta
    elif node_is_production is not None:
      # Where node_is_production is the name of the key found.
      single_node_dict['production'] = node_is_production
      production_node_dicts[str(nodeid)] = single_node_dict
    elif node_is_beta is not None:
      single_node_dict['beta'] = node_is_beta
      beta_node_dicts[str(nodeid)] = single_node_dict      
    else:
      # This shouldn't happen, but if it gets here the node is
      # neither production or beta.
      single_node_dict['unknown'] = "unknown"
      other_node_dicts[str(nodeid)] = single_node_dict
  
  production_beta_key_dicts = {'production':production_node_dicts,
                               'beta':beta_node_dicts,
                               'other':other_node_dicts}
  
  return_dict['production_beta_key_dicts'] = production_beta_key_dicts
  return_dict['nodes_with_multi_keys'] = multi_match
  return return_dict




def split_lan_nodes(node_dicts):
  """
  <Purpose>
    Takes a dictionary of node_dicts and splits them based on their ip 
    addresses (adding NAT nodes in one special category).  If 'node a' and 
    'node b' are both part of the '10.8.10.X' network they will be grouped 
    together so you can tell how many nodes are part of the same local network.
    In this implementation it is possible for a LAN to only have one node. 
  <Argument>
    node_dicts
      A dictionary {nodeid:node_dict} of node dictionaries.
  <Exceptions>
    None.
  <Side Effects>
    None.
  <Return>
    Returns a dictionary of the form {'10.8.10.X':[node_dicts]}, where
    '[node_dicts]' is a list of node_dicts that are in the 10.8.10.X LAN.
  """
  
  # Dictionary of LANs that will be returned.
  lans = {}
  
  for nodeid, single_node_dict in node_dicts.items():
    ip_port = single_node_dict['nodelocation']
    
    # Checks to see if the IP is a NAT node, if so it puts it into a 
    # separate category.
    if ip_port.startswith('NAT'):
      if lans.has_key('NAT'):
        lans['NAT'].append(single_node_dict)
      else:
        lans['NAT'] = [single_node_dict]
    else:
      # Original string is in the form of "10.8.10.6:123" and it is then split
      # into the form of ["10.8.10", .6:123"], thus striping of the last octet
      # and port information.
      lan_key = ip_port.rsplit('.', 1)[0] + ".X"
      
      if lans.has_key(lan_key):
        lans[lan_key].append(single_node_dict)
      else:
        lans[lan_key] = [single_node_dict]
        
  return lans




def _key_check(vessels_list, key_name_dict):
  """
  <Purpose>
    This is a helper method for 'production_beta_key_split',
    it checks to see if a given dictionary of keys
  <Arguments>
    vessels_list
      A list of vessel dictionaries associated with a given node.
    key_name_dict
      A dictionary of production or beta keys in the form
      of {'key_name':publickey_dict}.
  <Exceptions>
    If a the list of vessels passed in contain more than one key match 
    a 'MoreThanOneProdBetaKeyError' will be raised, since this should 
    never happen when dealing with production and beta transition keys.
  <Side Effects>
    None.
  <Return>
    Either a key name as a string or 'None' if no match was found.
  """
  
  found_match = None
  
  for single_vessel in vessels_list:
    for key_name, pubkey_dict in key_name_dict.items():
      for userkey in single_vessel['userkeys']:
        if userkey == pubkey_dict:  
          # If a duplicate key is found an error should be raised, for now we
          # will catch this error until ticket #853 is resolved.
          try:
            if found_match is not None:
              raise MoreThanOneProdBetaKeyError("Found multiple key matches: " +
                                                str(found_match) + " and " +
                                                str(key_name) + " Should not happen " +
                                                str(single_vessel['nodelocation']))
            else:
              found_match = key_name
          except MoreThanOneProdBetaKeyError, err:
            found_match = (key_name, 2)

  return found_match




def _production_keys():
  """
  <Purpose>
    To generate a dictionary of production keys for 
    checking to see if a node is a production node or
    a beta node based off of what user keys its vessels
    have.
  <Argument>
    None.
  <Exceptions>
    Possible IO errors if keys have not been downloaded
    to their correct locations.
  <Side Effects>
    None.
  <Return>
    Returns a dictionary of production keys in the form
    of {'key_name':publickey_dict}.
  """

  prod_keys_dict = {}

  prod_key_names = ['acceptdonation', 'canonical', 'movingtogenilookup',
                    'movingtoonepercent2', 'movingtoonepercent',
                    'movingtoonepercent_manyevents', 'onepercent2',
                    'onepercent', 'onepercentmanyevents']

  for name in prod_key_names:
    prod_keys_dict[name] = experimentlib.create_identity_from_key_files(PRODUCTION_KEY_PATH + name +
                                                                        '.publickey').get('publickey_dict')
  
  return prod_keys_dict




def _beta_keys():
  """
  <Purpose>
    To generate a dictionary of beta keys for 
    checking to see if a node is a production node or
    a beta node based off of what user keys its vessels
    have.
  <Argument>
    None.
  <Exceptions>
    Possible IO errors if keys have not been downloaded
    to their correct locations.
  <Side Effects>
    None.
  <Return>
    Returns a dictionary of beta keys in the form
    of {'key_name':publickey_dict}.
  """

  beta_keys_dict = {}
  
  beta_key_names = ['acceptdonation', 'canonical', 'movingtoonepercent_manyevents',
                    'onepercentmanyevents']

  for name in beta_key_names:
    beta_keys_dict[name] = experimentlib.create_identity_from_key_files(BETA_KEY_PATH + name + 
                                                                        '.publickey').get('publickey_dict')
  
  return beta_keys_dict
