
###### shared section ########

# Module that ensures application code runs only once...
import os

# allow me to specify error names instead of numbers
import errno

# need to know the os type...
import platform

# printing to sys.stderr
import sys

# returns a process lock (True) or if the lock is held returns the PID of the 
# process holding the lock
# NOTE: one must call stillhaveprocesslock periodically to guard against a user
# deleting the tmp file
def stillhaveprocesslock(lockname):
  #print >> sys.stderr, 'Verifying we still have lock for '+lockname
  val =  getprocesslock(lockname) 
  return val == os.getpid() or val == True

def getprocesslock(lockname):
  ostype = platform.system()
  if ostype == 'Windows' or ostype == 'Microsoft':
    #print >> sys.stderr, 'Getting some Windows lockmutex'
    return getprocesslockmutex(lockname)
  elif ostype == 'Linux' or ostype == 'Darwin' or 'BSD' in ostype:
    # unfortunately, it seems *NIXes differ on whether O_EXLOCK is supported
    try:
      os.O_EXLOCK
    except AttributeError:
      #print >> sys.stderr, 'Getting flock for '+lockname
      return getprocesslockflock(lockname)   
    else:
      #print >> sys.stderr, 'Getting o_exlock for '+lockname
      return getprocesslocko_exlock(lockname)
  else:
    raise Exception, 'Unknown operating system:'+ostype


def releaseprocesslock(lockname):
  ostype = platform.system()
  if ostype == 'Windows' or ostype == 'Microsoft':
    return releaseprocesslockmutex(lockname)
  elif ostype == 'Linux' or ostype == 'Darwin' or 'BSD' in ostype:
    # unfortunately, it seems *NIXes differ on whether O_EXLOCK is supported
    try:
      os.O_EXLOCK
    except AttributeError:
      #print >> sys.stderr, 'Releasing flock for '+lockname
      return releaseprocesslockflock(lockname)   
    else:
      #print >> sys.stderr, 'Releasing o_exlock for '+lockname
      return releaseprocesslocko_exlock(lockname)
  else:
    raise Exception, 'Unknown operating system:'+ostype



###### MAC / LINUX section ########

# NOTE: In order to avoid leaking file descriptors, if I've tried to get the
# process lock before I'll close the old one on success or the new one on 
# failure
oldfiledesc = {}

# BUG FIX:   sometimes the PID is shorter than others.   Notice, I don't
# truncate the file, so I need to ensure I overwrite the digits of a  pid 
# that could be more digits than mine...
pidendpadding = "      "

# this works on a smattering of systems...
def getprocesslocko_exlock(lockname):
  # the file we'll use
  lockfn = "/tmp/runoncelock."+lockname
    
  try:
    fd = os.open(lockfn,os.O_CREAT | os.O_RDWR | os.O_EXLOCK | os.O_NONBLOCK)
    #print >> sys.stderr, 'o_exlock get file descriptor == '+str(fd)

    # See above (under definition of pidendpadding) about why this is here...
    os.write(fd,str(os.getpid())+pidendpadding)
    #print >> sys.stderr, 'wrote pid('+str(os.getpid())+') to o_exlock file'
    if lockname in oldfiledesc:
      os.close(oldfiledesc[lockname])
    oldfiledesc[lockname] = fd
    return True
  except (OSError,IOError), e:
    if e[0] == errno.EACCES or e[0] == errno.EAGAIN:
      # okay, they must have started already.  
      pass 
      #print >> sys.stderr, 'Getting o_exlock failed, must have already started'
    else:
      # we weren't expecting this...
      #print >> sys.stderr, 'badness going down in getting o_exlock'
      raise
  # Let's return the PID
  fo = open(lockfn)
  pidstring = fo.read()
  fo.close()
  #print >> sys.stderr, 'pid '+pidstring+' has the o_exlock for '+lockname
  return int(pidstring)



def getprocesslockflock(lockname):
  global oldfiledesc
  # the file we'll use
  lockfn = "/tmp/runoncelock."+lockname
    
  try:
    fd = os.open(lockfn,os.O_CREAT | os.O_RDWR | os.O_NONBLOCK)
    #print >> sys.stderr, 'flock get file descriptor == '+str(fd)
  except (OSError, IOError), e:
    if e[0] == errno.EACCES or e[0] == errno.EAGAIN:
      # okay, they must have started already.
      pass   
      #print >> sys.stderr, 'Getting flock open failed, must have already started'
    else:
      #print >> sys.stderr, 'badness going down in opening for flock'
      raise
  else:
    try:
      import fcntl
      fcntl.flock(fd,fcntl.LOCK_EX | fcntl.LOCK_NB)
      # See above (under definition of pidendpadding) about why this is here...
      os.write(fd,str(os.getpid())+pidendpadding)
      #print >> sys.stderr, 'wrote pid ('+str(os.getpid())+') to flocked file'
      if lockname in oldfiledesc:
        os.close(oldfiledesc[lockname])
      oldfiledesc[lockname] = fd
      return True
    except (OSError, IOError), e:
      os.close(fd)
      if e[0] == errno.EACCES or e[0] == errno.EAGAIN:
        # okay, they must have started already.
        pass
        #print >> sys.stderr, 'Getting flock fcntl.flock failed, must have already started'
      else:
        # we weren't expecting this...
        #print >> sys.stderr, 'badness going down in fcntl.flock for flock'
        raise

  # Let's return the PID
  fo = open(lockfn)
  pidstring = fo.read()
  fo.close()
  #print >> sys.stderr, 'pid '+pidstring+' has the flock for '+lockname
  return int(pidstring)


