"""
<Program Name>
  node_monitor.py

<Started>
  February 14, 2011

<Author>
  Steven Portzer

<Purpose>
  Produces a log of when Seattle nodes are advertising and/or contactable
  by logging whenever nodes start or stop advertising, and when they become
  contactable or not contactable.

  This gives us some idea of typical uptime for Seattle nodes and allows us to
  identify other trends in node activity, like nodes running on mobile devices
  or exhibiting diurnal patterns.

<Usage>
  This script should be run in a directory that contains a copy of the Seattle
  Experiment Library in a subdirectory named "experimentlibrary". See
  https://seattle.cs.washington.edu/wiki/Libraries/ExperimentLibrary for more
  information on setting up the Experiment Library.

  When running node_monitor.py, it should be passed two arguments: the name of a
  directory containing the public keys to check for advertising nodes and the
  name of the directory where the logs should be saved.

<Log Format>
  This script produces two logs. The first, "node_events.log", contains a line
  for every time a node starts or stops advertising or being contactable. Each
  line contains the following elements separated by spaces:

    time:
        approximately when the event was detected

    location:
        the location of the node the event pertains to, see information on
        experimentlib's nodelocation strings for format information

    event_type:
        "advertising", "not_advertising", "contactable", or "not_contactable"
        depending on the sort of event it is

    name:
        for events related to advertising this is the name of the public key
        being advertised under, for contactability events this is the md5 hash
        of the node's nodeid

  The log "node_dicts.log" contains a node dictionary on each line. Whenever a
  node is successfully contacted, it's dictionary is appended to this log. For
  information on the format of the dictionaries, see the documentation for
  browse_node(location).
"""


import sys

sys.path.append("experimentlibrary")
import experimentlib

import os
import time
import hashlib
import random


# Number of seconds to wait between polling lists of advertising nodes.
SLEEP_PERIOD = 60

# Seconds to wait when polling nodes which are both advertising and contactable.
CONSISTENT_POLLING_INTERVAL = 4*60*60      # every 4 hours
# Number of seconds to wait between polling nodes which are only advertising.
ONLY_ADVERTISING_POLLING_INTERVAL = 5*60   # every 5 minutes
# Number of seconds to wait between polling nodes which are only contactable.
ONLY_CONTACTABLE_POLLING_INTERVAL = 5*60   # every 5 minutes


# The name of the file where advertising and contactability events are logged
NODE_LOG = "node_events.log"
# The name of the file where information retrieved from browsing nodes is logged
VESSEL_LOG = "node_dicts.log"


# A dict storing the currently contactable nodeids as values with their
# current location as the key.
contactabledict = {}

# A dict with public key names as keys and the list of locations advertising
# under that key last time we checked as values.
oldlocationdict = {}

# A dict with locations as keys and the next time we should try to contact the
# node at that location as values.
nextlookupdict = {}



def browse_node(location):
  """
  <Purpose>
    Browses the node located at the given location and returns a condensed
    version of the vessel dict so it can be logged to file.

  <Arguments>
    location:
        The location of the node to browse, given as a string in the format used
        by Experiment Library.

  <Exceptions>
    Any Exception that is thrown by experimentlib.browse_node may be raised.

  <Side Effects>
    None.

  <Returns>
    A dictionary of node and lookup properties of the node at located at
    location. The dictionary contains the following values:
      'nodeid': the md5 hash of the node's id
      'location': the location of the node, almost certainly the passed location
          argument
      'version': the version of seattle running on the node
      'time': when the node information was received
      'latency': the time taken to retrieve the information
      'vesseldicts': a list of vessel dictionaries containing 'vesselname',
          'status', 'ownerkey', and 'userkeys' keys. The 'ownerkey' and
          'userkeys' are hashed using md5 to conserve space and improve human
          readability.
  """

  starttime = time.time()
  vesseldictlist = experimentlib.browse_node(location)
  endtime = time.time()

  nodedict = {}

  nodeid = vesseldictlist[0]['nodeid']
  hashfunc = hashlib.md5()
  hashfunc.update(nodeid)
  nodehash = hashfunc.hexdigest()

  nodedict['nodeid'] = nodehash
  nodedict['location'] = location
  nodedict['version'] = vesseldictlist[0]['version']
  nodedict['time'] = endtime
  nodedict['latency'] = endtime - starttime

  nodedict['vesseldicts'] = []

  for vesseldict in vesseldictlist:
    newvesseldict = {}

    newvesseldict['vesselname'] = vesseldict['vesselname']
    newvesseldict['status'] = vesseldict['status']

    # Hash all the keys to minimize the size of the log file.

    ownerkey = vesseldict['ownerkey']
    hashfunc = hashlib.md5()
    hashfunc.update(str(ownerkey['e']))
    hashfunc.update(str(ownerkey['n']))
    newvesseldict['ownerkey'] = hashfunc.hexdigest()

    newvesseldict['userkeys'] = []

    for userkey in vesseldict['userkeys']:
      hashfunc = hashlib.md5()
      hashfunc.update(str(userkey))
      newvesseldict['userkeys'].append(hashfunc.hexdigest())

    nodedict['vesseldicts'].append(newvesseldict)

  return nodedict



