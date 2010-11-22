""" 
Author: Justin Cappos

Module: A shell for Seattle called seash (pronounced see-SHH).   It's not meant
        to be the perfect shell, but it should be good enough for v0.1

Start date: September 18th, 2008

This is an example experiment manager for Seattle.   It allows a user to 
locate vessels they control and manage those vessels.

The design goals of this version are to be secure, simple, and reliable (in 
that order).   

Note: I've written this assuming that repy <-> python integration is perfect
and transparent (minus the bit of mess that fixes this).   As a result this
code may change significantly in the future.

This module is a mess.   The big problem is that we have ~ 30 lines of input
parsing for everything the user does followed by ~ 5 lines of code.   I'm not
sure how to fix this or structure this module to make it cleaner...
"""


# Let's make sure the version of python is supported
import checkpythonversion
checkpythonversion.ensure_python_version_is_supported()

# Armon: Prevent all warnings
import warnings
# Ignores all warnings
warnings.simplefilter("ignore")

# simple client.   A better test client (but nothing like what a real client
# would be)

### Integration fix here...
from repyportability import *


tabcompletion = True
try:

  # Even we can import the readline module successfully, we still disable tab
  # completion in Windows, in response to Ticket #891.
  import os
  if os.name == 'nt':
    raise ImportError

  # Required for the tab completer. It works on Linux and Mac. It does not work
  # on Windows. See http://docs.python.org/library/readline.html for details. 
  import readline
except ImportError:
  print "Auto tab completion is off, because it is not available on your operating system."
  tabcompletion = False
  

import repyhelper

repyhelper.translate_and_import("nmclient_shims.py")

# Following line commented out because time.repy has already been included in
# nmclient_shims.py, a pre-processed version of nmclient with explicity shim
# support, i.e. mycontext['UsingShims'] = True
#repyhelper.translate_and_import("time.repy")

repyhelper.translate_and_import("rsa.repy")

repyhelper.translate_and_import("listops.repy")

repyhelper.translate_and_import("parallelize.repy")

repyhelper.translate_and_import("domainnameinfo.repy")

repyhelper.translate_and_import("advertise.repy")   #  used to do OpenDHT lookups

repyhelper.translate_and_import("geoip_client.repy") # used for `show location`

repyhelper.translate_and_import("serialize.repy") # used for loadstate and savestate

import traceback

import os.path    # fix path names when doing upload, loadkeys, etc.

import sys

#
# Provides tab completion of file names for the CLI, especially when running
# experiments. Able to automatically list file names upon pressing tab, offering
# functionalities similar to thoese of the Unix bash shell. 
#
# Define prefix as the string from the user input before the user hits TAB.
#
# TODO: If the directory or file names contain spaces, tab completion does not
# work. Also works for only Unix-like systems where slash is "/".
#
# Loosely based on http://effbot.org/librarybook/readline.htm
# Mostly written by Danny Y. Huang
#
class TabCompleter:



  # Constructor that initializes all the private variables
  def __init__(self):

    # list of files that match the directory of the given prefix
    self._words = []

    # list of files that match the given prefix
    self._matching_words = []

    self._prefix = None

    

  # Returns the path from a given prefix, by extracting the string up to the
  # last forward slash in the prefix. If no forward slash is found, returns an
  # empty string.
  def _getpath(self, prefix):

    slashpos = prefix.rfind("/")
    currentpath = ""
    if slashpos > -1:
      currentpath = prefix[0 : slashpos+1]

    return currentpath



  # Returns the file name, or a part of the file name, from a given prefix, by
  # extracting the string after the last forward slash in the prefix. If no
  # forward slash is found, returns an empty string.
  def _getfilename(self, prefix):

    # Find the last occurrence of the slash (if any), as it separates the path
    # and the file name.
    slashpos = prefix.rfind("/")
    filename = ""

    # If slash exists and there are characters after the last slash, then the
    # file name is whatever that follows the last slash.
    if slashpos > -1 and slashpos+1 <= len(prefix)-1:
      filename = prefix[slashpos+1:]

    # If no slash is found, then we assume that the entire user input is the
    # prefix of a file name because it does not contain a directory
    elif slashpos == -1:
      filename = prefix

    # If both cases fail, then the entire user input is the name of a
    # directory. Thus, we return the file name as an empty string.

    return filename



  # Returns a list of file names that start with the given prefix.
  def _listfiles(self, prefix):

    # Find the directory specified by the prefix
    currentpath = self._getpath(prefix)
    if not currentpath:
      currentpath = "./"
    filelist = []

    # Attempt to list files from the directory
    try:
      currentpath = os.path.expanduser(currentpath)
      filelist = os.listdir(currentpath)

    except:
      # We are silently dropping all exceptions because the directory specified
      # by the prefix may be incorrect. In this case, we're returning an empty
      # list, similar to what you would get when you TAB a wrong name in the
      # Unix shell.
      pass

    finally:
      return filelist



  # The completer function required as a callback by the readline module. See
  # also http://docs.python.org/library/readline.html#readline.set_completer
  def complete(self, prefix, index):

    # If the user updates the prefix, then we list files that start with the
    # prefix.
    if prefix != self._prefix:

      self._words = self._listfiles(prefix)
      fn = self._getfilename(prefix)

      # Find the files that match the prefix
      self._matching_words = []
      for word in self._words:
        if word.startswith(fn):
          self._matching_words.append(word)

      self._prefix = prefix

    try:
      return self._getpath(prefix) + self._matching_words[index]

    except IndexError:
      return None






#### Helper functions and exception definitions


# this is how long we wait for a node to timeout
globalseashtimeout = 10


# This is the upload rate that we will use to estimate how long it takes for a file to upload.
# Default is left at 10240 bytes/sec (10 kB/sec)
globaluploadrate = 10240
  
# Use this to signal an error we want to print...
class UserError(Exception):
  """This indicates the user typed an incorrect command"""




# Saves the current state to file. Helper method for the savestate
# command. (Added by Danny Y. Huang)
def savestate(statefn, handleinfo, host, port, expnum, filename, cmdargs, 
              defaulttarget, defaultkeyname, autosave, currentkeyname):

  # obtain the handle info dictionary
  for longname in vesselinfo.keys():
    vessel_handle = vesselinfo[longname]['handle']
    handleinfo[longname] = nmclient_get_handle_info(vessel_handle)

  state = {}
  state['targets'] = targets
  state['keys'] = keys
  state['vesselinfo'] = vesselinfo
  state['nextid'] = nextid
  state['handleinfo'] = handleinfo
  state['host'] = host
  state['port'] = port
  state['expnum'] = expnum
  state['filename'] = filename
  state['cmdargs'] = cmdargs
  state['defaulttarget'] = defaulttarget
  state['defaultkeyname'] = defaultkeyname
  state['autosave'] = autosave
  state['globalseashtimeout'] = globalseashtimeout
  state['globaluploadrate'] = globaluploadrate

  # serialize states and encrypt
  if keys.has_key(defaultkeyname):
    cypher = rsa_encrypt(serialize_serializedata(state), keys[currentkeyname]['publickey'])
  else:
    raise Exception("The keyname '" + defaultkeyname + "' is not loaded.")

  # writing encrypted serialized states to file
  try:
    state_obj = open(statefn, 'w')
    state_obj.write(cypher)
  except:
    raise Exception("Error writing to state file '" + statefn + "'.")
  finally:
    state_obj.close()



def is_immutable_targetname(targetname):
  if targetname.startswith('%') or ':' in targetname:
    return True
  return False


def valid_targetname(targetname):
  if targetname.startswith('%') or ':' in targetname or ' ' in targetname:
    return False
  return True


def fit_string(stringdata, length):
  if len(stringdata) > length:
    return stringdata[:length-3]+'...'
  return stringdata


nextidlock = getlock()
def atomically_get_nextid():
  global nextid

  # mutex around getting an id
  nextidlock.acquire()

  myid = nextid
  nextid = nextid + 1

  nextidlock.release()

  return myid
    
  

# adds a vessel and returns the new ID...
def add_vessel(longname, keyname, vesselhandle):
  vesselinfo[longname] = {}
  vesselinfo[longname]['handle'] = vesselhandle
  vesselinfo[longname]['keyname'] = keyname
  vesselinfo[longname]['IP'] = longname.split(':')[0]
  vesselinfo[longname]['port'] = int(longname.split(':')[1])
  vesselinfo[longname]['vesselname'] = longname.split(':')[2]
  # miscelaneous information about the vessel (version, nodeID, etc.)
  vesselinfo[longname]['information'] = {}
  
  # set up a reference to myself...
  targets[longname] = [longname]

  myid = atomically_get_nextid()

  # add my id...
  targets['%'+str(myid)] = [longname]
  vesselinfo[longname]['ID'] = '%'+str(myid)

  # add me to %all...
  targets['%all'].append(longname)

  return myid




def copy_vessel(longname, newvesselname):
  newhandle = nmclient_duplicatehandle(vesselinfo[longname]['handle'])
  newlongname = vesselinfo[longname]['IP']+":"+str(vesselinfo[longname]['port'])+":"+newvesselname
  add_vessel(newlongname,vesselinfo[longname]['keyname'],newhandle)
  return newlongname

def delete_vessel(longname):
  # remove the item...
  del vesselinfo[longname]

  # remove the targets that reference it...
  for target in targets.copy():
    # if in my list...
    if longname in targets[target]:
      # if this is the %num entry or longname entry...
      if ('%' in target and target != '%all') or longname == target:
        del targets[target]
        continue
      # otherwise remove the item from the list...
      targets[target].remove(longname)



def longnamelist_to_nodelist(longnamelist):
  
  retlist = []
  for longname in longnamelist:
    nodename = vesselinfo[longname]['IP']+":"+str(vesselinfo[longname]['port'])
    retlist.append(nodename)

  return retlist


def find_handle_for_node(nodename):
  
  for longname in vesselinfo:
    if longname.rsplit(':',1)[0] == nodename:
      return vesselinfo[longname]['handle']
  raise IndexError("Cannot find handle for '"+nodename+"'")


# determines if there's a need to temporarily change the vessel timeout
# to avoid timing out on bad connection speeds when uploading file.
def set_upload_timeout(filedata):

  filesize = len(filedata)
  est_upload_time = filesize / globaluploadrate

  # sets the new timeout if necessary
  if est_upload_time > globalseashtimeout:

    for longname in vesselinfo:
      thisvesselhandle = vesselinfo[longname]['handle']
      thisvesselhandledict = nmclient_get_handle_info(thisvesselhandle)
      thisvesselhandledict['timeout'] = est_upload_time
      nmclient_set_handle_info(thisvesselhandle,thisvesselhandledict)


