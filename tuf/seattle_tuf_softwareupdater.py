""" 
Author: Justin Cappos

Start Date: August 4, 2008

Description:
A software updater for the node manager.   The focus is to make it secure, 
robust, and simple (in that order).

Usage:  ./softwareupdater.py


Updated 1/23/2009 use servicelogger to log errors - Xuanhua (Sean)s Ren
"""

import sys
import os

import daemon

import repyhelper

import tuf
from tuf.client import updater

# I need to make a cachedir for repyhelper...
if not os.path.exists('softwareupdater.repyhelpercache'):
  os.mkdir('softwareupdater.repyhelpercache')

# prepend this to my python path
sys.path = ['softwareupdater.repyhelpercache'] + sys.path
repyhelpercachedir = repyhelper.set_importcachedir('softwareupdater.repyhelpercache')


# this is being done so that the resources accounting doesn't interfere with logging
from repyportability import *

import urllib      # to retrieve updates
import random
import shutil
import socket   # we'll make it so we don't hang...
import tempfile
import traceback    # For exception logging if the servicelogger fails.
import runonce
import harshexit  # Used for portablekill
import portable_popen


# Import servicelogger to do logging
import servicelogger

# This gives us do_sleep
import misc

repyhelper.translate_and_import("signeddata.repy")
repyhelper.translate_and_import("sha.repy")

# Armon: The port that should be used to update our time using NTP
TIME_PORT = 51234
TIME_PORT_2 = 42345

# set the repo dir
tuf.conf.settings.repo_meta_dir = "."

# where to get updates from
seattle_url = "http://blackbox.cs.washington.edu/tuf_updatesite/"

# Whether the nodemanager should be told not to daemonize when it is restarted.
# This is only to assist our automated tests.
run_nodemanager_in_foreground = False

# Whether the softwareupdater should run in the foreground or not. Default
# to yes.
run_softwareupdater_in_foreground = True

# If this is True, the software updater needs to restart itself. Once True, it
# will never be False again. This is global rather than in main() because the
# way that main() is currently written, an exception may escape from main and
# a loop in the global scope will catch it and call main() again.
restartme = False

# This code is in its own function called later rather than directly in the
# global scope right here because otherwise we need to ensure that the
# safe_log* methods are defined above this code or else they would cause a
# NameError because they aren't defined yet.
def safe_servicelogger_init():
  """
  This initializes the servicelogger in a way that will not throw an exception
  even if servicelogger.init() does.
  """
  # initialize the servicelogger to log on the softwareupdater file
  try:
    servicelogger.init("softwareupdater")
  except:
    # We assume that if servicelogger.init() fails, then safe_log will
    # fall back on using 'print' because servicelogger.log() calls
    # will throw a ValueError.
    safe_log("Servicelogger.init() failed. Will try to use stdout. The exception from servicelogger.init() was:")
    safe_log_last_exception()



def safe_log(message):
  """
  Log a message in a way that cannot throw an exception. First try to log using
  the servicelogger, then just try to print the message.
  """
  try:
    #f = open('/tmp/log.txt', 'a')
    #f.write(message + '\n')
    #f.close()
    servicelogger.log(message)
  except:
    pass



def safe_log_last_exception():
  """
  Log the last exception in a way that cannot throw an exception. First try to
  log using the servicelogger, then just try to print the message.
  """
  try:
    # Get the last exception in case the servicelogger fails.
    exceptionstr = traceback.format_exc()
  except:
    pass
  
  try:
    servicelogger.log_last_exception()
  except:
    try:
      print exceptionstr
    except:
      # As the standard output streams aren't closed, it would seem that this
      # should never happen. If it does, though, what can we do to log the
      # message, other than directly write to a file?
      pass


################### Begin Rsync ################### 
# I'd love to be able to put this in a separate module or repyify it, but 
# I'd need urllib...

class RsyncError(Exception):
  pass