def advertising_lookup(identity, retries):
  """
  <Purpose>
    Attempts to retrieve the list of nodes advertising under a given identity
    and returns then list if successful.

  <Arguments>
    identity:
        An Experiment Library identity for looking up node locations.

    retries:
        An integer giving the number of times to retry the lookup if it fails
        or returns an empty list.

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None if all tries result in exceptions, and a list of the nodes advertising
    under the given identity otherwise.
  """

  # Every once in a while, a lookup returns an empty list when it shouldn't.
  # This is presumably due to something timing out. We don't want to see that
  # all the nodes suddenly stopped advertising when this obviously isn't the
  # case, so we should retry the lookup when the returned list is empty.
  # However, some lookups may legitimately return an empty list, so the calling
  # function should pick a reasonable value for the maximum number of retries.

  locationlist = None

  while retries >= 0 and (locationlist is None or len(locationlist) == 0):
    try:
      locationlist = experimentlib.lookup_node_locations_by_identity(identity)
    except Exception, e:
      pass
    retries -= 1

  return locationlist



def check_nodes(identitydict, nodelogfile, vessellogfile):
  """
  <Purpose>
    Determines which nodes are advertising under the keys in identitydict and
    contacts any nodes that need to be contacted.

  <Arguments>
    identitydict:
        A dictionary where the keys are public key names and the value is an
        Experiment Library identity for that key.

    nodelogfile:
        An open file for logging new advertising and contactability events.

    vessellogfile:
        An open file for logging the node dictionaries returned by browse_node.

  <Exceptions>
    None.

  <Side Effects>
    Writes to nodelogfile and vessellogfile.

  <Returns>
    None.
  """

  currenttime = time.time()

  # Currently advertising node locations.
  advertisingset = set()

  # Locations that started advertising under some key.
  addedlocationset = set()

  # Locations that stopped advertising under some key.
  droppedlocationset = set()
  
  for keyname in identitydict:

    # Locations that were advertising last time we checked this publickey.
    oldlocationlist = oldlocationdict[keyname]

    # Find all the node locations advertising under this key. If we don't expect
    # there to be many nodes advertising, then don't bother retrying many times.
    locationlist = advertising_lookup(identitydict[keyname],
        min(len(oldlocationlist), 10))

    if locationlist is None:
      print currenttime, "ERROR: advertising lookup failed for", keyname
      continue

    oldlocationdict[keyname] = locationlist

    advertisingset = advertisingset.union(locationlist)

    # Find any changes in the list of advertising nodes.
    startedadvertisingset = set(locationlist).difference(oldlocationlist)
    stoppedadvertisingset = set(oldlocationlist).difference(locationlist)

    addedlocationset = addedlocationset.union(startedadvertisingset)
    droppedlocationset = droppedlocationset.union(stoppedadvertisingset)

    for nodelocation in startedadvertisingset:
      nodelogfile.write(str(currenttime) + " " + nodelocation +
                        " advertising " + keyname + "\n")

    for nodelocation in stoppedadvertisingset:
      nodelogfile.write(str(currenttime) + " " + nodelocation +
                        " not_advertising " + keyname + "\n")


  for location in addedlocationset:
    # Contact this node immediately since it started advertising.
    nextlookupdict[location] = 0

  for location in droppedlocationset:
    if location in contactabledict or location in advertisingset:
      # Contact this node immediately since it stopped advertising.
      nextlookupdict[location] = 0
    else:
      # This node isn't advertising or contactable, so there's no real reason
      # to contact it until it starts advertising again.
      if location in nextlookupdict:
        del nextlookupdict[location]
      else:
        print currenttime, "ERROR:", location, \
            "not in nextlookupdict when it stopped advertising"


  # The list of node locations to try to contact at this time.
  currentlookuplist = []

  for location in nextlookupdict:
    if nextlookupdict[location] < currenttime:
      currentlookuplist.append(location)

  # Contact all list of node we're currently interested in. This lookup is
  # parallelized to improve speed. Especially for the mass lookup that occurs
  # when the script starts, increasing experimentlib.num_worker_threads to a
  # larger number will further increase the speed of this lookup.
  successlist, failurelist = experimentlib.run_parallelized(
                                              currentlookuplist, browse_node)


  # These are the nodes for which contacting them failed
  for nodelocation, errorstring in failurelist:

    if nodelocation in contactabledict:
      nodeid = contactabledict.pop(nodelocation)
      nodelogfile.write(str(currenttime) + " " + nodelocation + 
                        " not_contactable " + nodeid + "\n")

    if nodelocation in advertisingset:
      # Node is advertising but not contactable, so try again later.
      nextlookupdict[nodelocation] = currenttime + \
          (random.random() + 0.5) * ONLY_ADVERTISING_POLLING_INTERVAL
    else:
      # This node isn't advertising or contactable, so there's no real reason
      # to contact it until it starts advertising again.
      if nodelocation in nextlookupdict:
        del nextlookupdict[nodelocation]
      else:
        print currenttime, "ERROR:", nodelocation, \
            "not in nextlookupdict when it stopped being contactable"


  # These are the nodes we successfully contacted.
  for nodelocation, nodedict in successlist:
    # Log the retrieved node information.
    vessellogfile.write(str(nodedict) + "\n")

    nodeid = nodedict['nodeid']

    if nodelocation in contactabledict:
      # The node changed nodeid while still advertising. This probably won't
      # ever happen, but we might as well check. (Note: apparently this does
      # happen every once in a while.)
      if nodeid != contactabledict[nodelocation]:
        nodelogfile.write(str(currenttime) + " " + nodelocation +
                    " not_contactable " + contactabledict[nodelocation] + "\n")
        del contactabledict[nodelocation]

    if nodelocation not in contactabledict:
      contactabledict[nodelocation] = nodeid
      nodelogfile.write(str(currenttime) + " " + nodelocation +
                        " contactable " + nodeid + "\n")

    # Pick a semi-random time to do the next lookup so we aren't contacting all
    # the nodes at once.
    if nodelocation in advertisingset:
      nextlookupdict[nodelocation] = currenttime + \
          (random.random() + 0.5) * CONSISTENT_POLLING_INTERVAL
    else:
      nextlookupdict[nodelocation] = currenttime + \
          (random.random() + 0.5) * ONLY_CONTACTABLE_POLLING_INTERVAL