# Resets each vessel's timeout to globalseashtimeout
def reset_vessel_timeout():

  # resets each vessel's timeout to the original values before file upload
  for longname in vesselinfo:
    thisvesselhandle = vesselinfo[longname]['handle']
    thisvesselhandledict = nmclient_get_handle_info(thisvesselhandle)
    thisvesselhandledict['timeout'] = globalseashtimeout
    nmclient_set_handle_info(thisvesselhandle,thisvesselhandledict)


#################### functions that operate on a target

MAX_CONTACT_WORKER_THREAD_COUNT = 10


# This function abstracts out contacting different nodes.   It spawns off 
# multiple worker threads to handle the clients...
# by a threaded model in the future...
# NOTE: entries in targetlist are assumed by me to be unique
def contact_targets(targetlist, func,*args):
  
  phandle = parallelize_initfunction(targetlist, func, MAX_CONTACT_WORKER_THREAD_COUNT, *args)

  while not parallelize_isfunctionfinished(phandle):
    sleep(.1)
  
  # I'm going to change the format slightly...
  resultdict = parallelize_getresults(phandle)

  # There really shouldn't be any exceptions in any of the routines...
  if resultdict['exception']:
    print "WARNING: ",resultdict['exception']

  # I'm going to convert the format to be targetname (as the key) and 
  # a value with the return value...
  retdict = {}
  for nameandretval in resultdict['returned']:
    retdict[nameandretval[0]] = nameandretval[1]

  return retdict
    

    

# This function abstracts out contacting different nodes.   It is obsoleted by
# the threaded model...   This code is retained for testing reasons only
def simple_contact_targets(targetlist, func,*args):
  retdict = {}

  # do the function on each target, returning a dict of results.
  for target in targetlist:
    retdict[target] = func(target,*args)

  return retdict
    



# used in show files
def showfiles_target(longname):
  vesselname = vesselinfo[longname]['vesselname']
  try:
    filedata = nmclient_signedsay(vesselinfo[longname]['handle'],"ListFilesInVessel",vesselname)
  except NMClientException, e:
    return (False, str(e))
  else:
    return (True, filedata)








# used in show log
def showlog_target(longname):
  vesselname = vesselinfo[longname]['vesselname']
  try:
    logdata = nmclient_signedsay(vesselinfo[longname]['handle'],"ReadVesselLog",vesselname)
  except NMClientException, e:
    return (False, str(e))
  else:
    return (True, logdata)





# used in show resources
def showresources_target(longname):
  vesselname = vesselinfo[longname]['vesselname']
  try:
    resourcedata = nmclient_rawsay(vesselinfo[longname]['handle'],"GetVesselResources",vesselname)
  except NMClientException, e:
    return (False, str(e))
  else:
    return (True, resourcedata)


# used in show offcut
def showoffcut_target(nodename):
  vesselhandle = find_handle_for_node(nodename)
  try:
    offcutdata = nmclient_rawsay(vesselhandle,"GetOffcutResources")
  except NMClientException, e:
    return (False, str(e))
  else:
    return (True, offcutdata)
  




def browse_target(node, currentkeyname):

  # NOTE: I almost think I should skip those nodes that I know about from 
  # previous browse commands.   Perhaps I should have an option on the browse
  # command?

  host, portstring = node.split(':')
  port = int(portstring)

  # get information about the node's vessels
  try:
    nodehandle = nmclient_createhandle(host, port, privatekey = keys[currentkeyname]['privatekey'], publickey = keys[currentkeyname]['publickey'], timeout=globalseashtimeout)
  except NMClientException,e:
    return (False, str(e))

  try:
    # need to contact the node to get the list of vessels we can perform
    # actions on...
    ownervessels, uservessels = nmclient_listaccessiblevessels(nodehandle,keys[currentkeyname]['publickey'])

    retlist = []

    # we should add anything we can access (whether a user or owner vessel)
    for vesselname in ownervessels + uservessels:
      longname = host+":"+str(port)+":"+vesselname

      # if we haven't discovered the vessel previously...
      if longname not in targets:
        # set the vesselname in the handle
        newhandle = nmclient_duplicatehandle(nodehandle)
        handleinfo = nmclient_get_handle_info(newhandle)
        handleinfo['vesselname'] = vesselname
        nmclient_set_handle_info(newhandle, handleinfo)

        # then add the vessel to the target list, etc.
        # add_vessel has no race conditions as long as longname is unique 
        # (and it should be unique)
        id = add_vessel(longname,currentkeyname,newhandle)
        targets['browsegood'].append(longname)

        # and append some information to be printed...
        retlist.append('%'+str(id)+"("+longname+")")



  finally:
    nmclient_destroyhandle(nodehandle)

  return (True, retlist)


def list_or_update_target(longname):

  vesselname = vesselinfo[longname]['vesselname']
  try:
    vesseldict = nmclient_getvesseldict(vesselinfo[longname]['handle'])
  except NMClientException, e:
    return (False, str(e))
  else:
    # updates the dictionary of our node information (dictionary used in show, 
    # etc.)
    for key in vesseldict['vessels'][vesselname]:
      vesselinfo[longname][key] = vesseldict['vessels'][vesselname][key]

    # Update the "information" (version number, etc.)
    del vesseldict['vessels']
    vesselinfo[longname]['information'] = vesseldict

    return (True,)


def upload_target(longname, remotefn, filedata):
  vesselname = vesselinfo[longname]['vesselname']
  try:
    # add the file data...
    nmclient_signedsay(vesselinfo[longname]['handle'], "AddFileToVessel", vesselname, remotefn, filedata)
  except NMClientException, e:
    return (False, str(e))
  else:
    return (True,)


def download_target(longname,localfn,remotefn):
  vesselname = vesselinfo[longname]['vesselname']
  try:
    # get the file data...
    retrieveddata = nmclient_signedsay(vesselinfo[longname]['handle'], "RetrieveFileFromVessel", vesselname, remotefn)

  except NMClientException, e:
    return (False, str(e))

  else:
    writefn = localfn+"."+longname.replace(':','_')
    # write to the local filename (replacing ':' with '_')...
    fileobj = open(writefn,"w")
    fileobj.write(retrieveddata)
    fileobj.close()
    # for output...
    return (True, writefn)



def delete_target(longname,remotefn):
  vesselname = vesselinfo[longname]['vesselname']
  try:
    # delete the file...
    nmclient_signedsay(vesselinfo[longname]['handle'], "DeleteFileInVessel", vesselname, remotefn)

  except NMClientException, e:
    return (False, str(e))

  else:
    return (True,)


def start_target(longname, argstring):
  vesselname = vesselinfo[longname]['vesselname']
  try:
    # start the program
    nmclient_signedsay(vesselinfo[longname]['handle'], "StartVessel", vesselname, argstring)

  except NMClientException, e:
    return (False, str(e))

  else:
    return (True,)


def stop_target(longname):
  vesselname = vesselinfo[longname]['vesselname']
  try:
    # stop the programs
    nmclient_signedsay(vesselinfo[longname]['handle'], "StopVessel", vesselname)
  except NMClientException, e:
    return (False, str(e))

  else:
    return (True,)


def reset_target(longname):
  vesselname = vesselinfo[longname]['vesselname']
  try:
    # reset the target
    nmclient_signedsay(vesselinfo[longname]['handle'], "ResetVessel", vesselname)
  except NMClientException, e:
    return (False, str(e))
  else:
    return (True,)


def run_target(longname,filename,filedata, argstring):
  vesselname = vesselinfo[longname]['vesselname']
  try:
    nmclient_signedsay(vesselinfo[longname]['handle'], "AddFileToVessel", vesselname, filename, filedata)
    nmclient_signedsay(vesselinfo[longname]['handle'], "StartVessel", vesselname, argstring)
  except NMClientException, e:
    return (False, str(e))
  else:
    return (True,)



# didn't test...
def split_target(longname, resourcedata):
  vesselname = vesselinfo[longname]['vesselname']
  try:
    newvesselnames = nmclient_signedsay(vesselinfo[longname]['handle'], "SplitVessel", vesselname, resourcedata)
  except NMClientException, e:
    return (False, str(e))
  else:
    newname1 = copy_vessel(longname, newvesselnames.split()[0])
    newname2 = copy_vessel(longname, newvesselnames.split()[1])
    delete_vessel(longname)
    return (True,(newname1,newname2))


# didn't test...
def join_target(nodename,nodedict):
 
  if len(nodedict[nodename]) < 2:
    # not enough vessels, nothing to do
    return (False, None)
            

  # I'll iterate through the vessels, joining one with the current 
  # (current starts as the first vessel and becomes the "new vessel")
  currentvesselname = vesselinfo[nodedict[nodename][0]]['vesselname']
  currentlongname = nodedict[nodename][0]

  # keep a list of what I replace...
  subsumedlist = [currentlongname]

  for longname in nodedict[nodename][1:]:
    vesselname = vesselinfo[longname]['vesselname']
    try:
      newvesselname = nmclient_signedsay(vesselinfo[longname]['handle'], "JoinVessels", currentvesselname, vesselname)
    except NMClientException, e:
      return (False, str(e))
    else:
      newname = copy_vessel(longname, newvesselname)
      delete_vessel(longname)
      delete_vessel(currentlongname)
      subsumedlist.append(longname)
      currentlongname = newname
      currentvesselname = newvesselname
  else:
    return (True, (currentlongname,subsumedlist))



# didn't test...
def setowner_target(longname,newowner):
  vesselname = vesselinfo[longname]['vesselname']
  try:
    nmclient_signedsay(vesselinfo[longname]['handle'], "ChangeOwner", vesselname, rsa_publickey_to_string(keys[newowner]['publickey']))
  except NMClientException, e:
    return (False, str(e))
  else:
    return (True,)
  


# didn't test...
def setadvertise_target(longname,newadvert):
  vesselname = vesselinfo[longname]['vesselname']
  try:
    # do the actual advertisement changes
    nmclient_signedsay(vesselinfo[longname]['handle'], "ChangeAdvertise", vesselname, newadvert)
  except NMClientException, e:
    return (False, str(e))
  else:
    return (True,)
  

