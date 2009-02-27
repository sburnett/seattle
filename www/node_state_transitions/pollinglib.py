""" 
Author: Justin Cappos

Module: Polling program for GENI.   It looks for donations, sets them up, and
        writes the new info in the database.   

Start date: October 18th, 2008

This polls for resources donations in GENI.   It currently has lots and lots
of problems and was hurriedly written.   This will not recover correctly if 
it's interrupted when initializing a node, will not allow different owners
to donate resources from the same node.   This is a prime candidate for 
improvements or a rewrite.


"""


# It is absolutely essential to understand how to correctly write a processing
# function for Seattle GENI.   The obvious rules apply, such as check for 
# errors as much as possible, log any errors that occur, and write the code 
# clearly and cleanly.   However, this is not sufficient.
#
# The model for how keys are used is that each installer originally is set up
# with a per-user "donor key".   This links the donated vessel to the user who
# wanted to donate the resources.   The "user key" for this vessel should be 
# set to a well known public key.   The purpose of this key is to allow GENI
# to discover those nodes where a vessel has been donated.
#
# The normal procedure is that a Seattle GENI processing function will discover
# the new vessel and then perform a series of operation to prepare the 
# resources for GENI use.   For example, Seattle GENI may be given a vessel 
# with 8% of the node's resources, and may want to instead divide those 
# resources into 8 vessels each having ~ 1%.
#
# However, over time the number of different states a vessel may be in is 
# expected to grow.   So each time we want to transition to a new state, we
# don't want to have to handle every possible outdated intermediate state.   
# To avoid this, we can use different keys to indicate the state that a
# node is in.   
#
# For example, suppose that after we split our vessels into 
# 8 pieces, we realize that this is too small for many applications to use.
# We decide we really want to split each vessel into 4 pieces instead.   Now
# we need to handle nodes that are in 8 pieces (as the nodes we've already 
# setup are), 1 piece (as a new node would be), and also any failure scenario
# that may occur while setting up 8 pieces or 4 pieces.   
#
# It should be clear that as more states are added, this becomes increasingly
# difficult to correctly code.   As a result, the design choice that I propose
# is that there is a "canonical form" that the vessels on a node may always be 
# returned to.  All transformations of vessels will begin with the vessel in 
# that state and so reasoning about transformations is simplified.  
#
# The canonical form is almost identical to the donated form.   It's a single 
# vessel containing all the resources donated.   However, the owner of the 
# resources is not the user's donor key.   The owner of the resources is 
# instead a specially generated public key for the node.   Resources in 
# canonical form use the "canonical" public key as a user to advertise that 
# they are in canonical form.
#
# The state that a node is in is indicated by a key called the state key.
# This is implemented by setting a user key on a vessel.
#
# To build a new state 'X' for nodes you must provide three functions:
#   A function that changes the node state key to be an intermediate key.
#   A can2X function that can transform a node in "canonical form" to state X.
#      THE LAST OPERATION ON THE NODE MUST BE TO ENSURE THAT
#      THE NODE USES THE STATE KEY.
#   A X2can function that can transform a node that was either in state X or
#      failed when running can2X into canonical form.  THE LAST OPERATION ON 
#      THE NODE MUST BE TO ENSURE THAT THE NODE USES THE CANONICAL FORM KEY.
#
# Note that X2can is very similar for most end states.   As a result, 
# a helper function combinevessels listed below may be of assistance.
#
# To use your can2X function, call locateandprocessvessels with a set of tuples
# for the key and the function to call.



from repyportability import *

# BUG: Can I include this multiple places and pass handles between modules?
include nmclient.repy
include rsa.repy
include listops.repy
include parallelize.repy

import random
import advertise
import runonce
import logging
import sys
import time
import genidb
import traceback



class NodeError(Exception):
  """This exception means the node is in an invalid state"""


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
genilookuppublickey = rsa_file_to_publickey("genilookup.publickey")
movingtogenilookuppublickey = rsa_file_to_publickey("movingtogenilookup.publickey")