def do_rsync(serverpath, destdir, tempdir, meta_dir="."):
  """
  <Purpose>
    This method is the one that attempts to download the metainfo file from
    the given serverpath, then uses that to attempt to do an update.  This
    method makes sure that the downloaded metainfo file is valid and signed
    correctly before changing any files.  Once the metainfo file is determined
    to be valid, it will then compare file hashes between the ones in the new
    metainfo file and the hashes of the files currently on disk.  If there is
    a difference, the new file is downloaded and added to the updated list.  
    Once all the new files have been downloaded, if they all did so 
    successfully they are then copied over the old ones, replacing them and
    completing the update of the files.  Then a list of the files updated is
    returned.

  <Arguments>
    serverpath - The url for the update site that we will try to contact.  
                 This should be the url of the directory that contains all of
                 the files that are being pushed as an update.
    destdir - This is the directory where the new files will end up if 
              everything goes well.
    tempdir - This is the directory where the new files will be initially
              downloaded to before their hashes are checked.  This is not
              cleaned up after finishing.

  <Exceptions>
    Will throw various socket errors if there is trouble getting a file from
    the webserver.
    Will throw an RsyncError if the downloaded metainfo is malformed, or if
    the hash of a downloaded file does not match the one listed in the 
    metainfo file.

  <Side Effects>
    Files will be downloaded to tempdir, and they might be copied over to
    destdir if everything is successful.

  <Returns>
    A list of files that have been updated.  The list is empty if nothing is
    to be updated.
  """
  # start the update
  safe_log('started update')

  # set the additional data that the repo needs to function
  safe_log('setting repo metadata')
  tuf.conf.settings.repo_meta_dir = meta_dir
  # directory structure:
  #   /
  #     /meta
  #     /targets
  #     data
  mirrors = {'repo': {'urlbase':serverpath,'metapath':'meta','targetspath':'targets','metacontent':['**'],'targetscontent':['**']}}
  
  # set up the repo and get the targets it provides
  safe_log('creating the repository and getting the targets')
  repo = updater.Repository('repo', mirrors)
  repo.refresh()
  all_targets = repo.get_all_targets()

  # get the full list of files needing an update
  safe_log('getting the list of files that need updates')
  files_to_update = []
  for target in all_targets:
    target.path = os.path.sep.join(target.path.split(os.path.sep)[1:])
    path = os.path.join(destdir, target.path)
    for hash_, digest in target.fileinfo['hashes'].items():
      local_hasher = tuf.hash.Digest(hash_)
      try:
        local_hasher.update_filename(path)
      except IOError:
        files_to_update.append(target)
      if local_hasher.format() != digest:
        files_to_update.append(target)
  #files_to_update = list(all_targets)

  # download each of the needed files
  safe_log('downloading the needed files')
  updatedfiles = []
  for target in files_to_update:
    safe_log("Repo tells us that %s needs updating" % target.path)
    temporary_path = os.path.join(tempdir, target.path)
    temporary_path_prefix = os.path.dirname(temporary_path)
    if not os.path.exists(temporary_path_prefix):
      os.makedirs(temporary_path_prefix)
    target.download(temporary_path)
    updatedfiles.append(target.path)

  # copy the files to the local dir...
  safe_log('updating')
  for filename in updatedfiles:
    temporary_path = os.path.join(tempdir, filename)
    destination_path = os.path.join(destdir, filename)
    destination_prefix = os.path.dirname(destination_path)
    if not os.path.exists(destination_prefix):
      os.mkdir(destination_prefix)
    shutil.copy(temporary_path, destination_path)
    
  # and go home
  safe_log('going home')
  return updatedfiles
  
################### End Rsync ################### 

# MUTEX  (how I prevent multiple copies)
# a new copy writes an "OK" file. if it's written the previous can exit.   
# a previous copy writes a "stop" file. if it's written the new copy must exit
# each new program has its own stop and OK files (listed by mutex number)
# 
# first program (fresh_software_updater)
#              get softwareupdater.new mutex
#              clean all mutex files
#              once in main, take softwareupdater.old, release softwareupdater.new
#              exit if we ever lose softwareupdater.old
#
# old program (restart_software_updater)
#              find an unused mutex 
#              starts new with arg that is the mutex
#              wait for some time
#              if "OK" file exists, release softwareupdater.old, remove it and exit
#              else write "stop" file
#              continue normal operation
#
# new program: (software_updater_start)
#              take softwareupdater.new mutex
#              initializes
#              if "stop" file exists, then exit
#              write "OK" file
#              while "OK" file exists
#                 if "stop" file exists, then exit
#              take softwareupdater.old, release softwareupdater.new
#              start normal operation
#