def setownerinformation_target(longname,newownerinformation):
  vesselname = vesselinfo[longname]['vesselname']
  try:
    # do the actual advertisement changes
    nmclient_signedsay(vesselinfo[longname]['handle'], "ChangeOwnerInformation", vesselname, newownerinformation)
  except NMClientException, e:
    return (False, str(e))
  else:
    return (True,)
  

def setusers_target(longname,userkeystring):
  vesselname = vesselinfo[longname]['vesselname']
  try:
    nmclient_signedsay(vesselinfo[longname]['handle'], "ChangeUsers", vesselname, userkeystring)
  except NMClientException, e:
    return (False, str(e))
  else:
    return (True,)




# Checks if both keys are setup
def check_key_set(name):
  if (name in keys and 'publickey' in keys[name] and 'privatekey' in keys[name] and keys[name]['publickey'] and keys[name]['privatekey']):
    if not check_key_pair_compatibility(name):
      raise UserError("Error: Mis-matched Public/Private key pair!")

# Check the keys to make sure they are compatible, for the given name
def check_key_pair_compatibility(name):
   # Check for both sets of keys
    setPublic = keys[name]['publickey']
    setPrivate = keys[name]['privatekey']
    
    # Check for a mis-match
    match = rsa_matching_keys(setPrivate, setPublic)
    
    return match


# Reload the handles of a node. Used when "loadstate" is invoked. Returns a
# tuple (success, e), where success is a boolean and e is a string of error
# messages. Added by Danny Y. Huang.
def reload_target(longname, handleinfo):
  host, portstring, vesselname = longname.split(':')
  port = int(portstring)

  try:
    priKey = handleinfo[longname]['privatekey']
    pubKey = handleinfo[longname]['publickey']
  except KeyError:
    error = ("Vessel is absent in the handleinfo dictionary.")
    return (False, error)

  # find the user who has these keys
  thiskeyname = ""
  for keyname in keys.keys():
    if (keys[keyname]['publickey'] == pubKey and
        keys[keyname]['privatekey'] == priKey):
      thiskeyname = keyname
      break
  if not thiskeyname:
    return (False, "User with keyname '" + keyname + "' is not found.")

  # create new handle for the vessel
  try:
    vessel_handle = nmclient_createhandle(host, port, privatekey = priKey, publickey = pubKey, timeout=globalseashtimeout)
  except NMClientException, error:
    return (False, str(error))

  try:
    nmclient_set_handle_info(vessel_handle, handleinfo[longname])
    vesselinfo[longname]['handle'] = vessel_handle

    # hello test to see if the vessel is available
    (ownervessels, uservessels) = nmclient_listaccessiblevessels(vessel_handle, pubKey)
    if not (ownervessels + uservessels):
      return (False, "Vessel is not available for keyname " + keyname + ".")

  except Exception, error:
    # Catching unexpected exceptions
    return (False, "General exception: " + str(error) + ".")

  return (True, "")

#################### main loop and variables.
  
# a dict that contains all of the targets (vessels and groups) we know about.
targets = {'%all':[]}

# stores information about the vessels...
vesselinfo = {}

# the nextid that should be used for a new target.
nextid = 1

# a dict that contains all of the key information
keys = {}



# The usual way of handling a user request is:
#   1) parse the arguments the user gives (I do this up front so that I can
#      give intelligible error messages before doing any work)
#   2) handle the request.   If the request can be handled with local data, 
#      it does so.   Otherwise, contact_targets is called with the list of
#      of targets.   (targets are usually either nodenames or longnames)
#   3) provide output to the user informing them of what happened.   It is
#      common to create groups for the user if different targets have different
#      outcomes
#
# Steps 1 and 3 are always done inline (inflating the function length).   Step
# 2 is commonly done by a function XXX_target(...) listed above

def command_loop():
  # we will set this if they call set timeout
  global globalseashtimeout
  global globaluploadrate

  global targets
  global vesselinfo
  global nextid
  global keys

  # things that may be set herein and used in later commands
  host = None
  port = None
  expnum = None
  filename = None
  cmdargs = None
  defaulttarget = None
  defaultkeyname = None
  handleinfo = {}

  # whether to save the last state after every command
  autosave = False


  # Set up the tab completion environment (Added by Danny Y. Huang)
  if tabcompletion:
    completer = TabCompleter()
    readline.parse_and_bind("tab: complete")
    readline.set_completer_delims(" ")
    readline.set_completer(completer.complete)


  # exit via a return
  while True:

    try:
      
      
      # Saving state after each command? (Added by Danny Y. Huang)
      if autosave and defaultkeyname:
        try:
          # State is saved in file "autosave_username", so that user knows which
          # RSA private key to use to reload the state.
          autosavefn = "autosave_" + str(defaultkeyname)
          savestate(autosavefn, handleinfo, host, port, expnum, filename, 
                    cmdargs, defaulttarget, defaultkeyname, autosave, defaultkeyname)
        except Exception, error:
          raise UserError("There is an error in autosave: '" + str(error) + "'. You can turn off autosave using the command 'set autosave off'.")


      prompt = ''
      if defaultkeyname:
        prompt = fit_string(defaultkeyname,20)+"@"

      # display the thing they are acting on in their prompt (if applicable)
      if defaulttarget:
        prompt = prompt + fit_string(defaulttarget,20)

      prompt = prompt + " !> "
      # the prompt should look like: justin@good !> 

      # get the user input
      userinput = raw_input(prompt)

      userinput = userinput.strip()

      userinputlist = userinput.split()
      if len(userinputlist)==0:
        continue

      # by default, use the target specified in the prompt
      currenttarget = defaulttarget

      # set the target, then handle other operations
      if len(userinputlist) >= 2:
        if userinputlist[0] == 'on':
          if userinputlist[1] not in targets:
            raise UserError("Error: Unknown target '"+userinputlist[1]+"'")
          # set the target and strip the rest...
          currenttarget = userinputlist[1]
          userinputlist = userinputlist[2:]

          # they are setting the default
          if len(userinputlist) == 0:
            defaulttarget = currenttarget
            continue

      # by default, use the identity specified in the prompt
      currentkeyname = defaultkeyname

      # set the keys, then handle other operations
      if len(userinputlist) >= 2:
        if userinputlist[0] == 'as':
          if userinputlist[1] not in keys:
            raise UserError("Error: Unknown identity '"+userinputlist[1]+"'")
            
          # set the target and strip the rest...
          currentkeyname = userinputlist[1]
          userinputlist = userinputlist[2:]

          # they are setting the default
          if len(userinputlist) == 0:
            defaultkeyname = currentkeyname
            continue





# help or ?
      if userinputlist[0] == 'help' or userinputlist[0] == '?':
        if len(userinputlist) == 1:
          print \
"""
A target can be either a host:port:vesselname, %ID, or a group name.

on target [command] -- Runs a command on a target (or changes the default)
as keyname [command]-- Run a command using an identity (or changes the default).
add [target] [to group]      -- Adds a target to a new or existing group 
remove [target] [from group] -- Removes a target from a group
show                -- Displays shell state (use 'help show' for more info)
set                 -- Changes the state of the targets (use 'help set')
browse              -- Find vessels I can control
genkeys fn [len] [as identity] -- creates new pub / priv keys (default len=1024)
loadkeys fn [as identity]   -- loads filename.publickey and filename.privatekey
list               -- Update and display information about the vessels
upload localfn (remotefn)   -- Upload a file 
download remotefn (localfn) -- Download a file 
delete remotefn             -- Delete a file
reset                  -- Reset the vessel (clear the log and files and stop)
run file [args ...]    -- Shortcut for upload a file and start
start file [args ...] -- Start an experiment
stop               -- Stop an experiment
split resourcefn            -- Split another vessel off of each vessel
join                        -- Join vessels on the same node
help [help | set | show ]    -- help information 
exit                         -- exits the shell
loadstate fn -- Load saved states from a local file. One must call 'loadkeys 
                 username' and 'as username' first before loading the states,
                 so seash knows whose RSA keys to use in deciphering the state
                 file.
savestate fn -- Save the current state information to a local file.
"""
#!resourcedata                -- List resource information about the vessel

        else:
          if userinputlist[1] == 'set':
            print \
"""set users [ identity ... ]  -- Change a vessel's users
set ownerinfo [ data ... ]    -- Change owner information for the vessels
set advertise [ on | off ] -- Change advertisement of vessels
set owner identity        -- Change a vessel's owner
set timeout count  -- Sets the time that seash is willing to wait on a node
set uploadrate speed -- Sets the upload rate which seash will use to estimate
                        the time needed for a file to be uploaded to a vessel.
                        The estimated time would be set as the temporary 
                        timeout count during actual process. Speed should be 
                        in bytes/sec.
set autosave [ on | off ] -- Sets whether to save the state after every command.
                             Set to 'off' by default. The state is saved to a
                             file called 'autosave_keyname', where keyname is 
                             the name of the current key you're using.
"""


          elif userinputlist[1] == 'show':
            print \
"""
show info       -- Display general information about the vessels
show users      -- Display the user keys for the vessels
show ownerinfo  -- Display owner information for the vessels
show advertise  -- Display advertisement information about the vessels
show ip [to file] -- Display the ip addresses of the nodes
show hostname   -- Display the hostnames of the nodes
show location   -- Display location information (countries) for the nodes
show coordinates -- Display the latitude & longitude of the nodes
show owner      -- Display a vessel's owner
show targets    -- Display a list of targets
show identities -- Display the known identities
show keys       -- Display the known keys
show log [to file] -- Display the log from the vessel (*)
show files      -- Display a list of files in the vessel (*)
show resources  -- Display the resources / restrictions for the vessel (*)
show offcut     -- Display the offcut resource for the node (*)
show timeout    -- Display the timeout for nodes
show uploadrate -- Display the upload rate which seash uses to estimate
                   the required time for a file upload

(*) No need to update prior, the command contacts the nodes anew
"""


          elif userinputlist[1] == 'help':
            print \
"""
Extended commands (not commonly used):

loadpub fn [as identity]    -- loads filename.publickey 
loadpriv fn [as identity]   -- loads filename.privatekey
move target to group        -- Add target to group, remove target from default
contact host:port[:vessel] -- Communicate with a node
update             -- Update information about the vessels
"""
          else:
            raise UserError("Usage: help [ set | show ] -- display help")


        continue





# exit, quit, bye
      elif userinputlist[0] == 'exit' or userinputlist[0] == 'quit' or userinputlist[0] == 'bye':
        return







# show   (lots to do here)
      elif userinputlist[0] == 'show':
        if len(userinputlist) == 1:
          # What do I show?
          pass