knownstates = [canonicalpublickey, acceptdonationpublickey, 
               movingtoonepercentpublickey, onepercentpublickey,
               movingtoonepercent2publickey, onepercent2publickey,
               genilookuppublickey, movingtogenilookuppublickey]



def processnode(node, acceptnewnode, startstate, endstate, nodeerrorfunction, nodeprocessfunction, args):

  if not node:
    # sometimes an empty string is returned by OpenDHT
    return

  print time.ctime(),"Processing: ",node
  try:
    nmhandle, nodevesseldict = getnodehandleanddict(node,acceptnewnode)
  except NMClientException, e:
    print time.ctime(), "On node "+node+" error '"+str(e)+"' getting node handle"
    nodeerrorfunction(node)
    return

  # always clean up the handle
  try:
    if getnodestate(nmhandle, nodevesseldict)[0] != startstate:
      # Oh.   The DHT must contain old information
      print time.ctime(), "Node no longer has state!"
      return

    try:
      nodeprocessfunction(nmhandle, node, nodevesseldict, *args)
    except Exception, e:
      print time.ctime(), "In nodeprocessfunction on node:"+node+" error '"+str(e)+"'"
    else:
      try:
        setnodestate(nmhandle, endstate)
      except Exception, e:
        print time.ctime(), "In setnodestate on node:"+node+" error '"+str(e)+"'"

  finally:
    # handle was cleaned up...
    nmclient_destroyhandle(nmhandle)



def locateandprocessvessels(statefunctionargtuplelist, uniquename, sleeptime, acceptnewnode=False,parallelinstances=1):
  """
   <Purpose>
      Looks up a public key and then calls a function on a set of nodes 

   <Arguments>
      statefunctionargtuplelist:
         A list of tuples with a:

           start state : publickey

           end state : publickey

           nodeerrorfunction : called when there is an error in
           contacting the node. This function has the first argument
           already provided : the node name (IP address).

           nodeprocessfunction : called to change the node state. This
           function has the first two arguments already provided, the
           node handle and the node name.
         
           nodeprocessfunction args list : list of arguments to the nodeprocessfunction.    

      uniquename:
         A unique name for this action that can be used for logging and to
         ensure multiple copies aren't running

      sleeptime:
         The amount of time to sleep between lookups / node processing

      acceptnewnode:
         Allow a new node to have the following key.   Will create a new key 
         and add a per node key to the database

      parallelinstances:
         The number of concurrent events that should process nodes.

   <Exceptions>
      None

   <Side Effects>
      Ensures there is only one lookup for this key happening at a time 

   <Returns>
      This function runs forever (unless there is a fatal error)
  """

  logfn = "log."+str(uniquename)

  # set up the circular logger (at least 50 MB buffer)
  loggerfo = logging.circular_logger(logfn, 50*1024*1024)

  # redirect standard out / error to the circular log buffer
  sys.stdout = loggerfo
  sys.stderr = loggerfo


  lockname = "polling."+uniquename

  time_updatetime(34612)
  
  # get a unique lock based upon the key
  if runonce.getprocesslock(lockname) != True:
    # Someone else has the lock...
    print time.ctime(),"The lock is held.   Exiting"
    return

  print time.ctime(),"Starting..."

  # BUG: There could be a nasty race here where a node isn't seen as in a 
  # state because it doesn't advertise in time to be listed.
  # This will be fixed when we fix the NM advertisement bug (next update) so
  # I'll leave it in for now.

  cachednodelist = []
  while True:
    for statefunctionargtuple in statefunctionargtuplelist:

      startstate = statefunctionargtuple[0]
      endstate = statefunctionargtuple[1]
      nodeerrorfunction = statefunctionargtuple[2]
      nodeprocessfunction = statefunctionargtuple[3]
      args = statefunctionargtuple[4:]

      # I likely need to do something smart here when this fails...
      nodelist = advertise.lookup(startstate)

      # shuffle the nodelist to avoid reoccurring failures on processing
      # the same node over and over -- allows us to eventually process
      # other nodes
      random.shuffle(nodelist)
      print time.ctime(),"For start state '"+str(startstate['e'])[:10]+"...' found nodelist:",nodelist
      
