"""
<Program Name>
  deploy_stats.py

<Started>
  July 2009

<Author>
  n2k8000@u.washington.edu
  Konstantin Pik

<Purpose>
  This file contains methods to be used for creating summaries.

<Usage>
  See deploy_main.py.
  
"""
import deploy_main
import deploy_html


import repyhelper

# make sure we have access to the rsa lib in the local namespace
repyhelper.translate_and_import('rsa.repy')

canonicalpublickey = rsa_file_to_publickey("canonical.publickey")
# The key used for new donations...
acceptdonationpublickey = rsa_file_to_publickey("acceptdonation.publickey")

# Used for our first attempt at doing something sensible...
movingtoonepercentpublickey = rsa_file_to_publickey("movingtoonepercent.publickey")
onepercentpublickey = rsa_file_to_publickey("onepercent.publickey")

# Used as the second onepercentpublickey -- used to correct ivan's
# mistake of deleting vesselport entries from the geni database
movingtoonepercent2publickey = rsa_file_to_publickey("movingtoonepercent2.publickey")
onepercent2publickey = rsa_file_to_publickey("onepercent2.publickey")


# Getting us out of the mess we started with
#genilookuppublickey = rsa_file_to_publickey("genilookup.publickey")
movingtogenilookuppublickey = rsa_file_to_publickey("movingtogenilookup.publickey")

# Used as the many events onepercent publickey -- This has 50 events per vessel
movingtoonepercentmanyeventspublickey = rsa_file_to_publickey("movingtoonepercentmanyevents.publickey")
onepercentmanyeventspublickey = rsa_file_to_publickey("onepercentmanyevents.publickey")

# create an array of the states
knownstates = [canonicalpublickey, acceptdonationpublickey, 
           movingtoonepercentpublickey, onepercentpublickey,
           movingtoonepercent2publickey, onepercent2publickey,
           movingtoonepercentmanyeventspublickey, onepercentmanyeventspublickey,
           movingtogenilookuppublickey]
           
# and the human readable representations of those states
knownstates_string = ['canonicalpublickey', 'acceptdonationpublickey', 
           'movingtoonepercentpublickey', 'onepercentpublickey',
           'movingtoonepercent2publickey', 'onepercent2publickey',
           'movingtoonepercentmanyeventspublickey', 'onepercentmanyeventspublickey',
           'movingtogenilookuppublickey']
           

def check_is_seattle_installed(file_data):
  """
  <Purpose>
    Checks to see if seattle is installed.
    
  <Arguments>
    file_data:
      the logfile as a string from a node.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    Boolean. Is it installed?
  """
  return file_data.find('Did not find any seattle installs on') == -1

  
  
def insert_timestamp_from_fn(any_fn):
  """
  <Purpose>
    Gets the timestamp from a filename that has the following format:
    blabla.timestamp where timestamp is an actualy unixtime
    
  <Arguments>
    None.    
    
  <Exceptions>
    If the time is not valid or the fn is not valid, an empty string is returned

  <Side Effects>
    None.

  <Returns>
    Returns HTML formatted time.
  """
  
  # fn must be in format [blah].TIMESTAMP where timestamp is a valid unix time
  junk, sep, timestamp = any_fn.rpartition('.')
  try:
    return "<br><br><b>Log from "+time.ctime(float(timestamp))
  except Exception, e:
    print "Error in inserting timestamp. ",
    print e
    return ''
    

def key_to_string(key):
  # helper for the below method. Basically looks up the humanized name for the key
  for i in range(len(knownstates)):
    if knownstates[i] == key:
      return knownstates_string[i]
     