# show info       -- Display general information about the vessels
        elif userinputlist[1] == 'info' or userinputlist[1] == 'information':
          if not currenttarget:
            raise UserError("Error, command requires a target")

          for longname in targets[currenttarget]:
            if vesselinfo[longname]['information']:
              print longname, vesselinfo[longname]['information']
            else:
              print longname, "has no information (try 'update' or 'list')"


# show targets    -- Display a list of targets
        elif userinputlist[1] == 'targets' or userinputlist[1] == 'groups':
          for target in targets:
            if len(targets[target]) == 0:
              print target, "(empty)"
              continue
            # this is a vesselentry
            if target == targets[target][0]:
              continue
            print target, targets[target]


# show keys       -- Display the known keys
        elif userinputlist[1] == 'keys':
          for identity in keys:
            print identity,keys[identity]['publickey'],keys[identity]['privatekey']




# show identities -- Display the known identities
        # catch a common typo
        elif userinputlist[1] == 'identities' or userinputlist[1] == 'identites':
          for keyname in keys:
            print keyname,
            if keys[keyname]['publickey']:
              print "PUB",
            if keys[keyname]['privatekey']:
              print "PRIV",
            print



# show users      -- Display the user keys for the vessels
        elif userinputlist[1] == 'users':
          if not currenttarget:
            raise UserError("Error, command requires a target")

          for longname in targets[currenttarget]:
            if 'userkeys' in vesselinfo[longname]:
              if vesselinfo[longname]['userkeys'] == []:
                print longname,"(no keys)"
                continue

              print longname,
              # we'd like to say 'joe's public key' instead of '3453 2323...'
              for key in vesselinfo[longname]['userkeys']:
                for identity in keys:
                  if keys[identity]['publickey'] == key:
                    print identity,
                    break
                else:
                  print fit_string(rsa_publickey_to_string(key),15),
              print
            else:
              print longname, "has no information (try 'update' or 'list')"

          continue

# show ownerinfo  -- Display owner information for the vessels
        elif userinputlist[1] == 'ownerinfo':
          if not currenttarget:
            raise UserError("Error, command requires a target")

          for longname in targets[currenttarget]:
            if 'ownerinfo' in vesselinfo[longname]:
              print longname, "'"+vesselinfo[longname]['ownerinfo']+"'"
              # list all of the info...
            else:
              print longname, "has no information (try 'update' or 'list')"

          continue

# show advertise  -- Display advertisement information about the vessels
        elif userinputlist[1] == 'advertise':
          if not currenttarget:
            raise UserError("Error, command requires a target")

          for longname in targets[currenttarget]:
            if 'advertise' in vesselinfo[longname]:
              if vesselinfo[longname]['advertise']:
                print longname, "on"
              else:
                print longname, "off"
              # list all of the info...
            else:
              print longname, "has no information (try 'update' or 'list')"

          continue


# show owner      -- Display a vessel's owner
        elif userinputlist[1] == 'owner':
          if not currenttarget:
            raise UserError("Error, command requires a target")

          for longname in targets[currenttarget]:
            if 'ownerkey' in vesselinfo[longname]:
              # we'd like to say 'joe public key' instead of '3453 2323...'
              ownerkey = vesselinfo[longname]['ownerkey']
              for identity in keys:
                if keys[identity]['publickey'] == ownerkey:
                  print longname, identity+" pubkey"
                  break
              else:
                print longname, fit_string(rsa_publickey_to_string(ownerkey),15)
            else:
              print longname, "has no information (try 'update' or 'list')"

          continue



# show files      -- Display a list of files in the vessel (*)
        elif userinputlist[1] == 'file' or userinputlist[1] == 'files':

          if not currenttarget:
            raise UserError("Error, command requires a target")

          # print the list of files in the vessels...
          retdict = contact_targets(targets[currenttarget], showfiles_target)

          goodlist = []
          faillist = []
          for longname in retdict:
            # True means it worked
            if retdict[longname][0]:
              print "Files on '"+longname+"': '"+retdict[longname][1]+"'"
              goodlist.append(longname)
            else:
              print "failure on '"+longname+"': '"+retdict[longname][1]+"'"
              faillist.append(longname)
  
          # and display it...
          if faillist:
            print "Failures on "+str(len(faillist))+" targets: "+", ".join(faillist)
          if goodlist and faillist:
            targets['filesgood'] = goodlist
            targets['filesfail'] = faillist
            print "Added group 'filesgood' with "+str(len(targets['filesgood']))+" targets and 'filesfail' with "+str(len(targets['filesfail']))+" targets"

          continue






# show log [to file] -- Display the log from the vessel (*)
        elif userinputlist[1] == 'log' or userinputlist[1] == 'logs':
          if len(userinputlist) == 2:
            writeoutputtofile = False
          elif len(userinputlist) == 4 and (userinputlist[2] == 'to' or userinputlist[2] == 'TO' or userinputlist[2] == '>'):
            writeoutputtofile = True
            # handle '~'
            fileandpath = os.path.expanduser(userinputlist[3])
            outputfileprefix = fileandpath
          else:
            raise UserError("Error, format is 'show log' or 'show log to filenameprefix'")
            

          if not currenttarget:
            raise UserError("Error, command requires a target")

          # print the vessel logs...
          retdict = contact_targets(targets[currenttarget], showlog_target)

          goodlist = []
          faillist = []
          for longname in retdict:
            # True means it worked
            if retdict[longname][0]:
              if writeoutputtofile:
                # write to a file if requested.
                outputfilename = outputfileprefix +'.'+ longname
                outputfo = file(outputfilename,'w')
                outputfo.write(retdict[longname][1])
                outputfo.close()
                print "Wrote log as '"+outputfilename+"'."

              else:
                # else print it to the terminal
                print "Log from '"+longname+"':"
                print retdict[longname][1]

              # regardless, this is a good node
              goodlist.append(longname)

            else:
              print "failure on '"+longname+"': ",retdict[longname][1]
              faillist.append(longname)
  
          # and display it...
          if faillist:
            print "Failures on "+str(len(faillist))+" targets: "+", ".join(faillist)
          if goodlist and faillist:
            targets['loggood'] = goodlist
            targets['logfail'] = faillist
            print "Added group 'loggood' with "+str(len(targets['loggood']))+" targets and 'logfail' with "+str(len(targets['logfail']))+" targets"

          continue




# show resources  -- Display the resources / restrictions for the vessel (*)
        elif userinputlist[1] == 'resource' or userinputlist[1] == 'resources':

          if not currenttarget:
            raise UserError("Error, command requires a target")

          retdict = contact_targets(targets[currenttarget], showresources_target)
          faillist = []
          goodlist = []
          for longname in retdict:
            # True means it worked
            if retdict[longname][0]:
              print "Resource data for '"+longname+"':"
              print retdict[longname][1]
              goodlist.append(longname)
            else:
              print "Failure '"+longname+"':",retdict[longname][1]
              faillist.append(longname)
  
          # and display it...
          if faillist:
            print "Failures on "+str(len(faillist))+" targets: "+", ".join(faillist)
          if goodlist and faillist:
            targets['resourcegood'] = goodlist
            targets['resourcefail'] = faillist
            print "Added group 'resourcegood' with "+str(len(targets['resourcegood']))+" targets and 'resourcefail' with "+str(len(targets['resourcefail']))+" targets"

          continue



# show offcut     -- Display the offcut resource for the node (*)
        elif userinputlist[1] == 'offcut':

          if not currenttarget:
            raise UserError("Error, command requires a target")

          
          # we should only visit a node once...
          nodelist = listops_uniq(longnamelist_to_nodelist(targets[currenttarget]))
          retdict = contact_targets(nodelist, showoffcut_target)

          for nodename in retdict:
            if retdict[nodename][0]:
              print "Offcut resource data for '"+nodename+"':"
              print retdict[nodename][1]
            else:
              print "Failure '"+nodename+"':",retdict[longname][1]
  
          continue



# show ip [to file] -- Display the ip addresses of the nodes
        # catch a misspelling
        elif userinputlist[1] == 'ip' or userinputlist[1] == 'ips':

          if not currenttarget:
            raise UserError("Error, command requires a target")

          # print to the terminal (stdout)
          if len(userinputlist) == 2:
            # write data here...
            outfo = sys.stdout

          # print to a file
          elif len(userinputlist) == 4:
            
            if not (userinputlist[2] == 'to' or userinputlist[2] == 'TO' or 
                userinputlist[2] == '>'):
              raise UserError("Usage: show ip [to filename]")
            outfo = open(userinputlist[3],"w+")

          # bad input...
          else:
            raise UserError("Usage: show ip [to filename]")

          
          # we should only visit a node once...
          printedIPlist = []
          for longname in targets[currenttarget]:
            thisnodeIP = vesselinfo[longname]['IP']

            if thisnodeIP not in printedIPlist:
              printedIPlist.append(thisnodeIP)
              print >> outfo, thisnodeIP
  
          # if it's a file, close it...
          if len(userinputlist) == 4:
            outfo.close()

          continue

# show hostname        -- Display the hostnames of the nodes
        # catch a misspelling
        elif userinputlist[1] == 'hostnames' or userinputlist[1] == 'hostname' or userinputlist[1] == 'host' or userinputlist[1] == 'hosts':

          if not currenttarget:
            raise UserError("Error, command requires a target")

          
          # we should only visit a node once...
          printedIPlist = []
          for longname in targets[currenttarget]:
            thisnodeIP = vesselinfo[longname]['IP']

            if thisnodeIP not in printedIPlist:
              printedIPlist.append(thisnodeIP)
              print thisnodeIP,
              try: 
                nodeinfo = socket.gethostbyaddr(thisnodeIP)
              except (socket.herror,socket.gaierror, socket.timeout, socket.error):
                print 'has unknown host information'
              else:
                print 'is known as',nodeinfo[0]
  
          continue



# show location        -- Display location information about the nodes
        # catch a misspelling
        elif userinputlist[1] == 'locations' or userinputlist[1] == 'location':

          if not currenttarget:
            raise UserError("Error, command requires a target")

          geoip_init_client()
          
          # we should only visit a node once...
          printedIPlist = []

          for longname in targets[currenttarget]:
            thisnodeIP = vesselinfo[longname]['IP']

            # if we haven't visited this node
            if thisnodeIP not in printedIPlist:
              printedIPlist.append(thisnodeIP)
              location_dict = geoip_record_by_addr(thisnodeIP)
              if location_dict:
                print str(vesselinfo[longname]['ID'])+'('+str(thisnodeIP)+'): '+geoip_location_str(location_dict)
              else:
                print str(vesselinfo[longname]['ID'])+'('+str(thisnodeIP)+'): Location unknown'
              
          continue

        

