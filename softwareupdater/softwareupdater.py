""" 
Author: Justin Cappos

Start Date: August 4, 2008

Description:
A software updater for the node manager.   The focus is to make it secure, 
robust, and simple (in that order).

Usage:  ./softwareupdater.py


Updated 1/23/2009 use servicelogger to log errors - Xuanhua (Sean)s Ren


"""

# this is being done so that the resources accounting doesn't interfere with logging
from repyportability import *

import sys

import urllib      # to retrieve updates
import os   # needed for remove and path.exists
import subprocess   # used to start an experiment
import random
import shutil
import socket   # we'll make it so we don't hang...
import tempfile
import runonce
import nonportable  # Used for sys.exit

import repyhelper

# Import servicelogger to do logging
import servicelogger

# This gives us do_sleep
import misc

repyhelper.translate_and_import("signeddata.repy")
repyhelper.translate_and_import("sha.repy")

# Armon: The port that should be used to update our time using NTP
TIME_PORT = 51234
TIME_PORT_2 = 42345

softwareurl = "http://seattle.cs.washington.edu/couvb/updatesite/0.1/"

# embedded this because it seems easier to update it along with this file
# Every computer running Seattle will have this same public key, and will trust
# files signed by this key.
softwareupdatepublickey = {'e':82832270266597330072676409661763231354244983360850404742185516224735762244569727906889368190381098316859532462559839005559035695542121011189767114678746829532642015227757061325811995458461556243183965254348908097559976740460038862499279411461302045605434778587281242796895759723616079286531587479712074947611, 'n':319621204384190529645831372818389656614287850643207619926347176392517761801427609535545760457027184668587674034177692977122041230031985031724339016854308623931563908276376263003735701277100364224187045110833742749159504168429702766032353498688487937836208653017735915837622736764430341063733201947629404712911592942893299407289815035924224344585640141382996031910529762480483482480840200108190644743566141062967857181966489101744929170144756204101501136046697030104623523067263295405505628760205318871212056879946829241448986763757070565574197490565540710448548232847380638562809965308287901471553677400477022039092783245720343246522144179191881098268618863594564939975401607436281396130900640289859459360314214324155479461961863933551434423773320970748327521097336640702078449006530782991443968680573263568609595969967079764427272827202433035192418494908184888678872217792993640959292902948045622147093326912328933981365394795535990933982037636876825043938697362285277475661382202880481400699819441979130858152032120174957606455858082332914545153781708896942610940094268714863253465554125515897189179557899347310399568254877069082016414203023408461051519104976942275899720740657969311479534442473551582563833145735116565451064388421}


# initialize the servicelogger to log on the softwareupdater file
servicelogger.init("softwareupdater")


def get_file_hash(filename):
  fileobj = file(filename, 'rb')
  filedata = fileobj.read()
  fileobj.close()

  return sha_hexhash(filedata)



# We'll use this to get a file.   If it doesn't download in a reasonable time, 
# we'll fail. (BUG: doesn't do this yet.   I use timeouts, but they don't
# always work)
def safe_download(serverpath, filename, destdir, filesize):
  try:
    urllib.urlretrieve(serverpath+filename,destdir+filename)
    return True
  except Exception,e:
    servicelogger.log(str(e) + ' ' + serverpath+filename)
    servicelogger.log_last_exception()
    return False
 
#  # how much we have left to download
#  remainingsize = filesize
#
#  # get a file-like object for the URL...
#  safefo = urllib.urlopen(filename)
#
#  # always close after this...
#  try:
#    # download up to "filesize" worth of data...   
#    # BUG: We also should check to see if this is too slow...
#    mydata
#  
#  
#  finally:
#    try:
#      safefo.close()
#    except:
#      pass




################### Begin Rsync ################### 
# I'd love to be able to put this in a separate module or repyify it, but 
# I'd need urllib...

class RsyncError(Exception):
  pass




