"""
   Author: Justin Cappos

   Start Date: 28 May 2009

   Description:

   This is the XMLRPC interface for the backend of the seattleGENI database.   
   The majority of the backend functionality will reside in this file, but 
   lower level calls may be stubbed out for testing.
"""


# I need to get lock objects to handle concurrency and will use settimer for 
# running the cleanup thread...
from repyportability import *


# These are used to build a threaded XMLRPC server...
import SocketServer
import SimpleXMLRPCServer
import time

# A threaded XMLRPC server class, I'll use this just like SimpleXMLRPCServer
class ThreadedXMLRPCServer(SocketServer.ThreadingMixIn, SimpleXMLRPCServer.SimpleXMLRPCServer):
  """This is a threaded XMLRPC Server. """


# These are separated out into different modules mostly to simplify testing
# JAC: use these imports for testing...
#import falseNodeManagerAPI as NodeManagerAPI
#import falseDatabaseAPI as DatabaseAPI
import NodeManagerAPI
import DatabaseAPI


import persist

# the list of vesselnames that need to be cleaned up before reuse...
cleanuplist = []

cleanuplistlock = getlock()

# should we print debugging output?
DEBUG = True
DEBUGrequestcountdict = {}
DEBUGrequestcountdict['AssignVesselToUser'] = 0
DEBUGrequestcountdict['ExpireVessel'] = 0

# need sys to flush output to stdout/stderr
import sys

# used in _atomically_getorcreatelock
lockgettinglock = getlock()

# a set of locks that prevent race conditions on accessing a vessel.
vesselnamelockdict = {}


# The port that we'll listen on...
LISTENPORT = 8000




# will get a lock for a vessel or create one if one doesn't already exist
def _atomically_getorcreatevessellock(vesselname):

  # I need to lock this to prevent concurrent calls on the same vesselname from
  # getting different locks...
  lockgettinglock.acquire()

  # always release the lockgettinglock...
  try:

    # if missing, create a lock
    if vesselname not in vesselnamelockdict:
      vesselnamelockdict[vesselname] = getlock()

    # return the lock that is specific to this vesselname
    return vesselnamelockdict[vesselname]

  finally: 
    lockgettinglock.release()




def AssignVesselToUser(vesselname,userkeylist,username, VESSEL_EXPIRE_TIME_SECS = 60*60*4):
  """
    <Purpose>
      Assigns a vessel to a user (adding the userkeylist to the set of keys
      that are trusted by this vessel).   This function does not enforce 
      policy so the caller must ensure that the user is supposed to receive
      the vessel.

    <Arguments>
      vesselname:
        The vessel to assign to the user.   The name is in the format: 
        str(host public key):vesselid
      userkeylist:
        The list of keys to add to the vessel as user keys
      username:
        The user who will have a vesselmap entry created
      VESSEL_EXPIRE_TIME_SECS = 60*60*4 (4 hours):
        The amount of time until the vessel should expire

    <Exceptions>
      Exception is raised when the call fails.   The string that is returned
        will give details as to why the call failed.
      ValueError is raised when given invalid input.

    <Side Effects>
      Sets the user keys on a remote node, may create a lock, and on failure
      will trigger the cleanup of the vessel.

    <Returns>
      None.
  """
  DEBUGrequestcountdict['AssignVesselToUser'] = DEBUGrequestcountdict['AssignVesselToUser'] + 1

  # check that the arguments are valid

  vesselip, vesselport, vesselid = DatabaseAPI.convert_vesselname_to_ipportid(vesselname)
  

  if type(userkeylist) != type([]):
    raise ValueError("Invalid userkeylist '"+str(userkeylist)+"'")

  if len(userkeylist) == 0:
    raise ValueError("Must have at least one key in the userkeylist: '"+str(userkeylist)+"'")

  # Do I need to check key validity?

  if type(username) != type(''):
    raise ValueError("Invalid username '"+str(username)+"'")

  # I don't need to check that the user's name is in the database because the 
  # DatabaseAPI will catch this



  # get a lock so that there isn't a race to update this vessel...
  thisvessellock = _atomically_getorcreatevessellock(vesselname)

  # lock this vessel...
  thisvessellock.acquire()
  # ... but always release it when done
  try:
    # I need to ensure this vessel isn't assigned in the database to another
    # user...
    if DatabaseAPI.vesselname_is_in_vesselmap(vesselname):
      raise Exception("Vesselname '"+vesselname+"' was already allocated.")

    # If it's being cleaned up, don't allocate it.
    if vesselname in cleanuplist:
      raise Exception("Vesselname '"+vesselname+"' is dirty and so was not allocated.")

    try:
      # ChangeUsers...
      ownerpublickey, ownerprivatekey = DatabaseAPI.get_ownerkeys_given_vesselname(vesselname)

      NodeManagerAPI.dosignedcall(vesselip, vesselport, ownerpublickey, ownerprivatekey, "ChangeUsers", vesselid, '|'.join(userkeylist))

    except:
      # this vessel has a problem, please clean the user keys before trying to 
      # assign it to someone else
      cleanuplistlock.acquire()
      try:
        cleanuplist.append(vesselname)
        persist.commit_object(cleanuplist, 'cleanuplist')
      finally:
        cleanuplistlock.release()
      raise

    try:
      # write the vesselmap entry
      DatabaseAPI.write_vesselname_to_vesselmap(vesselname, username, VESSEL_EXPIRE_TIME_SECS)

    except:
      # this vessel has a problem, please clean the user keys before trying to 
      # assign it to someone else
      cleanuplistlock.acquire()
      try:
        cleanuplist.append(vesselname)
        persist.commit_object(cleanuplist, 'cleanuplist')
      finally:
        cleanuplistlock.release()
      raise

  finally:
    thisvessellock.release()