#show coordinates -- Display the latitude & longitude of the nodes
        elif userinputlist[1] == 'coordinates':
          if not currenttarget:
            raise UserError("Error, command requires a target")

          geoip_init_client()
          
          # we should only visit a node once...
          printedIPlist = []

          for longname in targets[currenttarget]:
            thisnodeIP = vesselinfo[longname]['IP']

            # if we haven't visited this node
            if thisnodeIP not in printedIPlist:
              printedIPlist.append(thisnodeIP)
              location_dict = geoip_record_by_addr(thisnodeIP)
              if location_dict:
                print str(vesselinfo[longname]['ID'])+'('+str(thisnodeIP)+'): ' + str(location_dict['latitude']) + ", " + str(location_dict['longitude'])
              else:
                print str(vesselinfo[longname]['ID'])+'('+str(thisnodeIP)+'): Location unknown'

          continue



# show timeout    -- Display the timeout for nodes
        elif userinputlist[1] == 'timeout' or userinputlist[1] == 'timeouts':

          print globalseashtimeout
          
          continue



# show uploadrate -- Display the upload rate for file transfers to nodes
        elif userinputlist[1] == 'uploadrate':

          print globaluploadrate

          continue







# show ???      -- oops!
        else:
          raise UserError("Error in usage: try 'help show'")
        continue






# add (target) (to group)
      elif userinputlist[0] == 'add':
        if len(userinputlist) == 2:
          source = userinputlist[1]
          dest = currenttarget

        elif len(userinputlist) == 3:
          source = currenttarget
          if userinputlist[1] != 'to':
            raise UserError("Error, command format: add (target) (to group)")
          dest = userinputlist[2]

        elif len(userinputlist) == 4:
          source = userinputlist[1]
          if userinputlist[2] != 'to':
            raise UserError("Error, command format: add (target) (to group)")
          dest = userinputlist[3]

        else:
          raise UserError("Error, command format: add (target) (to group)")
 
        # okay, now source and dest are set.   Time to add the nodes in source
        # to the group dest...
        if source not in targets:
          raise UserError("Error, unknown target '"+source+"'")
        if dest not in targets:
          if not valid_targetname(dest):
            raise UserError("Error, invalid target name '"+dest+"'")
          targets[dest] = []

        if is_immutable_targetname(dest):
          raise UserError("Can't modify the contents of '"+dest+"'")

        # source - dest has what we should add (items in source but not dest)
        addlist = listops_difference(targets[source],targets[dest])
        if len(addlist) == 0:
          raise UserError("No targets to add (the target is already in '"+dest+"')")
        
        for item in addlist:
          targets[dest].append(item)
        continue







# remove (target) (from group)
      elif userinputlist[0] == 'remove':
        if len(userinputlist) == 2:
          source = userinputlist[1]
          dest = currenttarget

        elif len(userinputlist) == 3:
          source = currenttarget
          if userinputlist[1] != 'from':
            raise UserError("Error, command format: remove (target) (from group)")
          dest = userinputlist[2]

        elif len(userinputlist) == 4:
          source = userinputlist[1]
          if userinputlist[2] != 'from':
            raise UserError("Error, command format: remove (target) (from group)")
          dest = userinputlist[3]

        else:
          raise UserError("Error, command format: remove (target) (from group)")
 
        # time to check args and do the ops
        if source not in targets:
          raise UserError("Error, unknown target '"+source+"'")
        if dest not in targets:
          raise UserError("Error, unknown group '"+dest+"'")

        if is_immutable_targetname(dest):
          raise UserError("Can't modify the contents of '"+dest+"'")

        # find the items to remove (the items in both dest and source)
        removelist = listops_intersect(targets[dest],targets[source])
        if len(removelist) == 0:
          raise UserError("No targets to remove (no items from '"+source+"' are in '"+dest+"')")

        # it's okay to end up with an empty group.   We'll leave it...
        for item in removelist:
          targets[dest].remove(item)

        continue
          





# move target to group
      elif userinputlist[0] == 'move':
        if len(userinputlist) == 4:
          moving = userinputlist[1]
          source = currenttarget
          if userinputlist[2] != 'to':
            raise UserError("Error, command format: move target to group")
          dest = userinputlist[3]

        else:
          raise UserError("Error, command format: move target to group")
 
        # check args...
        if source not in targets:
          raise UserError("Error, unknown group '"+source+"'")
        if moving not in targets:
          raise UserError("Error, unknown group '"+moving+"'")
        if dest not in targets:
          raise UserError("Error, unknown group '"+dest+"'")


        if is_immutable_targetname(dest):
          raise UserError("Can't modify the contents of '"+source+"'")

        if is_immutable_targetname(dest):
          raise UserError( "Can't modify the contents of '"+dest+"'")

        removelist = listops_intersect(targets[source], targets[moving])
        if len(removelist) == 0:
          raise UserError("Error, '"+moving+"' is not in '"+source+"'")

        addlist = listops_difference(removelist, targets[dest])
        if len(addlist) == 0:
          raise UserError("Error, the common items between '"+source+"' and '"+moving+"' are already in '"+dest+"'")

        for item in removelist:
          targets[source].remove(item)

        for item in addlist:
          targets[dest].append(item)

        continue







# contact host:port[:vessel] -- Communicate with a node
      elif userinputlist[0] == 'contact':
        if currentkeyname == None or not keys[currentkeyname]['publickey']:
          raise UserError("Error, must contact as an identity")

        if len(userinputlist)>2:
          raise UserError("Error, usage is contact host:port[:vessel]")

        if len(userinputlist[1].split(':')) == 2:
          host, portstring = userinputlist[1].split(':')
          port = int(portstring)
          vesselname = None
        elif len(userinputlist[1].split(':')) == 3:
          host, portstring,vesselname = userinputlist[1].split(':')
          port = int(portstring)
        else:
          raise UserError("Error, usage is contact host:port[:vessel]")
        
        # get information about the node's vessels
        thishandle = nmclient_createhandle(host, port, privatekey = keys[currentkeyname]['privatekey'], publickey = keys[currentkeyname]['publickey'], vesselid = vesselname, timeout = globalseashtimeout)
        ownervessels, uservessels = nmclient_listaccessiblevessels(thishandle,keys[currentkeyname]['publickey'])

        newidlist = []
        # determine if we control the specified vessel...
        if vesselname:
          if vesselname in ownervessels or vesselname in uservessels:
            longname = host+":"+str(port)+":"+vesselname
            # no need to set the vesselname, we did so above...
            id = add_vessel(longname,currentkeyname,thishandle)
            newidlist.append('%'+str(id)+"("+longname+")")
          else:
            raise UserError("Error, cannot access vessel '"+vesselname+"'")

        # we should add anything we can access
        else:
          for vesselname in ownervessels:
            longname = host+":"+str(port)+":"+vesselname
            if longname not in targets:
              # set the vesselname
              # NOTE: we leak handles (no cleanup of thishandle).   
              # I think we don't care...
              newhandle = nmclient_duplicatehandle(thishandle)
              handleinfo = nmclient_get_handle_info(newhandle)
              handleinfo['vesselname'] = vesselname
              nmclient_set_handle_info(newhandle, handleinfo)

              id = add_vessel(longname,currentkeyname,newhandle)
              newidlist.append('%'+str(id)+"("+longname+")")

          for vesselname in uservessels:
            longname = host+":"+str(port)+":"+vesselname
            if longname not in targets:
              # set the vesselname
              # NOTE: we leak handles (no cleanup of thishandle).   
              # I think we don't care...
              newhandle = nmclient_duplicatehandle(thishandle)
              handleinfo = nmclient_get_handle_info(newhandle)
              handleinfo['vesselname'] = vesselname
              nmclient_set_handle_info(newhandle, handleinfo)

              id = add_vessel(longname,currentkeyname,newhandle)
              newidlist.append('%'+str(id)+"("+longname+")")

        # tell the user what we did...
        if len(newidlist) == 0:
          print "Could not add any targets."
        else:
          print "Added targets: "+", ".join(newidlist)
            
        continue
  





# browse                               -- Find experiments I can control
      elif userinputlist[0] == 'browse':
        if currentkeyname == None or not keys[currentkeyname]['publickey']:
          raise UserError("Error, must browse as an identity with a public key")
  
        # they are trying to only do some types of lookup...
        if len(userinputlist) > 1:
          nodelist = advertise_lookup(keys[currentkeyname]['publickey'],lookuptype=userinputlist[1:])
        else:
          nodelist = advertise_lookup(keys[currentkeyname]['publickey'])

        # If there are no vessels for a user, the lookup may return ''
        for nodename in nodelist[:]:
          if nodename == '':
            nodelist.remove(nodename)

        # we'll output a message about the new keys later...
        newidlist = []

        faillist = []

        targets['browsegood'] = []

        print nodelist
        # currently, if I browse more than once, I look up everything again...
        retdict = contact_targets(nodelist,browse_target, currentkeyname)

        # parse the output so we can print out something intelligible
        for nodename in retdict:
          
          if retdict[nodename][0]:
            newidlist = newidlist + retdict[nodename][1]
          else:
            print "Error '",retdict[nodename][1],"' on "+nodename
            faillist.append(nodename)


        # tell the user what we did...
        if len(faillist) > 0:
          print "Failed to contact: "+ ", ".join(faillist)

        if len(newidlist) == 0:
          print "Could not add any new targets."
        else:
          print "Added targets: "+", ".join(newidlist)

        if len(targets['browsegood']) > 0:
          print "Added group 'browsegood' with "+str(len(targets['browsegood']))+" targets"
              
        continue