def main(identitydict, logdir):
  """
  <Purpose>
    An infinite loop that periodically calls check_nodes to determine which
    nodes are advertising and/or contactable.

  <Arguments>
    identitydict:
        A dictionary where the keys are public key names and the value is an
        Experiment Library identity for that key.

    logdir:
        A string containing the file path to the directory where the log files
        should be located.

  <Exceptions>
    None.

  <Side Effects>
    Writes to logs located in the logdir directory.

  <Returns>
    None.
  """

  while True:

    nodelogfile = open(logdir + "/" + NODE_LOG, 'a')
    vessellogfile = open(logdir + "/" + VESSEL_LOG, 'a')

    check_nodes(identitydict, nodelogfile, vessellogfile)

    nodelogfile.close()
    vessellogfile.close()

    # Wait for the predefined period of time.
    time.sleep(SLEEP_PERIOD)



def load_identities(directory):
  """
  <Purpose>
    Loads all the public keys from a given directory and returns a dictionary
    of identities for those public keys.

  <Arguments>
    directory:
        The directory to search in for public keys.

  <Exceptions>
    If directory isn't a valid directory or one of the publickey files is
    improperly formated, an exception will be raised.

  <Side Effects>
    None.

  <Returns>
    A dictionary with public key names (the file name minus the ending
    .publickey) mapping to identities for the public keys.
  """

  identitydict = {}
  filelist = os.listdir(directory)

  for entry in filelist:
    if entry.endswith(".publickey"):
      identity = experimentlib.create_identity_from_key_files(
                                                    directory + "/" + entry)
      keyname = entry[:-len(".publickey")]
      identitydict[keyname] = identity
      oldlocationdict[keyname] = []

  return identitydict



if __name__ == '__main__':

  if len(sys.argv) != 3:
    print "usage: python node_logging.py PUBLIC_KEY_DIRECTORY LOG_DIRECTORY"

  else:
    identitydict = load_identities(sys.argv[1])
    main(identitydict, sys.argv[2])