# internal method
def parse_vessel_string(vesseldict_string):
  """
  <Purpose>
    Parses the vesseldict and then attempts to figure out what state the node is in.
    
  <Arguments>
    vesseldict_string:
      the vesseldict file dumped as a string.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    Tuple of an array and an integer.
    
    The array is of tuples where each tuple is: (success_status, 'v#', explanation_string)
    The integer is the number of vessel_key_counters (aka how many states we have per this node)
  """
  
  # string should be a valid dict, so just eval it and conver it to a dict object
  vesseldict = eval(vesseldict_string)
  
  # each array element is a tuple with (success_status, 'v#', explanation_string)
  return_array = []
  
  # keep track of how many keys we have
  vessel_key_counter = 0
  
  # look up each vessel
  for each_vessel in vesseldict.keys():
    # this is the Xth vessel on the node
    vesselX_dict = vesseldict[each_vessel]
    # if it has the key we're looking for
    if 'userkeys' in vesselX_dict:
      # null/empty
      
      if not vesselX_dict['userkeys']:
        # empty key
        return_array.append((False, each_vessel, 'userkey is empty/null'))
      else: # not empty!
        # Kon: it's wrapped in an array for some reason? perhaps the node 
        #       is intended to be in more than one state in the future?
        pubkey_dict = vesselX_dict['userkeys'][0]
        
        # pubkey_dict is the pubkey that corresponds to the nodestate, so lets look it up
        if pubkey_dict in knownstates:
          # good it's valid
          return_array.append((True, each_vessel, key_to_string(pubkey_dict)))
          # increment how many state-keys we have
          vessel_key_counter += 1
        else:
          # oh oh... unknown pubkey!
          return_array.append((False, each_vessel, 'Unknown pubkey!:'+str(pubkey_dict)))
    else:
      # doesn't have a 'userkey' entry
      return_array.append((False, each_vessel, 'userkey does not exist'))
  return (return_array, vessel_key_counter)


def get_node_state(file_data):
  """
  <Purpose>
    Gets the node state and returns info that can be processed by make_summary.py.
    
  <Arguments>
    file_data:
      logfile of a node as a string.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    On failure:
      None 
    On success:
      (SuccessStatus, (array of node states, # of states), html_color)
  """
  # internal flag that's used in parsing the file.
  vesseldict_loop = False
  
  # parse the file line by line until we find the portion with the vesseldict
  # and then we'll need to find the end of vesseldict string.
  for each_line in file_data.splitlines():
    if each_line.find('File contents of vesseldict:') > -1 or vesseldict_loop:
      # start of vesseldict! make sure to store this in a seperate string
      # format is
      
      # File contents of vesseldict:
      # [vesseldict_as_string]
      # End contents of vesseldict
      
      # if we've already set the flag... then..
      if vesseldict_loop:
        # if this line doesn't start with the error msg, then this is the dict string
        if each_line.startswith('vesseldict is missing'):
          return (False, (['vesseldict is missing'], 0), deploy_html.colors_map['Error'])
          
        elif each_line.startswith('End contents of vesseldict'):
          # done dumping file, unset vesseldict_loop flag so we'll return with a None.
          vesseldict_loop = False
          
        else:
          # we have our string!
          vesseldict_string = each_line
          # the string and we'll get the node_state_array and the number of states the node is in
          node_state_array, state_counter = parse_vessel_string(vesseldict_string)
          
          # did we succeed? we should expect to have only one state per node
          success_status = (state_counter == 1)
          
          if success_status:
            return (True, (node_state_array, state_counter), deploy_html.colors_map['Success'])
          else:
            for each_vessel in node_state_array:
              # each_vessel[0]: Boolean, has a key?
              # each_vessel[1]: String, v1 (the vessel #)
              # each_vessel[2]: human-readable string
              if 'Unknown pubkey' in each_vessel[2]:
                return (False, (['Unknown pubkey found in '+each_vessel[1]], state_counter), deploy_html.colors_map['Error'])
            
          return (False, (['No keys found'], state_counter), deploy_html.colors_map['Error'])
      else:
        # set the flag so we can enter the loop again and read the next line
        vesseldict_loop = True
  return

  
  
