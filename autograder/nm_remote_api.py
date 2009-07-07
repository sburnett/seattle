"""
<Program Name>
  nm_remote_api.mix/py

<Author>
  Alper Sarikaya
  alpers@cs.washington.edu

<Purpose>
  Creates an interface between Emulab Seattle instances and the autograder
  scripting.

  Summary of functionality:
      - connects to remote emulab nodes by hostname 
            initialize(), add_node_by_hostname()
      - runs a repy program on a group of nodes or a single node with a 
        given timeout
            run_on_targets(), run_target()
      - acquires log output from vessels and stores them in state for user

  This is a general interface with connecting with remote Seattle instances
  directly, but the functionality is geared toward the needs of the
  autograder.

"""

import sys 
import nmAPI

from repyportability import *

import repyhelper

repyhelper.translate_and_import("nmclient.repy")
repyhelper.translate_and_import("rsa.repy")
repyhelper.translate_and_import("parallelize.repy")

# global state
key = {}
vesselinfo = {}

# the default Seattle instance to connect to
DEFAULT_NODEMANAGER_PORT = 1224

# alpers - adds a vessel and its information to the overall vessel dict
#          (from seash.mix); this is strictly internal.
def add_vessel(longname, vesselhandle):
    vesselinfo[longname] = {}
    vesselinfo[longname]['handle'] = vesselhandle
    vesselinfo[longname]['IP'] = longname.split(':')[0]
    vesselinfo[longname]['port'] = int(longname.split(':')[1])
    vesselinfo[longname]['vesselname'] = longname.split(':')[2]
    


def add_node_by_hostname(host, port=DEFAULT_NODEMANAGER_PORT):
    """
    <Purpose>
      Attempts to find a running Seattle instance at the host specified, 
      connect to it, and add meta-information about the instance and its 
      available vessels to the internal dictionary (vesselinfo).

    <Arguments>
      host:
          The host where the Seattle instance is running (ip or full-qual name)
      port:
          The port where the Seattle instance is running (default 1224)

    <Exceptions>
      Will throw an exception if the module has not been initalized, the host 
      was not found, or no Seattle instance was found running on the specified
      host:port.

    <Side Effects>
      Updates internal dict vesselinfo

    <Returns>
      Returns a list of vessel longnames
    """

    check_is_initialized(check_vesselinfo=False)
        
    # get information about the node's vessels
    thishandle = nmclient_createhandle(host, port, privatekey = key['private'],
                                       publickey = key['public'])
    ownervessels, uservessels = nmclient_listaccessiblevessels(thishandle, 
                                                               key['public'])
    
    new_vessel_list = []
    
    # we should add anything we can access (we only care about ownervessels)
    for vesselname in ownervessels:
      longname = host+":"+str(port)+":"+vesselname
      if longname not in vesselinfo:
        # set the vesselname
        # NOTE: we leak handles (no cleanup of thishandle).   
        # I think we don't care...
        newhandle = nmclient_duplicatehandle(thishandle)
        handleinfo = nmclient_get_handle_info(newhandle)
        handleinfo['vesselname'] = vesselname
        nmclient_set_handle_info(newhandle, handleinfo)
        
        add_vessel(longname, newhandle)
        new_vessel_list.append(longname)
        
        
    # tell the user what we did...
    if len(new_vessel_list) == 0:
        print "Could not add any targets."
    else:
        print "Added targets: "+", ".join(new_vessel_list)

    return new_vessel_list

    