def do_rsync(serverpath, destdir, tempdir):
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

  # get the metainfo (like a directory listing)
  safe_download(serverpath, "metainfo", tempdir, 1024*32)

  # read the file data into a string
  newmetafileobject = file(tempdir+"metainfo")
  newmetafiledata = newmetafileobject.read()
  newmetafileobject.close()

  # Incorrectly signed, we don't update...
  if not signeddata_issignedcorrectly(newmetafiledata, softwareupdatepublickey):
    servicelogger.log("New metainfo not signed correctly.  Not updating")
    return []

  try:
    # read in the old file
    oldmetafileobject = file(destdir+"metainfo")
    oldmetafiledata = oldmetafileobject.read()
    oldmetafileobject.close()
  except:
    # The old file has problems.   We'll use the new one since it's signed
    pass

  else:
    try:
      # Armon: Update our time via NTP, before we check the meta info
      time_updatetime(TIME_PORT)
    except:
      time_updatetime(TIME_PORT_2)
    
    # they're both good.   Let's compare them...
    shoulduse, reasons = signeddata_shouldtrust(oldmetafiledata,newmetafiledata,softwareupdatepublickey)

    if shoulduse == True:
      # great!   All is well...
      pass
    elif shoulduse == None:
      # hmm, a warning...   
      if len(reasons) == 1 and reasons[0] == 'Cannot check expiration':
        # we should probably allow this.  The node may be offline 
        servicelogger.log("Warning:"+str(reasons))
        #print "Warning:"+str(reasons)
        pass
      elif 'Timestamps match' in reasons:
        # Already seen this one...
        servicelogger.log(reasons)
        #print str(reasons)
        return []

    elif shoulduse == False:
      if 'Public keys do not match' in reasons:
        # If the only complaint is that the oldmetafiledata and newmetafiledata
        # are signed by different keys, this is actually OK at this point.  We
        # know that the newmetafiledata was correctly signed with the key held
        # within this softwareupdater, so this should actually only happen when
        # the oldmetafiledata has an out of date signature.  However, we do 
        # still need to make sure there weren't any other fatal errors that 
        # we should distrust. - Brent
        reasons.remove('Public keys do not match')
        for comment in reasons:
          if comment in signeddata_fatal_comments:
            # If there is a different fatal comment still there, still log it
            # and don't perform the update.
            servicelogger.log(reasons)
            #print str(reasons)
            return []
            
          if comment in signeddata_warning_comments:
            # If there is a different warning comment still there, log the
            # warning.  We will take care of specific behavior shortly.
            servicelogger.log(comment)
            
        if 'Timestamps match' in reasons:
          # Act as we do above when timestamps match
          # Already seen this one...
          servicelogger.log(reasons)
          #print str(reasons)
          return []
      else:
        # Let's assume this is a bad thing and exit
        servicelogger.log(reasons)
        return []

  # now it's time to update
  updatedfiles = [ "metainfo" ]

  for line in file(tempdir+"metainfo"):

    # skip comments
    if line[0] == '#':
      continue
 
    # skip signature parts
    if line[0] == '!':
      continue
 
    # skip blank lines
    if line.strip() == '':
      continue

    linelist = line.split()
    if len(linelist)!= 3:
      raise RsyncError, "Malformed metainfo line: '"+line+"'"

    filename, filehash, filesize = linelist
    
    # if the file is missing or the hash is different, we want to download...
    if not os.path.exists(destdir+filename) or get_file_hash(destdir+filename) != filehash:
      # get the file
      safe_download(serverpath, filename, tempdir, filesize)

      # oh crap!   The hash doesn't match what we thought
      if get_file_hash(tempdir+filename) != filehash:
        servicelogger.log("Hash mismatch on file '"+filename+"':" + filehash +
            " vs " + get_file_hash(tempdir+filename))
        shutil.copy(tempdir+filename, '/homes/iws/couvb/'+filename+'.oddness') 
        raise RsyncError, "Hash of file '"+filename+"' does not match information in metainfo file"

      # put this file in the list of files we need to update
      updatedfiles.append(filename)      


  # copy the files to the local dir...
  for filename in updatedfiles:
    shutil.copy(tempdir+filename, destdir+filename)
    
  # done!   We updated the files
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
    If we can't get the lock, we will exit.  The standard streams are closed.
    We will hold the softwareupdater.new lock while trying to start, but if
    all goes well, we will release that lock and aquire the 
    softwareupdater.old lock.

  <Returns>
    None
  """
  gotlock = runonce.getprocesslock("softwareupdater.new")
  if gotlock == True:
    # I got the lock.   All is well...
    pass
  else:
    # didn't get the lock, and we like to be real quiet, so lets 
    # exit quietly
    sys.exit(55)

  # Close the standard streams so the user doesnt have to worry about it.
  sys.stdin.close()
  sys.stdout.close()
  sys.stderr.close()

  # don't hang if the socket is slow (in some ways, this doesn't always work)
  # BUG: http://mail.python.org/pipermail/python-list/2008-January/471845.html
  socket.setdefaulttimeout(10)
  
  # remove any old / broken test dirs...
  if os.path.exists("download.test"):
    shutil.rmtree("download.test")
  
  # create the test dir...
  os.mkdir("download.test")
  # copy my metainfo file into there
  shutil.copy("metainfo","download.test")

  # do an update to that directory.   If I don't see an unexpected error, we 
  # should be in good shape
  tempdir = tempfile.mkdtemp()+"/"
  try:
    do_rsync(softwareurl, "download.test/",tempdir)
  except Exception:
     # We continue if this happens later, 
     # so we should do so now as well
     pass
  finally:
    shutil.rmtree(tempdir)
      
  # remove the test directory
  shutil.rmtree("download.test")

  # time to handle startup (with respect to other copies of the updater
  if len(sys.argv) == 1:
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
  # if "stop" file exists, then exit
  if os.path.exists("softwareupdater.stop."+mutexname):
    sys.exit(2)

  # write "OK" file
  file("softwareupdater.OK."+mutexname,"w").close()
  
  # while "OK" file exists
  while os.path.exists("softwareupdater.OK."+mutexname):
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
      servicelogger.log("Another software updater old process (pid: "+str(gotlock)+") is running")
      sys.exit(55)
    else:
      servicelogger.log("Another software updater old process is running")
      sys.exit(55)
  
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
      servicelogger.log("Another software updater old process (pid: "+str(gotlock)+") is running")
      sys.exit(55)
    else:
      servicelogger.log("Another software updater old process is running")
      sys.exit(55)
  # Should be ready to go...



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

  # find an unused mutex 
  thismutex = get_mutex()

  # starts new with arg that is the mutex 
  junkupdaterobject = subprocess.Popen(["python","softwareupdater.py",thismutex])

  # wait for some time (1 minute) for them to init and stop them if they don't
  for junkcount in range(30):
    misc.do_sleep(2.0)

    # if "OK" file exists, release softwareupdater.old, remove OK file and exit
    if os.path.exists("softwareupdater.OK."+thismutex):
      runonce.releaseprocesslock('softwareupdater.old')
      os.remove("softwareupdater.OK."+thismutex)
      # I'm happy, it is taking over
      sys.exit(10)

  # else write "stop" file because it failed...
  file("softwareupdater.stop."+thismutex,"w").close()

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
    # I got the lock, it wasn't running...
    # we want to start a new one, so lets release
    runonce.releaseprocesslock('seattlenodemanager')
  elif retval == False:
    # Someone has the lock, but I can't do anything...
    servicelogger.log("The lock 'seattlenodemanager' is held by an unknown process")
  else:
    # I know the process ID!   Let's stop the process...
    nonportable.portablekill(retval)
  

  # run the node manager.   I rely on it to do the smart thing (handle multiple
  # instances, etc.)
  junkprocessobject = subprocess.Popen(["python","nmmain.py"])
  
  # I don't do anything with the processobject.  The process will run for some 
  # time, perhaps outliving me (if I'm updated first)


def main():
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

  # This is similar to init only:
  #   1) we loop / sleep
  #   2) we restart ourselves if we are updated
  #   3) we restart our client if they are updated


  # If this is true, I need to be restarted...   Once True it will never be 
  # False again
  restartme = False

  while True:
    # sleep for 5-55 minutes 
    for junk in range(random.randint(10, 110)):
      # We need to wake up every 30 seconds otherwise we will take
      # the full 5-55 minutes before we die when someone tries to
      # kill us nicely.
      misc.do_sleep(30)
      # Make sure we still have the process lock.
      # If not, we should exit
      if not runonce.stillhaveprocesslock('softwareupdater.old'):
        servicelogger.log('We no longer have the processlock\n')
        sys.exit(55)


    # Make sure that if we failed somehow to restart, we keep trying before
    # every time we try to update. - Brent
    if restartme:
      restart_software_updater()
      
    # where I'll put files...
    tempdir = tempfile.mkdtemp()+"/"


    # I'll clean this up in a minute
    try:
      updatedlist = do_rsync(softwareurl, "./",tempdir)
    except RsyncError:
      # oops, hopefully this will be fixed next time...
      continue

    finally:
      shutil.rmtree(tempdir)

    # no updates   :)   Let's wait again...
    if updatedlist == []:
      continue

   
    # if there were updates, the metainfo file should be one of them...
    assert('metainfo' in updatedlist)

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
    

if __name__ == '__main__':
  # problems here are fatal.   If they occur, the old updater won't stop...
  try:
    init()
  except Exception, e:
    servicelogger.log_last_exception()
    raise e

  # in case there is an unexpected exception, continue (we'll sleep first thing
  # in main)
  while True:
    try:
      main()
    except SystemExit:
      # If there is a SystemExit exception, we should probably actually exit...
      raise
    except Exception, e:
      servicelogger.log_last_exception()
      # Otherwise we will keep on trucking
      pass