def init():
  """
  <Purpose>
    This method is here to do a runthrough of trying to update.  The idea is
    that if there is going to be a fatal error, we want to die immediately
    rather than later.  This way, when a node is updating to a flawed version,
    the old one won't die until we know the new one is working.  Also goes
    through the magic explained in the comment block above.

  <Arguments>
    None

  <Exceptions>
    See fresh_software_updater and software_updater_start.

  <Side Effects>
    If we can't get the lock, we will exit.
    We will hold the softwareupdater.new lock while trying to start, but if
    all goes well, we will release that lock and aquire the 
    softwareupdater.old lock.

  <Returns>
    None
  """
  # Note: be careful about making this init() method take too long. If it takes
  # longer to complete than the amount of time that restart_software_updater()
  # waits, then the new software updater will never be left running. Keep in
  # mind very slow systems and adjust the wait time in restart_software_updater()
  # if needed.
  
  gotlock = runonce.getprocesslock("softwareupdater.new")
  if gotlock == True:
    # I got the lock.   All is well...
    pass
  else:
    # didn't get the lock, and we like to be real quiet, so lets 
    # exit quietly
    sys.exit(55)

  # Close stdin because we don't read from stdin at all. We leave stdout and stderr
  # open because we haven't done anything to make sure that output to those (such as
  # uncaught python exceptions) go somewhere else useful.
  sys.stdin.close()

  # don't hang if the socket is slow (in some ways, this doesn't always work)
  # BUG: http://mail.python.org/pipermail/python-list/2008-January/471845.html
  socket.setdefaulttimeout(10)

  # time to handle startup (with respect to other copies of the updater
  if len(sys.argv) == 1 or sys.argv[-1] == 'debug':
    # I was called with no arguments, must be a fresh start...
    fresh_software_updater()
  else:
    # the first argument is our mutex number...
    software_updater_start(sys.argv[1])


def software_updater_start(mutexname):
  """
  <Purpose>
    When restarting the software updater, this method is called in the new 
    one.  It will write an OK file to let the original know it has started,
    then will wait for the original to acknowledge by either removing the OK
    file, meaning we should carry on, or by writing a stop file, meaning we
    should exit.  Carrying on means getting the softwareupdater.old lock, and
    releasing the softwareupdater.new lock, then returning.
  
  <Arguments>
    mutexname - The new software updater was started with a given mutex name,
                which is used to uniquely identify the stop and OK files as
                coming from this softwareupdater.  This way the old one can
                know that the softwareupdater it started is the one that is
                continueing on.

  <Exceptions>
    Possible Exception creating the OK file.

  <Side Effects>
    Acquires the softwareupdater.old lock and releases the softwareupdater.new
    lock.

  <Return>
    None
  """

  safe_log("[software_updater_start] This is a new software updater process started by an existing one.")

  # if "stop" file exists, then exit
  if os.path.exists("softwareupdater.stop."+mutexname):
    safe_log("[software_updater_start] There's a stop file. Exiting.")
    open('/tmp/log.txt', 'w').write("HERE")
    sys.exit(2)

  # write "OK" file
  file("softwareupdater.OK."+mutexname,"w").close()
  
  # while "OK" file exists
  while os.path.exists("softwareupdater.OK."+mutexname):
    safe_log("[software_updater_start] Waiting for the file softwareupdater.OK."+mutexname+" to be removed.")
    misc.do_sleep(1.0)
    # if "stop" file exists, then exit
    if os.path.exists("softwareupdater.stop."+mutexname):
      sys.exit(3)

  # Get the process lock for the main part of the program.
  gotlock = runonce.getprocesslock("softwareupdater.old")
  # Release the lock on the initialization part of the program
  runonce.releaseprocesslock('softwareupdater.new')
  if gotlock == True:
    # I got the lock.   All is well...
    pass
  else:
    if gotlock:
      safe_log("[software_updater_start] Another software updater old process (pid: "+str(gotlock)+") is running")
      sys.exit(55)
    else:
      safe_log("[software_updater_start] Another software updater old process is running")
      sys.exit(55)
 
  safe_log("[software_updater_start] This software updater process is now taking over.")
 
  # start normal operation
  return