def get_node_version(file_data):
  """
  <Purpose>
    Returns the node version.
    
  <Arguments>
    file_data:
      logfile read in as string for a node.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    (SuccessStatus, String)
  """

  # keep track of all the version strings we'll grab
  version_array = []
  
  # parse each line of the log, we're looking for 'version =' string
  for each_line in file_data.splitlines():
    if each_line.startswith('version ='):
      # string starst with what we want, so strip the line and add 
      # the version to our array of versions
      junk, sep, version = each_line.rpartition('=')
      version = version.strip(' "\'')
      version_array.append(version)
  
  # count how many version strings we've found so far..
  if len(version_array) == 2:
    # assume that node upgraded
    return (True, "Upgraded from "+version_array[0]+" to "+version_array[1], deploy_html.colors_map['Success'])
  elif len(version_array) == 1:
    # just return node version
    return (True, version_array[0], deploy_html.colors_map['Success'])
  else:
    # unexpected!
    return (False, "Unexpected number of version strings in log:\n"+\
      str(version_array), deploy_html.colors_map['SmallError'])



def get_nodes_up(summary_file):
  """
  <Purpose>
    Cheap way of seeing how many of the nodes our tests actually ran on..
    sum up the "versions", which is a unique line per host-log.  This can be slightly
    inaccurate (within several nodes, eg: if nodes upgraded?).
    
  <Arguments>
    summary_file:
      path to the summary.log file (htmlsummary.log)
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    Tuple of form (nodes_up, HumanString)
  """
  
    # 
    
  out, err, retcode = deploy_main.shellexec2('grep ^version '+summary_file+\
      ' | sort | uniq -c | awk \'{ print $1 }\'')
  # each line starts with a number, so convert to int and give it a try
  try:
    # this is how many computers are 'up'
    counter = 0
    for line in out.splitlines():
      counter += int(line)
  except ValueError, e:
    # ignore it, we don't really care
    pass
  except Exception, e:
    print 'Error in get_nodes_up'
    print e
  finally:
    return (counter, str(counter)+' hosts responded in a timely fashion '+\
        'and ran our tests.\n\n')
      
      
      
def get_uniq_machines(controller_file):
  """
  <Purpose>
    find out how many machines total we surveyed line looks like:
    
    Jun 16 2009 01:56:07 | Setup:  Found 950 unique hosts to connect to.
    
  <Arguments>
    controller_file:
      path to the controller.log file
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    returns an (int, HumanString)
  """

  out, err, retcode = deploy_main.shellexec2("awk '/Found/ { print $8 } ' "+controller_file)
  try:
    out = out.strip('\n\r ')
    return (str(int(out)), 'There were '+out+' unique hosts surveyed\n\n')
  except ValueError, ve:
    print 'Unexpected number of uniq hosts returned from shell.'
    print ve
  except Exception, e:
    print 'Error in get_uniq_machines()'
    print e
    
    
    
def check_is_nm_running(file_data):
  """
  <Purpose>
    Tells you if NM is running and it's status.
    
  <Arguments>
    file_data:
      log file of a node as string.
    
  <Exceptions>
    None.

  <Side Effects>
    file_data

  <Returns>
    Tuple in the form of (BooleanErrorStatus, StringDesc)
  """
  
  return_value = ''
  # now check if we have any NM errors
  if file_data.find('Node Manager is not running.') > -1:
    return_value = (False, 'Not running', deploy_html.colors_map['Error'])
  elif file_data.find('[NodeManager]') > -1:
    return_value = (False, 'Error state', deploy_html.colors_map['Error'])
  else:
    return_value = (True, 'Running', deploy_html.colors_map['Success'])
  return return_value
  
  
  
def check_is_su_running(file_data):
  """
  <Purpose>
    Tells you if SU is running and it's status.
    
  <Arguments>
    file_data:
      log file of a node as string.
    
  <Exceptions>
    None.

  <Side Effects>
    file_data

  <Returns>
    Tuple in the form of (BooleanErrorStatus, StringDesc)
  """
  
  return_value = ''
  # now check if we have any NM errors
  if file_data.find('Software Updater is not running.') > -1:
    return_value = (False, 'Not running', deploy_html.colors_map['Error'])
  elif file_data.find('[SoftwareUpdater]') > -1:
    if file_data.find('Software Updater memory usage is unusually high') > -1:
      return_value = (False, 'High Memory Usage', deploy_html.colors_map['SmallError'])
    else:
      return_value = (False, 'Error State', deploy_html.colors_map['Error'])
  else:
    return_value = (True, 'Running', deploy_html.colors_map['Success'])
  return return_value