############# NOTE: cachednodelist SHOULD BE REMOVED after 0.1c is deployed!
      # have a small chance to flush the cache to prevent nodes from being in 
      # the cache forever
      if random.random() < .1:
        print time.ctime(), "Flushing cache"
        cachednodelist = []
      cachednodelist = cachednodelist + nodelist
      cachednodelist = listops_uniq(cachednodelist)
      random.shuffle(cachednodelist)

# parallelize the execution of the function across the nodes...
      phandle = parallelize_initfunction(cachednodelist, processnode, parallelinstances, acceptnewnode, startstate, endstate, nodeerrorfunction, nodeprocessfunction, args)

      try: 
        while not parallelize_isfunctionfinished(phandle):
          if not runonce.stillhaveprocesslock(lockname):
            print time.ctime(),"I have lost the lock.   Exiting"
            return
          time.sleep(1)

        # Get the results so that I can log ...
        runresults = parallelize_getresults(phandle)
        for nodename, exceptionstring in runresults['exception']:
          print "Failure on node "+nodename+".   Exception string '"+exceptionstring+"'"

      finally:
        # clean up the handle
        parallelize_closefunction(phandle)

      time.sleep(sleeptime)



def getnodehandleanddict(node, acceptnewnode=False):
  """
   <Purpose>
      Returns a node handle for a node and dictionary

   <Arguments>
      node:
         A string containing IP:port

      acceptnewnode:
         Allow a new node to have the following key.   Will create a new key 
         and add a per node key to the database

   <Exceptions>
      NMClientException: 
         If there are communication errors
    
   <Side Effects>
      None

   <Returns>
      A nmhandle with the correct keys loaded
  """


  host, portstring = node.split(':')
  port = int(portstring)

  # may raise an exception
  thisnmhandle = nmclient_createhandle(host, port)

  # close the handle on any error...
  try:
    retdict = nmclient_getvesseldict(thisnmhandle)
          
    nodeID = rsa_publickey_to_string(retdict['nodekey'])

    # look up the node info using its key. if no such node found,
    # node will be None, otherwise it will be a Donation object
    # linked to the db.
    dbnode = genidb.lookup_node(nodeID)


    if acceptnewnode:
      # New nodes are complex so this is broken out for simplicity...
      dbnode = acceptnewnodehelper(thisnmhandle, host, port, retdict, dbnode)

    if not dbnode:
      raise NodeError("Node "+node+" with ID '"+nodeID+"' does not have an entry in the database")
    # set up the handle to do signed requests...
    thishandleinfo = nmclient_get_handle_info(thisnmhandle)
    thishandleinfo['publickey'] = rsa_string_to_publickey(dbnode.owner_pubkey)
    thishandleinfo['privatekey'] = rsa_string_to_privatekey(dbnode.owner_privkey)
    nmclient_set_handle_info(thisnmhandle, thishandleinfo)


  except:
    # left for further debugging, but not essential since the
    # exception is re-raised and printed further up the stack
    print time.ctime(),"Exception in getnodehandleanddict"
    traceback.print_exc(file=sys.stdout)
    nmclient_destroyhandle(thisnmhandle)
    raise

  return thisnmhandle,retdict