def releaseprocesslocko_exlock(lockname):
  if lockname in oldfiledesc:
    os.close(oldfiledesc[lockname])
    del oldfiledesc[lockname]
    #print >> sys.stderr, 'removed o_exlock for '+lockname
  

def releaseprocesslockflock(lockname):
  if lockname in oldfiledesc:
    import fcntl
    fcntl.flock(oldfiledesc[lockname],fcntl.LOCK_UN)
    os.close(oldfiledesc[lockname])
    del oldfiledesc[lockname]
    #print >> sys.stderr, 'removed flock for '+lockname





##### WINDOWS SECTION ##########

try:
  import windows_api
  windowsAPI = windows_api
except:
  try:
    import windows_ce_api
    windowsAPI = windows_ce_api
  except:
    windowsAPI = None
    pass
  pass

# NOTE: in Windows, only the current user can get the PID for their process.
# This makes sense because only the current user should uninstall their code.

# I need to ensure I don't close the handle to the mutex.   I'll make it a
# global so it isn't cleaned up.
mutexhandle = {}


# this is a helper function that opens the right location in the registry
# if write is set to true, it creates any missing items.
def openkey(basekey, keylist, write=False):
  import _winreg
  if keylist == []:
    return basekey
  else:
    if write:
      try:
        thisKey = _winreg.OpenKey(basekey, keylist[0], 0, _winreg.KEY_SET_VALUE | _winreg.KEY_WRITE) 
      except WindowsError:
        # need to create the key
        thisKey = _winreg.CreateKey(basekey, keylist[0])
      # return the remaining keys
      return openkey(thisKey, keylist[1:], write)

    else:
      # opening a key for reading...
      # I allow this call to raise an WindowsError for a non-existent key
      thisKey = _winreg.OpenKey(basekey, keylist[0], 0, _winreg.KEY_READ)
      return openkey(thisKey, keylist[1:], write)
        

# How many milliseconds to wait to acquire mutex?
WAIT_TIME = 200

# return True on success, and either the pid of the locking process or False 
# on failure.
def getprocesslockmutex(lockname):
  import _winreg
  regkeyname = r"runonce."+lockname

  # traverse registry path
  registrypath = ["SOFTWARE","UW","Seattle","1.0"]

  # locked, do we own the mutex?
  locked = False

  # Does a handle already exist?
  if lockname in mutexhandle:
    # Lets try to get ownership of it
    locked = windowsAPI.acquireMutex(mutexhandle[lockname], WAIT_TIME)
  else:
    # Lets create the mutex, then get ownership
    try:
      mutexhandle[lockname] = windowsAPI.createMutex('Global\\runonce.'+lockname)
      locked = windowsAPI.acquireMutex(mutexhandle[lockname], WAIT_TIME)
    except windowsAPI.FailedMutex:
      # By default, we don't have the lock, so its okay
      pass

  # We own it!
  if locked:
    # Okay, it worked.   Now write something in the registry so others
    # can find the PID
    registryconn = _winreg.ConnectRegistry(None,_winreg.HKEY_CURRENT_USER)

    # get the place to write
    thekey = openkey(registryconn, registrypath, write=True) 

    try:
      _winreg.SetValueEx(thekey,regkeyname,0, _winreg.REG_SZ, str(os.getpid()))
    except EnvironmentError,e:                                          
      print thekey, regkeyname, 0, _winreg.REG_SZ, os.getpid()
      print "Encountered problems writing into the Registry..."+str(e)
      raise

    _winreg.CloseKey(thekey)
    _winreg.CloseKey(registryconn)

    return True      

  # figure out the pid with the lock...
  registryconn = _winreg.ConnectRegistry(None,_winreg.HKEY_CURRENT_USER)
  try:
    thekey = openkey(registryconn, registrypath, write=False)
  except WindowsError:
    # the key didn't exist.  Must be stored under another user...
    return False

  # I'll return once there are no more values or I've found the key...
  try:
    # BUG: is there a better way to do this?
    # shouldn't have more than 1024 keys...
    for num in range(1024):
      valuename, data, datatype = _winreg.EnumValue(thekey,num)
      if valuename == regkeyname:
        return int(data)

    else:
      # didn't find the key
      return False

  except EnvironmentError, e:                                          
    # not found...   This is odd.   The registry path is there, but no key...
    return False

  finally:
    _winreg.CloseKey(thekey)
    _winreg.CloseKey(registryconn)

# Release a windows mutex
def releaseprocesslockmutex(lockname):
  # Does the handle exist?
  if lockname in mutexhandle:
    try:
      # Release the mutex
      windowsAPI.releaseMutex(mutexhandle[lockname])
    except windowsAPI.NonOwnedMutex, e:
      # Its fine to release when we don't own, handle is not release on failure
      pass