# genkeys filename [len] [as identity]          -- creates keys
      elif userinputlist[0] == 'genkeys':
        if len(userinputlist)==2:
          keylength = 1024
          # expand '~'
          fileandpath = os.path.expanduser(userinputlist[1])
          keyname = os.path.basename(fileandpath)
          pubkeyfn = fileandpath+'.publickey'
          privkeyfn = fileandpath+'.privatekey'
        elif len(userinputlist)==3:
          keylength = int(userinputlist[2])
          # expand '~'
          fileandpath = os.path.expanduser(userinputlist[1])
          keyname = os.path.basename(fileandpath)
          pubkeyfn = fileandpath+'.publickey'
          privkeyfn = fileandpath+'.privatekey'
        elif len(userinputlist)==4:
          if userinputlist[2] != 'as':
            raise UserError("Usage: genkeys filename [len] [as identity]")
          keylength = 1024
          keyname = userinputlist[3]
          pubkeyfn = userinputlist[1]+'.publickey'
          privkeyfn = userinputlist[1]+'.privatekey'
        elif len(userinputlist)==5:
          if userinputlist[3] != 'as':
            raise UserError("Usage: genkeys filename [len] [as identity]")
          keylength = int(userinputlist[2])
          keyname = userinputlist[4]
          pubkeyfn = userinputlist[1]+'.publickey'
          privkeyfn = userinputlist[1]+'.privatekey'
        else:
          raise UserError("Usage: genkeys filename [len] [as identity]")
  

        # do the actual generation (will take a while)
        newkeys = rsa_gen_pubpriv_keys(keylength)
        
        rsa_privatekey_to_file(newkeys[1],privkeyfn)
        rsa_publickey_to_file(newkeys[0],pubkeyfn)
        keys[keyname] = {'publickey':newkeys[0], 'privatekey':newkeys[1]}

        print "Created identity '"+keyname+"'"
        continue
  




# loadpub filename [as identity]                    -- loads a public key
      elif userinputlist[0] == 'loadpub':
        if len(userinputlist)==2:
          # they typed 'loadpub foo.publickey'
          if userinputlist[1].endswith('.publickey'):
            # handle '~'
            fileandpath = os.path.expanduser(userinputlist[1])
            keyname = os.path.basename(fileandpath[:len('.publickey')])
            pubkeyfn = fileandpath
          else:
            # they typed 'loadpub foo'
            # handle '~'
            fileandpath = os.path.expanduser(userinputlist[1])
            keyname = os.path.basename(fileandpath)
            pubkeyfn = fileandpath+'.publickey'
        elif len(userinputlist)==4:
          if userinputlist[2] != 'as':
            raise UserError("Usage: loadpub filename [as identity]")

          # they typed 'loadpub foo.publickey'
          if userinputlist[1].endswith('.publickey'):
            # handle '~'
            fileandpath = os.path.expanduser(userinputlist[1])
            pubkeyfn = fileandpath
          else:
            # they typed 'loadpub foo'
            # handle '~'
            fileandpath = os.path.expanduser(userinputlist[1])
            pubkeyfn = fileandpath+'.publickey'
          keyname = userinputlist[3]
        else:
          raise UserError("Usage: loadpub filename [as identity]")

        # load the key and update the table...
        pubkey = rsa_file_to_publickey(pubkeyfn)
        if keyname not in keys:
          keys[keyname] = {'publickey':pubkey, 'privatekey':None}
        else:
          keys[keyname]['publickey'] = pubkey
          
          # Check the keys, on error reverse the change and re-raise
          try:
            check_key_set(keyname)
          except:
            keys[keyname]['publickey'] = None
            raise

        continue
  




# loadpriv filename [as identity]                    -- loads a private key
      elif userinputlist[0] == 'loadpriv':
        if len(userinputlist)==2:
          # they typed 'loadpriv foo.privatekey'
          if userinputlist[1].endswith('.privatekey'):
            # handle '~'
            fileandpath = os.path.expanduser(userinputlist[1])
            privkeyfn = fileandpath+'.privatekey'
            keyname = os.path.basename(fileandpath[:len('.privatekey')])
          else:
            # they typed 'loadpriv foo'
            # handle '~'
            fileandpath = os.path.expanduser(userinputlist[1])
            privkeyfn = fileandpath+'.privatekey'
            keyname = os.path.basename(fileandpath)
        elif len(userinputlist)==4:
          if userinputlist[2] != 'as':
            raise UserError("Usage: loadpriv filename [as identity]")

          # they typed 'loadpriv foo.privatekey'
          if userinputlist[1].endswith('.privatekey'):
            # handle '~'
            fileandpath = os.path.expanduser(userinputlist[1])
            privkeyfn = fileandpath
          else:
            # they typed 'loadpriv foo'
            # handle '~'
            fileandpath = os.path.expanduser(userinputlist[1])
            privkeyfn = fileandpath+'.publickey'
          keyname = userinputlist[3]
        else:
          raise UserError("Usage: loadpriv filename [as identity]")

        # load the key and update the table...
        privkey = rsa_file_to_privatekey(privkeyfn)
        if keyname not in keys:
          keys[keyname] = {'privatekey':privkey, 'publickey':None}
        else:
          keys[keyname]['privatekey'] = privkey
          
          # Check the keys, on error reverse the change and re-raise
          try:
            check_key_set(keyname)
          except:
            keys[keyname]['privatekey'] = None
            raise
          
        continue




# loadkeys filename [as identity]                    -- loads a private key
      elif userinputlist[0] == 'loadkeys':
        if userinputlist[1].endswith('publickey') or userinputlist[1].endswith('privatekey'):
          print 'Warning: Trying to load a keypair named "'+userinputlist[1]+'.publickey" and "'+userinputlist[1]+'.privatekey"'

        if len(userinputlist)==2:

          # the user input may have a directory or tilde in it.   The key name 
          # shouldn't have either.
          fileandpath = os.path.expanduser(userinputlist[1])
          keyname = os.path.basename(fileandpath)
          privkeyfn = fileandpath+'.privatekey'
          pubkeyfn = fileandpath+'.publickey'


        elif len(userinputlist)==4:
          if userinputlist[2] != 'as':
            raise UserError("Usage: loadkeys filename [as identity]")

          # the user input may have a directory or tilde in it.   The key name 
          # shouldn't have either.
          fileandpath = os.path.expanduser(userinputlist[1])
          privkeyfn = fileandpath+'.privatekey'
          pubkeyfn = fileandpath+'.publickey'

          keyname = userinputlist[3]
        else:
          raise UserError("Usage: loadkeys filename [as identity]")



        # load the keys and update the table...
        try:
          privkey = rsa_file_to_privatekey(privkeyfn)
        except (OSError, IOError), e:
          raise UserError("Cannot locate private key '"+privkeyfn+"'.\nDetailed error: '"+str(e)+"'.")

        try:
          pubkey = rsa_file_to_publickey(pubkeyfn)
        except (OSError, IOError), e:
          raise UserError("Cannot locate private key '"+privkeyfn+"'.\nDetailed error: '"+str(e)+"'.")

        keys[keyname] = {'privatekey':privkey, 'publickey':pubkey}
        

        # Check the keys, on error reverse the change and re-raise
        try:
          check_key_set(keyname)
        except:
          del keys[keyname]
          raise
          
        continue




# list               -- Update and display information about the vessels

# output looks similar to:
#  ID Own                       Name     Status              Owner Information
#  %1  *       128.208.3.173:1224:v5      Fresh                               
#  %2  *        128.208.3.86:1224:v2      Fresh                               
#  %3          234.17.98.23:53322:v5    Stopped               Chord experiment
#
      elif userinputlist[0] == 'list':
        if len(userinputlist)>1:
          raise UserError("Usage: list")

        if not currenttarget:
          raise UserError("Must specify a target")
        
        # update information about the vessels...
        faillist = []
        goodlist = []

        retdict = contact_targets(targets[currenttarget],list_or_update_target)

        for longname in retdict:
          if retdict[longname][0]:
            goodlist.append(longname)
          else:
            print "Error '"+retdict[longname][1]+"' on "+longname
            faillist.append(longname)

        # and display it...
        if faillist:
          print "Failures on "+str(len(faillist))+" targets: "+", ".join(faillist)
        if goodlist:
          print "%4s %3s %25s %10s %30s" % ('ID','Own','Name','Status','Owner Information')

        # walk through target to print instead of the good list so that the
        # names are printed in order...
        for longname in targets[currenttarget]:
          if longname in goodlist:  
            if keys[currentkeyname]['publickey'] == vesselinfo[longname]['ownerkey']:
              owner = '*'
            else:
              owner = ''
            print "%4s  %1s  %25s %10s %30s" % (vesselinfo[longname]['ID'],owner,fit_string(longname,25),vesselinfo[longname]['status'],fit_string(vesselinfo[longname]['ownerinfo'],30))

        # add groups for fail and good (if there is a difference in what nodes do)
        if goodlist and faillist:
          targets['listgood'] = goodlist
          targets['listfail'] = faillist
          print "Added group 'listgood' with "+str(len(targets['listgood']))+" targets and 'listfail' with "+str(len(targets['listfail']))+" targets"


        statusdict = {}
        # add status groups (if there is a difference in vessel state)
        for longname in goodlist:
          if vesselinfo[longname]['status'] not in statusdict:
            # create a list with this element...
            statusdict[vesselinfo[longname]['status']] = []
          statusdict[vesselinfo[longname]['status']].append(longname)

        if len(statusdict) > 1:
          print "Added group",
          for statusname in statusdict:
            targets['list'+statusname] = statusdict[statusname]
            print "'list"+statusname+"' with "+str(len(targets['list'+statusname]))+" targets",
          print
          
        continue
  
# reset                  -- Reset the vessel (clear the log and files and stop)
      elif userinputlist[0] == 'reset':
        if len(userinputlist)>1:
          raise UserError("Usage: reset")

        if not currenttarget:
          raise UserError("Must specify a target")
        
        # reset the vessels...
        faillist = []
        goodlist = []

        retdict = contact_targets(targets[currenttarget],reset_target)

        for longname in retdict:
          if retdict[longname][0]:
            goodlist.append(longname)
          else:
            print "Error '"+retdict[longname][1]+"' on "+longname
            faillist.append(longname)

        # and display it...
        if faillist:
          print "Failures on "+str(len(faillist))+" targets: "+", ".join(faillist)
        if goodlist and faillist:
          targets['resetgood'] = goodlist
          targets['resetfail'] = faillist
          print "Added group 'resetgood' with "+str(len(targets['resetgood']))+" targets and 'resetfail' with "+str(len(targets['resetfail']))+" targets"

        continue
  



# update
      elif userinputlist[0] == 'update':
        if len(userinputlist)>1:
          raise UserError("Usage: update")

        if not currenttarget:
          raise UserError("Must specify a target")
        
        # update information about the vessels...
        faillist = []
        goodlist = []

        retdict = contact_targets(targets[currenttarget],list_or_update_target)

        for longname in retdict:
          if retdict[longname][0]:
            goodlist.append(longname)
          else:
            print "Error '"+retdict[longname][1]+"' on "+longname
            faillist.append(longname)

        # and display it...
        if faillist:
          print "Failures on "+str(len(faillist))+" targets: "+", ".join(faillist)
        if goodlist and faillist:
          targets['updategood'] = goodlist
          targets['updatefail'] = faillist
          print "Added group 'updategood' with "+str(len(targets['updategood']))+" targets and 'updatefail' with "+str(len(targets['updatefail']))+" targets"

        continue
  