def acceptnewnodehelper(nmhandle, host, port, retdict, dbnode):
  # private
  # A helper function removed from getnodehandleanddict for readability

  # The database and the node can potentially each be in two different states:
  # The db can either have no entry or have an entry for the node (with correct
  # key).   The node can either have the donor key as the owner or the 
  # per node key as the owner.
  # We do the db state update *FIRST* so there are only three possible combined
  # database / node states:
  # DB (no entry)        Node (donor key)
  # DB (per node key)    Node (donor key)
  # DB (per node key)    Node (per node key)
  # 
  # This function detects the state and in the absense of errors leaves the 
  # node and database in the final state (returning the dbnode object)


  # Find the node's owner key.   I can't be in more than one state at a time so
  # I'll find the owner key of the vessel in a state.

  for vesselname in retdict['vessels']:
    if listops_intersect(retdict['vessels'][vesselname]['userkeys'], knownstates):
      donationownerpubkey = retdict['vessels'][vesselname]['ownerkey']
      donationvesselname = vesselname
      break
  else:
    raise NodeError("Node "+host+":"+str(port)+" does not seem to have a state after checking!")

  nodeID = rsa_publickey_to_string(retdict['nodekey'])

  if dbnode == None:
    print time.ctime(),"No DB entry"
    # DB (no entry)        Node (donor key)

    dbnode = genidb.create_node(nodeID, host, port, 'Initializing', retdict['version'], rsa_publickey_to_string(donationownerpubkey))
    print time.ctime(),'create_node success with dbnode nodeID', nodeID
    # Now I need to change the node state...
    # change the owner.   First I need to set up the handle to use the old keys
    myhandleinfo = nmclient_get_handle_info(nmhandle)
    myhandleinfo['publickey'] = donationownerpubkey
    myhandleinfo['privatekey'] = rsa_string_to_privatekey(genidb.get_donor_privkey(rsa_publickey_to_string(donationownerpubkey)))
    nmclient_set_handle_info(nmhandle, myhandleinfo)

    nmclient_signedsay(nmhandle, "ChangeOwner", donationvesselname, dbnode.owner_pubkey)
    
    # after this I'll need to fix the handle to use the new key...
    return dbnode

  # okay, the state exists
  
  if donationownerpubkey != rsa_string_to_publickey(dbnode.owner_pubkey):
    # DB (per node key)    Node (donor key)
    print time.ctime(), "DB per node key, node donorkey"

    # Now I need to change the node state...
    # change the owner.   First I need to set up the handle to use the old keys
    myhandleinfo = nmclient_get_handle_info(nmhandle)
    myhandleinfo['publickey'] = donationownerpubkey
    myhandleinfo['privatekey'] = rsa_string_to_privatekey(genidb.get_donor_privkey(rsa_publickey_to_string(donationownerpubkey)))
    nmclient_set_handle_info(nmhandle, myhandleinfo)

    nmclient_signedsay(nmhandle, "ChangeOwner", donationvesselname, dbnode.owner_pubkey)
    
    # after this I'll need to fix the handle to use the new key...
    return dbnode

  # DB (per node key)    Node (per node key)
  print time.ctime(), "DB per node key, node per node key"
  
  # NOTE: The case that there is a node that has the state key, but the owner 
  # key isn't known by the database will be caught in getnodehandleanddict
  return dbnode




def getnodestate(nmhandle,vesseldict):
  """
   <Purpose>
      Finds the state of a node.

   <Arguments>
      nmhandle:
         The handle to the node manager

      vesseldict:
         A dictionary as returned by nmclient_getvesseldict

   <Exceptions>
      NMClientException: 
         If there are communication errors
    
      NodeError:
         If there seem to be multiple states for the node

   <Side Effects>
      None

   <Returns>
      A tuple where the first element is the state the node is in (i.e. a key 
      in knownstates) or None and the second element is a list of vessels with
      that marked as the user.
  """


  # get the key used in the handle...
  myhandleinfo = nmclient_get_handle_info(nmhandle)
  mypublickey = myhandleinfo['publickey']


  # We don't know what the state is yet.   I want to assign this to a variable
  # instead of returning immediately because I need to check if we think 
  # multiple keys qualify.
  vesselstate = None
  vesselnamelist = []

  # I'm only interested in the vessels I control...
  for vesselname in vesseldict['vessels']:

    if vesseldict['vessels'][vesselname]['ownerkey'] == mypublickey:
      # find if the user key(s) represent a state
      stateslisted = listops_intersect(vesseldict['vessels'][vesselname]['userkeys'],knownstates)
      for state in stateslisted:
        if vesselstate and state != vesselstate:
          # Uh oh.   It's a dup!
          raise NodeError("More than one state '"+str(vesselstate)+"' and '"+str(state)+"' on the same node")
        vesselstate = state
        vesselnamelist.append(vesselname)

  # I'll return None if the state is not set or the state otherwise.
  return vesselstate, vesselnamelist

  
  