def ExpireVessel(vesselname):
  """
    <Purpose>
      Removes a vessel from a user, adding it to the list for cleanup.

    <Arguments>
      vesselname:
        The vessel to clean-up.   The name is in the format: 
        str(host public key):vesselid

    <Exceptions>
      Exception is raised when the call fails.   The string that is returned
        will give details as to why the call failed.
      ValueError is raised when given invalid input.

    <Side Effects>
      Triggers the cleanup of the vessel.

    <Returns>
      None.
  """

  DEBUGrequestcountdict['ExpireVessel'] = DEBUGrequestcountdict['ExpireVessel'] + 1
  # check that the arguments are valid
  if type(vesselname) != type(''):
    raise ValueError("Invalid vesselname '"+str(vesselname)+"'")



  # get a lock so that there isn't a race to update this vessel...
  thisvessellock = _atomically_getorcreatevessellock(vesselname)

  # lock this vessel...
  thisvessellock.acquire()
  # ... but always release it when done
  try:
    # I need to remove the vesselmap
    DatabaseAPI.remove_vesselname_from_vesselmap(vesselname)

    # add the vessel to the cleanuplist...
    cleanuplistlock.acquire()
    try:
      cleanuplist.append(vesselname)
      persist.commit_object(cleanuplist, 'cleanuplist')
    finally:
      cleanuplistlock.release()

  finally:
    thisvessellock.release()

  


# private.   This will run forever and clean up vessels that we were asked
# to clean up

def _cleanup_vessels():

  while True:

    DEBUGcleanedcount = 0

    # We'll do this forever...
    try:
      for vesselname in cleanuplist[:]:
        try:
          print time.time(),vesselname, "before database api"
          sys.stdout.flush()
          # somehow get the key from the database...
          ownerpublickey, ownerprivatekey = DatabaseAPI.get_ownerkeys_given_vesselname(vesselname)
 
          print time.time(),vesselname, "before database api convert"
          sys.stdout.flush()
          try:
            vesselip, vesselport, vesselid = DatabaseAPI.convert_vesselname_to_ipportid(vesselname)
          except Exception, e:
            print "Horrible internal error!!! '"+str(e)+"'"
            exitall()

          print time.time(),vesselname, "Before change users"
          sys.stdout.flush()
          NodeManagerAPI.dosignedcall(vesselip, vesselport, ownerpublickey, ownerprivatekey, "ChangeUsers", vesselid, '')
          # clean up the vessel state
          print time.time(),vesselname, "Before reset vessel"
          sys.stdout.flush()
          NodeManagerAPI.dosignedcall(vesselip, vesselport, ownerpublickey, ownerprivatekey, "ResetVessel", vesselid)
        except Exception, e:
          print e
          continue

        cleanuplistlock.acquire()
        try:
          cleanuplist.remove(vesselname)
          persist.commit_object(cleanuplist, 'cleanuplist')
        finally:
          cleanuplistlock.release()

        DEBUGcleanedcount = DEBUGcleanedcount + 1

    except Exception, e:
      print "cleanup: ",e
      pass

    if DEBUG: 
      print time.time(),DEBUGcleanedcount, len(cleanuplist), DEBUGrequestcountdict
      sys.stdout.flush()

    sleep(2)





def main():

  # give the database and node manager api a chance to init
  DatabaseAPI.init_database()
  NodeManagerAPI.init_nmapi()

  global cleanuplist
  # get the cleanup data...
  cleanuplist = persist.restore_object('cleanuplist')

  # Register the XMLRPCServer in a threaded manner...
  server = ThreadedXMLRPCServer(("127.0.0.1",LISTENPORT), allow_none=True)

  print "Listening on port "+str(LISTENPORT)+"..."

  settimer(0, _cleanup_vessels, ())
  server.register_multicall_functions()
  server.register_function(AssignVesselToUser, 'AssignVesselToUser')
  server.register_function(ExpireVessel, 'ExpireVessel')

  # Start serving clients
  server.serve_forever()


if __name__ == '__main__':
  main()