# alpers - tells specified vessels to run a program
def run_on_targets(vessel_list, filename, filedata, argstring, timeout=240):
    """
    <Purpose>
      Attempts to run a specific program on a group of Emulab nodes.  This
      should be the main way to run repy code on a *group* of Emulab nodes.

    <Arguments>
      vessel_list:
          A valid list of vessel longnames.

      filename:
          The name/location of the repy file to import.

      filedata:
          The contents of the file in string format (e.g. output of 
          filename.read())

      argstring:
          An argument string passed to the repy program at runtime - note that 
          the argstring is NEVER empty - the first argument should always be 
          the filename.
         
      timeout:
          A specified timeout (in seconds) at which the vessel will be forcibly
          stopped.  Defaults to 240 seconds (4 minutes).

    <Exceptions>
      Will throw an exception if any of the names in the vessel_list are
      invalid (i.e. not in vesselinfo).  This check will also check if the 
      module has been initialized or not.

    <Side Effects>
      Calls at maximum 20 threads to delegate run_target() to; has the
      potential to overrun memory if called too much

    <Returns>
      A dictionary with the key as the vessel longname and the value as
      a tuple of (success?, info).  
      
      If success is False, the program either threw an exception (highly
      improbable, see run_target()) or was preempted by the timeout - the info
      string will contain various debug info.  
      
      If success is True, the program was successfully started and terminated.

    """

    # check to see whether all vessel names are valid
    for vessel in vessel_list:
        if vessel not in vesselinfo:
            raise Exception, "Unable to find vessel in current state " + \
                "(vessel: " + vessel + ")"

    # start the parallelized communication using the single-vessel 
    # run_target() function
    phandle = parallelize_initfunction(vessel_list, run_target, 20, filename, 
                                       filedata, argstring, timeout)

    # wait until all functions have completed
    while not parallelize_isfunctionfinished(phandle):
        sleep(0.1)

    # start a dictionary to keep track of results
    resultdict = parallelize_getresults(phandle)
    log_results = {}

    # for each exception, assert False and pass along the exception text
    for (vessel, exception) in resultdict['exception']:
        log_results[vessel] = (False, exception)

    # for each successful run, communicate the results to the log.
    # success may be False if timeout was triggered; caller will need to check
    for (vessel, (success, msg)) in resultdict['returned']:
        log_results[vessel] = (success, msg)

    return log_results



# alpers - attempts to tell vessel to run a program
def run_target(longname, filename, filedata, argstring, timeout=240):
    """
    <Purpose>
      Attempts to add and run a file on a specific vessel given the vessel's 
      longname and the file data.  This should be the main way to execute repy 
      code on emulab servers.

    <Arguments>
      longname:
          The vessel's longname, i.e. ip:port:vessel_name

      filename:
          The name of the repy file

      filedata:
          A string containing the contents of the file (filename.read())

      argstring:
          An argument string passed to the repy program at runtime - note that 
          the argstring is NEVER empty - the first argument should always be the
          filename.
         
      timeout:
          A specified timeout (in seconds) at which the vessel will be forcibly
          stopped.  Defaults to 240 seconds (4 minutes).

    <Exceptions>
      At the moment will throw an exception if the longname is invalid.  It will
      also throw an exception if the module has not been initialized.

    <Side Effects>
      None.

    <Returns>
      A tuple with the format (success?, info).  On success, the tuple (True,) 
      will be returned; on failure the tuple (False, str(exception)) will be 
      returned.
    """

    # smart argstring check:
    if filename.find("/") != -1:
        error_msg = "Please pass in the filename without any directory/hierarchy information (passed in '%s')" % filename
        return (False, error_msg)

    # check if the first argument is the file name - if not, add it
    argparts = argstring.partition(" ")
    if argparts[0] != filename:
        if argparts[2] != "":
            argstring = filename + " " + argparts[2].strip()
        else:
            argstring = filename

    check_is_initialized()

    # add the file to the vessel
    vesselname = vesselinfo[longname]['vesselname']
    try:
        nmclient_signedsay(vesselinfo[longname]['handle'], "AddFileToVessel", 
                           vesselname, filename, filedata)
    except NMClientException, e:
        return (False, str(e))
    
    #print "Successfully added ", filename, " to vessel"
    
    # start the execution of the file
    try:
        nmclient_signedsay(vesselinfo[longname]['handle'], "StartVessel", 
                           vesselname, argstring)
    except NMClientException, e:
        return (False, str(e))
    
    # check and wait for termination
    num_checks = 10
    sleep_time = 0
    for i in range(num_checks):
        if i + 1 == num_checks:
            sleep_time = timeout/num_checks + timeout%num_checks
        else:
            sleep_time = timeout/num_checks

        sleep(sleep_time)
        #print "slept for ", str(sleep_time), " seconds"
        
        if is_vessel_finished(longname):
            print "noticed that execution is done before timeout hit"
            break

    summary = ""
    if not is_vessel_finished(longname):
        summary += "Timeout (" + str(timeout) + \
            " seconds) triggered; stopping execution"
        stop_target(longname)
        return (False, summary)
    else:
        summary += "Finished execution in approx. " + str(sleep_time) + \
            " seconds."
        return (True, summary)
    