# this is called by either the installer or the program that handles starting
# up on boot
def fresh_software_updater():
  """
  <Purpose>
    This function is ment to be called when starting a softwareupdater when no
    other is currently running.  It will clear away any outdated OK or stop
    files, then release the softwareupdater.new lock and acquire the
    softwareupdater.old lock.

  <Arguments>
    None
 
  <Exceptions>
    Possible exception if there is a problem removing the OK/stop files.    

  <Side Effects>
    The softwareupdater.new lock is released.
    The softwareupdater.old lock is acquired.
    All old OK and stop files are removed.

  <Returns>
    None
  """
  # clean all mutex files
  for filename in os.listdir('.'):
    # Remove any outdated stop or OK files...
    if filename.startswith('softwareupdater.OK.') or filename.startswith('softwareupdater.stop.'):
      os.remove(filename)

  # Get the process lock for the main part of the program.
  gotlock = runonce.getprocesslock("softwareupdater.old")
  # Release the lock on the initialization part of the program
  runonce.releaseprocesslock('softwareupdater.new')
  if gotlock == True:
    # I got the lock.   All is well...
    pass
  else:
    if gotlock:
      safe_log("[fresh_software_updater] Another software updater old process (pid: "+str(gotlock)+") is running")
      sys.exit(55)
    else:
      safe_log("[fresh_software_updater] Another software updater old process is running")
      sys.exit(55)
  # Should be ready to go...

  safe_log("[fresh_software_updater] Fresh software updater started.")


def get_mutex():
  # do this until we find an unused file mutex.   we should find one 
  # immediately with overwhelming probability
  while True:
    randtoken = str(random.random())
    if not os.path.exists("softwareupdater.OK."+randtoken) and not os.path.exists("softwareupdater.stop."+randtoken):
      return randtoken
  

def restart_software_updater():
  """
  <Purpose>
    Attempts to start a new software updater, and will exit this one if the
    new one seems to start successfully.  If the new one does not start
    successfully, then we just return.

  <Arguments>
    None

  <Exceptions>
   Possible exception if there is problems writing the OK file.
 
  <Side Effects>
    If all goes well, a new softwareupdater will be started, and this one will
    exit.

  <Returns>
    In the successful case, it will not return.  If the new softwareupdater does
    not start correctly, we will return None.
  """

  safe_log("[restart_software_updater] Attempting to restart software updater.")

  # find an unused mutex 
  thismutex = get_mutex()

  # starts new with arg that is the mutex 
  junkupdaterobject = portable_popen.Popen([sys.executable,"softwareupdater.py",thismutex])

  # wait for some time (1 minute) for them to init and stop them if they don't
  for junkcount in range(30):
    misc.do_sleep(2.0)

    # if "OK" file exists, release softwareupdater.old, remove OK file and exit
    if os.path.exists("softwareupdater.OK."+thismutex):
      runonce.releaseprocesslock('softwareupdater.old')
      os.remove("softwareupdater.OK."+thismutex)
      # I'm happy, it is taking over
      safe_log("[restart_software_updater] The new instance of the software updater is running. This one is exiting.")
      sys.exit(10)

  # else write "stop" file because it failed...
  file("softwareupdater.stop."+thismutex,"w").close()

  safe_log("[restart_software_updater] Failed to restart software updater. This instance will continue.")

  # I continue normal operation
  return



def restart_client(filenamelist):
  """
  <Purpose>
    Restarts the node manager.

  <Arguments>
    filenamelist - Currently not used, but is included for possible future use.

  <Exceptions>
    None

  <Side Effects>
    The current node manager is killed, and a new one is started.

  <Returns>
    None.
  """
  # kill nmmain if it is currently running
  retval = runonce.getprocesslock('seattlenodemanager')
  if retval == True:
    safe_log("[restart_client] Obtained the lock 'seattlenodemanager', it wasn't running.")
    # I got the lock, it wasn't running...
    # we want to start a new one, so lets release
    runonce.releaseprocesslock('seattlenodemanager')
  elif retval == False:
    # Someone has the lock, but I can't do anything...
    safe_log("[restart_client] The lock 'seattlenodemanager' is held by an unknown process. Will try to start it anyways.")
  else:
    safe_log("[restart_client] Stopping the nodemanager.")
    # I know the process ID!   Let's stop the process...
    harshexit.portablekill(retval)
  
  safe_log("[restart_client] Starting the nodemanager.")

  # run the node manager.   I rely on it to do the smart thing (handle multiple
  # instances, etc.)
  nm_restart_command_args_list = [sys.executable, "nmmain.py"]
  
  if run_nodemanager_in_foreground:
    nm_restart_command_args_list.append('--foreground')
  
  junkprocessobject = portable_popen.Popen(nm_restart_command_args_list)
  
  # I don't do anything with the processobject.  The process will run for some 
  # time, perhaps outliving me (if I'm updated first)