def setnodestate(nmhandle,newstate):
  """
   <Purpose>
      Sets the state of a node.

   <Arguments>
      nmhandle:
         The handle to the node manager

      newstate:
         The state the node should end up in

   <Exceptions>
      NMClientException: 
         If there are communication errors

      NodeError:
         If the node is not in a valid state
    

   <Side Effects>
      None

   <Returns>
      None
  """


  vesseldict = nmclient_getvesseldict(nmhandle)

  oldstate, vesselswithstate = getnodestate(nmhandle,vesseldict)

  if len(vesselswithstate)==0:
    raise NodeError("There are no vessels with preexisting state")

  # I'll remove the state from all vessels save one.
  for vesselname in vesselswithstate[:-1]:
    
    # remove the state key from all of these...
    vesseldict['vessels'][vesselname]['userkeys'].remove(oldstate)

    # and change the users
    _changeusers(nmhandle, vesselname, vesseldict['vessels'][vesselname]['userkeys'])
    

  vesselname = vesselswithstate[-1]
  
  # remove the state key from all of these...
  vesseldict['vessels'][vesselname]['userkeys'].remove(oldstate)

  # add the new state...
  vesseldict['vessels'][vesselname]['userkeys'].append(newstate)

  # and change the state
  _changeusers(nmhandle, vesselname, vesseldict['vessels'][vesselname]['userkeys'])








def combinevessels(nmhandle, nodename, vesseldict, keepthisstate):
  """
   <Purpose>
      Combines vessels on the same node into a single vessel.   This helps to 
      move the node close to canonical form.   Don't forget to add the 
      canonical public key when done!

   <Arguments>
      nmhandle:
         The handle to the node manager

      nodename:
         The node we're working on

      vesseldict:
         The node's vessel dictionary

      keepthisstate:
         The state.   I'll always ensure a vessel has this at all points.

   <Exceptions>
      NMClientException: 
         if there are communication errors

      Various errors (KeyError, etc.) if the keys are invalid

   <Side Effects>
      None

   <Returns>
      The name of the new vessel
  """

  myhandleinfo = nmclient_get_handle_info(nmhandle)
  mypublickey = myhandleinfo['publickey']

  vessellist = []

  startingvessel = None

  for vesselname in vesseldict['vessels']:
    if vesseldict['vessels'][vesselname]['ownerkey'] == mypublickey:
      vessellist.append(vesselname)
      if keepthisstate in vesseldict['vessels'][vesselname]['userkeys']:
        startingvessel = vesselname


  if not startingvessel:
    raise NodeError("Can't find state '"+str(keepthisstate)+"' in node "+nodename)

  vessellist.remove(startingvessel)

  # The basic philosophy is that we'll join vessels repeatedly.   Pretty simple
  # actually...   The first vessel (target vessel) will retain the user keys 
  # and therefore the state
  
  targetvessel = startingvessel

  for currentvessel in vessellist:
    try:
      newvessel = nmclient_signedsay(nmhandle, "JoinVessels", targetvessel, currentvessel)
    except NMClientException, e:
      print time.ctime(), "Error '"+str(e)+"' joining vessels in combinevessels on node "+nodename
    
    targetvessel = newvessel

  return targetvessel





def _changeusers(nmhandle, targetvessel, userpubkeylist):
  # Private to this module
  # Just a simple helper program to do a change users (will throw exceptions)


  userpubkeystringlist = []
  for userpubkey in userpubkeylist:
    userpubkeystringlist.append(rsa_publickey_to_string(userpubkey))

  nmclient_signedsay(nmhandle, "ChangeUsers", targetvessel, '|'.join(userpubkeystringlist))