def stop_target(longname):
    """
    <Purpose>
      Stop a vessel from executing repy code.

    <Arguments>
      longname:
          The vessel's longname, i.e. ip:port:vessel_name

    <Exceptions>
      At the moment will throw an exception if the longname is invalid.  It will
      also throw an exception if the module has not been initalized.

    <Side Effects>
      None.

    <Returns>
      A tuple consisting of (success?, info)
    """

    check_is_initialized()

    vesselname = vesselinfo[longname]['vesselname']
    try:
        nmclient_signedsay(vesselinfo[longname]['handle'], "StopVessel",
                           vesselname)
    except NMClientException, e:
        return (False, str(e))
    else:
        return (True,)



def showlog_vessel(longname):
    """
    <Purpose>
      Get a vessel's log outlining output from the executed repy file.

    <Arguments>
      longname:
          The vessel's longname, i.e. ip:port:vessel_name

    <Exceptions>
      At the moment will throw an exception if the longname is invalid.  It will
      also throw an exception if the module has not been initalized.

    <Side Effects>
      None.

    <Returns>
      A tuple consisting of (success?, info).  A successful log-get will write 
      the log to the info variable, otherwise the exception will be printed.
    """

    check_is_initialized()

    vesselname = vesselinfo[longname]['vesselname']
    try:
        logdata = nmclient_signedsay(vesselinfo[longname]['handle'],"ReadVesselLog",
                                     vesselname)
    except NMClientException, e:
        return (False, str(e))
    else:
        append_log(longname, logdata)
        return (True, logdata)



def reset_targets(longname_list):
    """
    <Purpose>
      Cleans a group of vessels for reuse.  Specifically, cleans the vessels'
      logs, filesystems, and halts any running code.

    <Arguments>
      longname_list:
          A list of vessel longnames, i.e. [ip:port:v1, ip:port,v2, ...]

    <Exceptions>
      Only raises an exception if the module has not been initialized.  
      All exceptions from reset_target() will be caught and returned in the 
      failed_hosts dictionary (including longname KeyErrors).

    <Side Effects>
      Clears the (global) logs state of this module for each vessel that
      successfully reset.

    <Returns>
      A tuple consisting of (success?, failed_dict).  A success is determined
      by each vessel successfully resetting; a failure is designated by at
      least one failure.  The failures are detailed in the failed_dict, where 
      the key is the longname and the value is the exception string.
    """

    check_is_initialized()
    global logs
    
    phandle = parallelize_initfunction(longname_list, reset_target, 20)

    while not parallelize_isfunctionfinished(phandle):
        sleep(0.1)

    resultdict = parallelize_getresults(phandle)

    failed_hosts = {}
    for (vessel, (success, msg)) in resultdict['returned']:
        #print vessel, success, msg
        if not success:
            failed_hosts[vessel] = msg
    
    for (vessel, exception_str) in resultdict['exception']:
        failed_hosts[vessel] = exception_str

    if len(failed_hosts.keys()) == 0:
        return (True, "")
    else:
        return (False, failed_hosts)



def reset_target(longname):
    """
    <Purpose>
      Cleans a specific vessel for reuse.  Specifically, cleans the vessels
      log, filesystem, and halts any running code.

    <Arguments>
      longname:
          The vessel's longname, i.e. ip:port:vessel_name
    
    <Exceptions>
      At the moment throws a KeyError if the longname is not in the current
      state or if the module has not been initialized.

    <Side Effects>
      Will clear the (global) logs entry for this specific vessel.

    <Returns>
      A tuple consisting of (success?, info).  A successful reset have no info,
      otherwise the exception will be copied to the info variable.

    """
    
    check_is_initialized()

    vesselname = vesselinfo[longname]['vesselname']
    handle = vesselinfo[longname]['handle']
    try:
        nmclient_signedsay(handle, "ResetVessel", vesselname)
    except NMClientException, e:
        return (False, str(e))
    else:
        # delete the logs relating to this vessel
        global logs
        del logs[longname]
        
        return (True, "")