# savestate localfile -- Save current states to file (Added by Danny Y. Huang)
      elif userinputlist[0] == 'savestate':
        if len(userinputlist) == 2:
          # expand ~
          fileandpath = os.path.expanduser(userinputlist[1]) 
        else:
          raise UserError("Usage: savestate localfile")

        try:
          savestate(fileandpath, handleinfo, host, port, expnum, filename, 
                    cmdargs, defaulttarget, defaultkeyname, autosave, currentkeyname)
        except Exception, error:
          raise UserError("Error saving state: '" + str(error) + "'.")

        continue




# loadstate localfile -- Load states from file (Added by Danny Y. Huang)
      elif userinputlist[0] == 'loadstate':
        if len(userinputlist) == 2:
          # expand ~
          fileandpath = os.path.expanduser(userinputlist[1]) 
        else:
          raise UserError("Usage: loadstate localfile")

        if not currentkeyname:
          raise UserError("Specify the key name by first typing 'as [username]'.")
        
        # reading encrypted serialized states from file
        state_obj = open(fileandpath, 'r')
        cypher = state_obj.read()
        state_obj.close()

        try:
          # decrypt states
          statestr = rsa_decrypt(cypher, keys[currentkeyname]['privatekey'])

          # deserialize
          state = serialize_deserializedata(statestr)
        except Exception, error:
          error_msg = "Unable to correctly parse state file. Your private "
          error_msg += "key may be incorrect."
          raise UserError(error_msg)

        # restore variables
        targets = state['targets']
        keys = state['keys']
        vesselinfo = state['vesselinfo']
        handleinfo = state['handleinfo']
        nextid = state['nextid']
        host = state['host']
        port = state['port']
        expnum = state['expnum']
        filename = state['filename']
        cmdargs = state['cmdargs'] 
        defaulttarget = state['defaulttarget']
        defaultkeyname = state['defaultkeyname']
        autosave = state['autosave']
        globalseashtimeout = state['globalseashtimeout']
        globaluploadrate = state['globaluploadrate']
        
        # Reload node handles. Rogue nodes are deleted from the original targets
        # and vesselinfo dictionaries.
        retdict = contact_targets(targets['%all'], reload_target, handleinfo)
        
        reloadgood = []
        reloadfail = []

        for longname in retdict:
          if not retdict[longname][0]:
            print "Failure '" + retdict[longname][1] + "' on " + longname + "."
            reloadfail.append(longname)
          else:
            reloadgood.append(longname)

        # update the groups
        if reloadfail and reloadgood:
          targets['reloadgood'] = reloadgood
          targets['reloadfail'] = reloadfail
          print("Added group 'reloadgood' with " +str(len(targets['reloadgood'])) + \
                  " targets and 'reloadfail' with " + str(len(targets['reloadfail'])) + " targets")

        if autosave:
          print "Autosave is on."

        continue





# upload localfn (remotefn)   -- Upload a file 
      elif userinputlist[0] == 'upload':
        if len(userinputlist)==2:
          # expand '~'
          fileandpath = os.path.expanduser(userinputlist[1])
          remotefn = os.path.basename(fileandpath)
          localfn = fileandpath
        elif len(userinputlist)==3:
          # expand '~'
          fileandpath = os.path.expanduser(userinputlist[1])
          localfn = fileandpath
          remotefn = userinputlist[2]
        else:
          raise UserError("Usage: upload localfn (remotefn)")

        if not currenttarget:
          raise UserError("Must specify a target")


        # read the local file...
        fileobj = open(localfn,"r")
        filedata = fileobj.read()
        fileobj.close()

        # to prevent timeouts during file uploads on slow connections,
        # temporarily sets the timeout count on all vessels to be the 
        # time needed to upload the file with the current globaluploadrate
        set_upload_timeout(filedata)

        # add the file to the vessels...
        faillist = []
        goodlist = []

        retdict = contact_targets(targets[currenttarget],upload_target, remotefn, filedata)

        for longname in retdict:
          if retdict[longname][0]:
            goodlist.append(longname)
          else:
            print "Failure '"+retdict[longname][1]+"' uploading to",longname
            faillist.append(longname)

        # update the groups
        if goodlist and faillist:
          targets['uploadgood'] = goodlist
          targets['uploadfail'] = faillist
          print "Added group 'uploadgood' with "+str(len(targets['uploadgood']))+" targets and 'uploadfail' with "+str(len(targets['uploadfail']))+" targets"

        # resets the timeout count on all vessels to globalseashtimeout
        reset_vessel_timeout()
  
        continue
  


# download remotefn (localfn) -- Download a file 
      elif userinputlist[0] == 'download':
        if len(userinputlist)==2:
          # handle '~'
          fileandpath = os.path.expanduser(userinputlist[1])
          remotefn = os.path.basename(fileandpath)
          localfn = fileandpath
        elif len(userinputlist)==3:
          remotefn = userinputlist[1]
          # handle '~'
          fileandpath = os.path.expanduser(userinputlist[2])
          localfn = fileandpath
        else:
          raise UserError("Usage: download localfn (remotefn)")

        if not currenttarget:
          raise UserError("Must specify a target")
  


        faillist = []
        goodlist = []

        retdict = contact_targets(targets[currenttarget],download_target,localfn,remotefn)

        writestring = ''
        for longname in retdict:
          if retdict[longname][0]:
            goodlist.append(longname)
            # for output...
            writestring = writestring + retdict[longname][1]+ " "
          else:
            print "Failure '"+retdict[longname][1]+"' downloading from",longname
            faillist.append(longname)

        if writestring:
          print "Wrote files: "+writestring

        # add groups if needed...
        if goodlist and faillist:
          targets['downloadgood'] = goodlist
          targets['downloadfail'] = faillist
          print "Added group 'downloadgood' with "+str(len(targets['downloadgood']))+" targets and 'downloadfail' with "+str(len(targets['downloadfail']))+" targets"

  
        continue
  



# delete remotefn             -- Delete a file
      elif userinputlist[0] == 'delete':
        if len(userinputlist)==2:
          remotefn = userinputlist[1]
        else:
          raise UserError("Usage: delete remotefn")

        if not currenttarget:
          raise UserError("Must specify a target")
  

        faillist = []
        goodlist = []

        retdict = contact_targets(targets[currenttarget],delete_target, remotefn)

        for longname in retdict:
          if retdict[longname][0]:
            goodlist.append(longname)
          else: 
            print "Failure '"+retdict[longname][1]+"' deleting on",longname
            faillist.append(longname)

        # add groups if needed...
        if goodlist and faillist:
          targets['deletegood'] = goodlist
          targets['deletefail'] = faillist
          print "Added group 'deletegood' with "+str(len(targets['deletegood']))+" targets and 'deletefail' with "+str(len(targets['deletefail']))+" targets"

  
        continue
  

  
# start file [args ...]  -- Start an experiment
      elif userinputlist[0] == 'start':
        if len(userinputlist)>1:
          argstring = ' '.join(userinputlist[1:])
        else:
          raise UserError("Usage: start file [args ...]")

        if not currenttarget:
          raise UserError("Must specify a target")
  
        # need to get the status, etc (or do I just try to start them all?)
        faillist = []
        goodlist = []

        retdict = contact_targets(targets[currenttarget],start_target, argstring)

        for longname in retdict:
          if retdict[longname][0]:
            goodlist.append(longname)
          else:
            print "Failure '"+retdict[longname][1]+"' starting ",longname
            faillist.append(longname)

        # add groups if needed...
        if goodlist and faillist:
          targets['startgood'] = goodlist
          targets['startfail'] = faillist
          print "Added group 'startgood' with "+str(len(targets['startgood']))+" targets and 'startfail' with "+str(len(targets['startfail']))+" targets"

  

# stop               -- Stop an experiment
      elif userinputlist[0] == 'stop':
        if len(userinputlist)>1:
          raise UserError("Usage: stop")

        if not currenttarget:
          raise UserError("Must specify a target")
  
        # need to get the status, etc (or do I just try to stop them all?)
        faillist = []
        goodlist = []

        retdict = contact_targets(targets[currenttarget],stop_target)

        for longname in retdict:
          if retdict[longname][0]:
            goodlist.append(longname)
          else:
            print "Failure '"+retdict[longname][1]+"' stopping ",longname
            faillist.append(longname)



        # add groups if needed...
        if goodlist and faillist:
          targets['stopgood'] = goodlist
          targets['stopfail'] = faillist
          print "Added group 'stopgood' with "+str(len(targets['stopgood']))+" targets and 'stopfail' with "+str(len(targets['stopfail']))+" targets"



# run file [args...]    -- Shortcut for upload a file and start
      elif userinputlist[0] == 'run':
        if len(userinputlist)>1:
          # Handle '~' in file names
          fileandpath = os.path.expanduser(userinputlist[1])
          onlyfilename = os.path.basename(fileandpath)
          argstring = " ".join([onlyfilename] + userinputlist[2:])
        else:
          raise UserError("Usage: run file [args ...]")

        if not currenttarget:
          raise UserError("Must specify a target")
  

        # read the local file...
        fileobj = open(fileandpath,"r")
        filedata = fileobj.read()
        fileobj.close()

        # to prevent timeouts during file uploads on slow connections,
        # temporarily sets the timeout count on all vessels to be the 
        # time needed upload the file with the current globaluploadrate
        set_upload_timeout(filedata)

        faillist = []
        goodlist = []

        retdict = contact_targets(targets[currenttarget],run_target,onlyfilename,filedata, argstring)

        for longname in retdict:
          if retdict[longname][0]:
            goodlist.append(longname)
          else:
            print "Failure '"+retdict[longname][1]+"' on ",longname
            faillist.append(longname)


        # update the groups
        if goodlist and faillist:
          targets['rungood'] = goodlist
          targets['runfail'] = faillist
          print "Added group 'rungood' with "+str(len(targets['rungood']))+" targets and 'runfail' with "+str(len(targets['runfail']))+" targets"

        # resets the timeout count on all vessels to globalseashtimeout
        reset_vessel_timeout()
  
        continue
  