def main(debug=False):
  """
  <Purpose>
    Has an infinite loop where we sleep for 5-55 minutes, then check for 
    updates.  If an update happens, we will restart ourselves and/or the
    node manager as necesary.
    
  <Arguments>
    None

  <Exceptions>
    Any non-RsyncError exceptions from do_rsync.

  <Side Effects>
    If there is an update on the update site we are checking, it will be 
    grabbed eventually.

  <Return>
    Will not return.  Either an exception will be thrown, we exit because we
    are restarting, or we loop infinitely.
  """

  global restartme

  # This is similar to init only:
  #   1) we loop / sleep
  #   2) we restart ourselves if we are updated
  #   3) we restart our client if they are updated

  while True:
    if debug:
      rint = 1
    else:
      rint = random.randint(10, 110)
    for junk in range(rint):
      # We need to wake up every 30 seconds otherwise we will take
      # the full 5-55 minutes before we die when someone tries to
      # kill us nicely.
      misc.do_sleep(1)
      # Make sure we still have the process lock.
      # If not, we should exit
      if not runonce.stillhaveprocesslock('softwareupdater.old'):
        safe_log('[main] We no longer have the processlock\n')
        sys.exit(55)

    # set the softwareurl based on whether debug is set
    if debug:
      softwareurl = 'http://localhost:12345'
    else:
      softwareurl = seattle_url

    # Make sure that if we failed somehow to restart, we keep trying before
    # every time we try to update. - Brent
    if restartme:
      restart_software_updater()
      
    # where I'll put files...
    tempdir = tempfile.mkdtemp()+"/"


    # I'll clean this up in a minute
    try:
      updatedlist = do_rsync(softwareurl, "./",tempdir)
    except Exception:
      safe_log_last_exception()
      # oops, hopefully this will be fixed next time...
      continue

    finally:
      shutil.rmtree(tempdir)

    safe_log('[main] rsync with server yielded the following changes: %s' % str(updatedlist))
    # no updates   :)   Let's wait again...
    if updatedlist == []:
      continue

    clientlist = updatedlist[:]
    if 'softwareupdater.py' in clientlist:
      restartme = True
      clientlist.remove('softwareupdater.py')

    # if the client software changed, let's update it!
    if clientlist != []:
      restart_client(clientlist)

    # oh! I've changed too.   I should restart...   search for MUTEX for info
    if restartme:
      restart_software_updater()

    if debug: break



def read_environmental_options():
  """
  This doesn't read command line options. It reads environment variable
  options. The reason is because the software updater currently expects that
  any first command line arg is the name of a mutex used by an already running
  software updater. I don't see any good reason to risk changing more than is
  needed until more major changes are being made to the software updater.
  This also makes it so that we don't have to bother passing the option through
  to restarts of the softwareupdater.
  """
  try:
    global run_nodemanager_in_foreground
    global run_softwareupdater_in_foreground
    if 'SEATTLE_RUN_NODEMANAGER_IN_FOREGROUND' in os.environ:
      run_nodemanager_in_foreground = True
    if os.environ.get('SEATTLE_RUN_SOFTWAREUPDATER_IN_FOREGROUND', True) == "False":
      run_softwareupdater_in_foreground = False
  except:
    # The defaults here are safe, so if something went wrong in
    # the code above, however unlikely, let's ignore it.
    pass




if __name__ == '__main__':
  from sys import argv

  # find out whether we're debugging or not
  if 'debug' in argv[-1]:
    debug = True
  else:
    debug = False

  if 'debugrestart' in argv[-1]:
    loop = True
  else:
    loop = False

  # get our env options
  read_environmental_options()
  if not run_softwareupdater_in_foreground and not debug:
    daemon.daemonize()

  # Initialize the service logger.
  safe_servicelogger_init()
  
  # problems here are fatal.   If they occur, the old updater won't stop...
  try:
    init()
  except Exception, e:
    safe_log_last_exception()
    raise e

  # in case there is an unexpected exception, continue (we'll sleep first thing
  # in main)
  while True:
    try:
      main(debug)
    except SystemExit:
      # If there is a SystemExit exception, we should probably actually exit...
      raise
    except Exception, e:
      # Log the exception and let main() run again.
      safe_log_last_exception()
      # Sleep a little to prevent a fast loop if the exception is happening
      # before any other calls to do_sleep().
      misc.do_sleep(1.0)
    if not loop: break