# alpers - initialize stuff!
def initialize(host_list, keyname):
    """
    <Purpose>
      Initializes the state of the module, attempts to connect to each instance
      of Seattle on the given Emulab nodes.

    <Arguments>
      host_list: 
          A list of valid Emulab hostnames with running Seattle instances.
      keyname:
          The name of the public and private keys of which to authenticate
          to the Seattle instances.  This string is the prefix of the publickey
          and privatekey files. (e.g. "autograder" for "autograder.publickey")

    <Exceptions>
      Should return no exceptions, except if keyname is incorrect (not found).

    <Side Effects>
      Initializes module state.

    <Returns>
      A tuple consisting of (success?, info), where info is a list of vessel
      longnames on success and a summary failure string on fail.  Success is
      determined by number of vessels acquired; if that number is less than
      the number of hosts given, this will fail.

      ** this condition will not be upheld if hosts have multiple vessels.

    """
    
    summary = ""

    # check if any state has been initialized
    if not key == {} or not vesselinfo == {}:
        summary += "Initialized state still exists, tear_down() first."
        return (False, summary)
    
    # attempt to read in authentication keys
    key['public'] = rsa_file_to_publickey(keyname + ".publickey")
    key['private'] = rsa_file_to_privatekey(keyname + ".privatekey")

    # critical for nmclient to work, attempt to get the current time on port
    time_updatetime(34933)
    
    # attempt to contact and store state, append vessel longnames to list
    acquired_vessels = []
    for host in host_list:
        try:
            new_vessels = add_node_by_hostname(host)
        except NMClientException, e:
            summary += " " + str(e)
        else:
            acquired_vessels.extend(new_vessels)
            
    # if we were given a certain number of hosts, we should at least have that
    # many vessels (doesn't guarantee uniqueness)
    if len(acquired_vessels) < len(host_list):
        return (False, summary)
    else:
        return (True, acquired_vessels)



# alpers - test whether module has been initialized
def check_is_initialized(check_vesselinfo=True):
    is_initialized = True
    if not key == {}:
        if check_vesselinfo:
            if not vesselinfo == {}:
                is_initialized = True
        else:
            is_initialized = True
    else:
        is_initialized = False

    if not is_initialized:
        raise Exception, "The module has not been initialized."



# alpers - tear down..
def tear_down():
    """
    <Purpose>
      Clears all stored state about previous vessels.

    <Arguments>
      None.

    <Exceptions>
      None.

    <Side Effects>
      Clears all state (vesselinfo, stored keys, logs); no vessel 
      functionality will work (they will all return exceptions)

    <Returns>
      None.

    """

    key = {}
    vesselinfo = {}

    log_lock.acquire()
    logs = {}
    log_lock.release()



def is_vessel_finished(longname):
    """
    <Purpose>
      Attempts to acquire a vessel's current state and determine whether it has
      finished running repy code.

    <Arugments>
      The vessel longname of which to query.

    <Exceptions>
      Will throw an exception if the module has not been instantiated or the
      longname is invalid.

    <Side Effects>
      None.
    
    <Returns>
      True if the vessel has finished running repy code, False otherwise (this
      includes not having run code at all!)

    """
    
    retdict = nmclient_getvesseldict(vesselinfo[longname]['handle'])
    status = retdict['vessels'][vesselinfo[longname]['vesselname']]['status']

    print "current status of", longname, "=>", status

    if status == 'Started':
        return False
    else:
        return True



# ! nothing calls the next two anymore, but I feel like it could be useful..
def query_all_vessels_state():
    """
    <Purpose>
      Attempts to acquire vessel state for each vessel in vesselinfo.

    <Arguments>
      None.

    <Exceptions>
      Should be none unless vesselinfo was instantiated incorrectly and has
      invalid data.

    <Side Effects>
      None.

    <Returns>
      A dictionary of vessel longnames to status strings.
    """
    
    status_list = {}
    
    for longname in vesselinfo:
        retdict = nmclient_getvesseldict(vesselinfo[longname]['handle'])
        status_list[longname] = retdict['vessels'][vesselinfo[longname]['vesselname']]['status']
    
    return status_list



# alpers - query vessel state to see if vessels are finished executing
def all_emulab_vessels_done():
    """
    <Purpose>
      Runs query_vessel_state() to determine whether all vessels have finished 
      executing repy code.

    <Arguments>
      None.

    <Exceptions>
      Should be none unless vesselinfo was instantiated incorrectly and has
      invalid data.

    <Side Effects>
      None.

    <Returns>
      A boolean describing whether all vessels have finished executing repy 
      code.
    """

    status = query_vessel_state()
    for vessel, status in status.iteritems():
        if status == 'Started':
            return False

    return True



# this code is outdated, should i still use this?
# currently being used with showlog_vessel()
log_lock = threading.Lock()
logs = {}
def append_log(host, log):
    log_lock.acquire()
    logs[host] = log
    log_lock.release()

def get_logs():
    return logs