#split resourcefn            -- Split off of each vessel another vessel

      elif userinputlist[0] == 'split':
        if len(userinputlist)==2:
          # expand ~
          fileandpath = os.path.expanduser(userinputlist[1])
          resourcefn = fileandpath
        else:
          raise UserError("Usage: split resourcefn")

        if not currenttarget:
          raise UserError("Must specify a target")

        resourcefo = open(resourcefn)
        resourcedata = resourcefo.read()
        resourcefo.close() 
  

        faillist = []
        goodlist1 = []
        goodlist2 = []

        retdict = contact_targets(targets[currenttarget],split_target,resourcedata)

        for longname in retdict:
          if retdict[longname][0]:
            newname1, newname2 = retdict[longname][1]
            goodlist1.append(newname1)
            goodlist2.append(newname2)
            print longname+" -> ("+newname1+", "+newname2+")"
          else:
            print "Failure '"+retdict[longname][1]+"' splitting",longname
            faillist.append(longname)

        # update the groups
        if goodlist1 and goodlist2 and faillist:
          targets['split1'] = goodlist1
          targets['split2'] = goodlist2
          targets['splitfail'] = faillist
          print "Added group 'split1' with "+str(len(targets['split1']))+" targets, 'split2' with "+str(len(targets['split2']))+" targets and 'splitfail' with "+str(len(targets['splitfail']))+" targets"
        elif goodlist1 and goodlist2:
          targets['split1'] = goodlist1
          targets['split2'] = goodlist2
          print "Added group 'split1' with "+str(len(targets['split1']))+" targets and 'split2' with "+str(len(targets['split2']))+" targets"

  
        continue




#join                        -- Join vessels on the same node

      elif userinputlist[0] == 'join':
        if len(userinputlist)!=1:
          raise UserError("Usage: join")

        if not currenttarget:
          raise UserError("Must specify a target")

        if not currentkeyname or not keys[currentkeyname]['publickey'] or not keys[currentkeyname]['privatekey']:
          raise UserError("Must specify an identity with public and private keys...")

        nodedict = {}
        skipstring = ''
        # Need to group vessels by node...
        for longname in targets[currenttarget]:
          if keys[currentkeyname]['publickey'] != vesselinfo[longname]['ownerkey']:
            skipstring = skipstring + longname+" "
            continue

          nodename = vesselinfo[longname]['IP']+":"+str(vesselinfo[longname]['port'])
          if nodename not in nodedict:
            nodedict[nodename] = []

          nodedict[nodename].append(longname)

        # if we skip nodes, explain why
        if skipstring:
          print "Skipping "+skipstring+" because the current identity is not the owner."
          print "If you are trying to join vessels with different owners, you need"
          print "to change ownership to the same owner first"


        faillist = []
        goodlist = []

        retdict = contact_targets(nodedict.keys(),join_target,nodedict)

        for nodename in retdict:
 
          if retdict[nodename][0]:
            print retdict[nodename][1][0],"<- ("+", ".join(nodedict[nodename])+")"
            goodlist = goodlist + nodedict[nodename]
          else:
            if retdict[nodename][1]:
              print "Failure '"+retdict[nodename][1]+"' on",nodename
              faillist = faillist + nodedict[nodename]
            # Nodes that I only have one vessel on don't get added to a list...

        # update the groups
        if goodlist and faillist:
          targets['joingood'] = goodlist
          targets['joinfail'] = faillist
          print "Added group 'joingood' with "+str(len(targets['joingood']))+" targets and 'joinfail' with "+str(len(targets['joinfail']))+" targets"
        elif goodlist:
          targets['joingood'] = goodlist
          targets['joinfail'] = faillist
          print "Added group 'joingood' with "+str(len(targets['joingood']))+" targets"

  
        continue














# set                 -- Changes the state of the targets (use 'help set')
      elif userinputlist[0] == 'set':
      
  
        if len(userinputlist) == 1:
          # what do I do here?
          pass

        
# set owner identity        -- Change a vessel's owner
        elif userinputlist[1] == 'owner':
          if len(userinputlist)==3:
            newowner = userinputlist[2]
          else:
            raise UserError("Usage: set owner identity")
  
          if not currenttarget:
            raise UserError("Must specify a target")
  
          if newowner not in keys:
            raise UserError("Unknown identity: '"+newowner+"'")

          if not keys[newowner]['publickey']:
            raise UserError("No public key for '"+newowner+"'")

          faillist = []
          goodlist = []
          retdict = contact_targets(targets[currenttarget],setowner_target,newowner)

          for longname in retdict:
            if retdict[longname][0]:
              goodlist.append(longname)
            else:
              print "Failure '"+retdict[longname][1]+"' on ",longname
              faillist.append(longname)


  
          # update the groups
          if goodlist and faillist:
            targets['ownergood'] = goodlist
            targets['ownerfail'] = faillist
            print "Added group 'ownergood' with "+str(len(targets['ownergood']))+" targets and 'ownerfail' with "+str(len(targets['ownerfail']))+" targets"
  
    
          continue
  


# set autosave [ on | off ] -- Set whether SeaSH automatically saves the last state.
        elif userinputlist[1] == 'autosave':
          if len(userinputlist) == 3:
            if userinputlist[2] == 'on':
              autosave = True
            elif userinputlist[2] == 'off':
              autosave = False
            else:
              raise UserError("Usage: set autosave [ on | off (default)]")
          else:
            raise UserError("Usage: set autosave [ on | off (default)]")
          
          continue



# set advertise [ on | off ] -- Change advertisement of vessels
        elif userinputlist[1] == 'advertise':
          if len(userinputlist)==3:
            if userinputlist[2] == 'on':
              newadvert = True
            elif userinputlist[2] == 'off':
              newadvert = False
            else:
              raise UserError("Usage: set advertise [ on | off ]")
          else:
            raise UserError("Usage: set advertise [ on | off ]")
  
          if not currenttarget:
            raise UserError("Must specify a target")
  

          faillist = []
          goodlist = []
          retdict = contact_targets(targets[currenttarget],setadvertise_target,newadvert)

          for longname in retdict:
            if retdict[longname][0]:
              goodlist.append(longname)
            else:
              print "Failure '"+retdict[longname][1]+"' on ",longname
              faillist.append(longname)


          # update the groups
          if goodlist and faillist:
            targets['advertisegood'] = goodlist
            targets['advertisefail'] = faillist
            print "Added group 'advertisegood' with "+str(len(targets['advertisegood']))+" targets and 'advertisefail' with "+str(len(targets['advertisefail']))+" targets"
  
    
          continue
  

# set ownerinfo [ data ... ]    -- Change owner information for the vessels
        elif userinputlist[1] == 'ownerinfo':
          newdata = " ".join(userinputlist[2:])
  
          if not currenttarget:
            raise UserError("Must specify a target")
  
          faillist = []
          goodlist = []
          retdict = contact_targets(targets[currenttarget],setownerinformation_target,newdata)

          for longname in retdict:
            if retdict[longname][0]:
              goodlist.append(longname)
            else:
              print "Failure '"+retdict[longname][1]+"' on ",longname
              faillist.append(longname)


          # update the groups
          if goodlist and faillist:
            targets['ownerinfogood'] = goodlist
            targets['ownerinfofail'] = faillist
            print "Added group 'ownerinfogood' with "+str(len(targets['ownerinfogood']))+" targets and 'ownerinfofail' with "+str(len(targets['ownerinfofail']))+" targets"
  
    
          continue
  

# set users [ identity ... ]  -- Change a vessel's users
        elif userinputlist[1] == 'users':
          userkeys = []

          for identity in userinputlist[2:]:
            if identity not in keys:
              raise UserError("Unknown identity: '"+identity+"'")

            if not keys[identity]['publickey']:
              raise UserError("No public key for '"+identity+"'")
          
            userkeys.append(rsa_publickey_to_string(keys[identity]['publickey']))
          # this is the format the NM expects...
          userkeystring = '|'.join(userkeys)
  
          if not currenttarget:
            raise UserError("Must specify a target")
  

          faillist = []
          goodlist = []
          retdict = contact_targets(targets[currenttarget],setusers_target,userkeystring)

          for longname in retdict:
            if retdict[longname][0]:
              goodlist.append(longname)
            else:
              print "Failure '"+retdict[longname][1]+"' on ",longname
              faillist.append(longname)
  
          # update the groups
          if goodlist and faillist:
            targets['usersgood'] = goodlist
            targets['usersfail'] = faillist
            print "Added group 'usersgood' with "+str(len(targets['usersgood']))+" targets and 'usersfail' with "+str(len(targets['usersfail']))+" targets"
  
    
          continue


# set timeout count  -- Sets the time that seash is willing to wait on a node
        elif userinputlist[1] == 'timeout':

          if len(userinputlist) != 3:
            raise UserError("set timeout takes exactly one argument")

          # I need to set the timeout for new handles...
          try:
            globalseashtimeout = int(userinputlist[2])
          except ValueError:
            raise UserError("The timeout value must be a number")

          # let's reset the timeout for existing handles...
          for longname in vesselinfo:
            thisvesselhandle = vesselinfo[longname]['handle']
            thisvesselhandledict = nmclient_get_handle_info(thisvesselhandle)
            thisvesselhandledict['timeout'] = globalseashtimeout
            nmclient_set_handle_info(thisvesselhandle,thisvesselhandledict)
    
          continue


        # set uploadrate speed     -- Sets the speed seash will modify the
        #                             timeout count with when uploading files
        elif userinputlist[1] == 'uploadrate':

          if len(userinputlist) != 3:
            raise UserError("set uploadrate takes exactly one positive integer")
          try:
            globaluploadrate = int(userinputlist[2])
          except ValueError:
            raise UserError("The speed value must be a number (in bytes per second)")
        




# set ???  -- Bad command for set...
        else:

          print "Error: set command not understood, try 'help set'"

  

  
  


  
  

  
  
# else unknown
      else:
        print "Error: command not understood"
  

# handle errors
    except KeyboardInterrupt:
      # print or else their prompt will be indented
      print
      # Make sure the user understands why we exited
      print 'Exiting due to user interrupt'
      return
    except EOFError:
      # print or else their prompt will be indented
      print
      # Make sure the user understands why we exited
      print 'Exiting due to EOF (end-of-file) keystroke'
      return
    except UserError, e:
      print e
    except:
      traceback.print_exc()
      
  
  
if __name__=='__main__':
  time_updatetime(34612)
  command_loop()
