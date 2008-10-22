
###### shared section ########

# Module that ensures application code runs only once...
import os

# allow me to specify error names instead of numbers
import errno

# need to know the os type...
import platform

# returns a process lock (True) or if the lock is held returns the PID of the 
# process holding the lock
# NOTE: one must call stillhaveprocesslock periodically to guard against a user
# deleting the tmp file
def stillhaveprocesslock(lockname):
  val =  getprocesslock(lockname) 
  return val == os.getpid()

def getprocesslock(lockname):
  ostype = platform.system()
  if ostype == 'Windows' or ostype == 'Microsoft':
    return getprocesslockmutex(lockname)
  elif ostype == 'Linux' or ostype == 'Darwin' or 'BSD' in ostype:
    # unfortunately, it seems *NIXes differ on whether O_EXLOCK is supported
    try:
      os.O_EXLOCK
    except AttributeError:
      return getprocesslockflock(lockname)   
    else:
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
      return releaseprocesslockflock(lockname)   
    else:
      return releaseprocesslocko_exlock(lockname)
  else:
    raise Exception, 'Unknown operating system:'+ostype



###### MAC / LINUX section ########

# NOTE: In order to avoid leaking file descriptors, if I've tried to get the
# process lock before I'll close the old one on success or the new one on 
# failure
oldfiledesc = {}

# this works on a smattering of systems...
def getprocesslocko_exlock(lockname):
  # the file we'll use
  lockfn = "/tmp/runoncelock."+lockname
    
  try:
    fd = os.open(lockfn,os.O_CREAT | os.O_RDWR | os.O_EXLOCK | os.O_NONBLOCK)
    os.write(fd,str(os.getpid()))
    if lockname in oldfiledesc:
      os.close(oldfiledesc[lockname])
    oldfiledesc[lockname] = fd
    return True
  except (OSError,IOError), e:
    if e[0] == errno.EACCES or e[0] == errno.EAGAIN:
      # okay, they must have started already.   
      pass
    else:
      # we weren't expecting this...
      raise
  # Let's return the PID
  fo = open(lockfn)
  pidstring = fo.read()
  fo.close()
  return int(pidstring)



def getprocesslockflock(lockname):
  global oldfiledesc
  # the file we'll use
  lockfn = "/tmp/runoncelock."+lockname
    
  try:
    fd = os.open(lockfn,os.O_CREAT | os.O_RDWR | os.O_NONBLOCK)
  except (OSError, IOError), e:
    if e[0] == errno.EACCES or e[0] == errno.EAGAIN:
      # okay, they must have started already.   
      pass
    else:
      raise
  else:
    try:
      import fcntl
      fcntl.flock(fd,fcntl.LOCK_EX | fcntl.LOCK_NB)
      os.write(fd,str(os.getpid()))
      if lockname in oldfiledesc:
        os.close(oldfiledesc[lockname])
      oldfiledesc[lockname] = fd
      return True
    except (OSError, IOError), e:
      os.close(fd)
      if e[0] == errno.EACCES or e[0] == errno.EAGAIN:
        # okay, they must have started already.   
        pass
      else:
        # we weren't expecting this...
        raise

  # Let's return the PID
  fo = open(lockfn)
  pidstring = fo.read()
  fo.close()
  return int(pidstring)


def releaseprocesslocko_exlock(lockname):
  if lockname in oldfiledesc:
    os.close(oldfiledesc[lockname])
    del oldfiledesc[lockname]
  

def releaseprocesslockflock(lockname):
  if lockname in oldfiledesc:
    import fcntl
    fcntl.flock(oldfiledesc[lockname],fcntl.LOCK_UN)
    os.close(oldfiledesc[lockname])
    del oldfiledesc[lockname]





##### WINDOWS SECTION ##########

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
        

# return True on success, and either the pid of the locking process or False 
# on failure.
def getprocesslockmutex(lockname):
  from win32event import CreateMutex
  from win32api import GetLastError
  from winerror import ERROR_ALREADY_EXISTS
  import _winreg
  regkeyname = r"runonce."+lockname

  # traverse registry path
  registrypath = ["SOFTWARE","UW","Seattle","1.0"]

  # need to ensure that the mutexhandle is not garbage collected...
  try:
    mutexhandle[lockname] = CreateMutex(None, 1, 'Global\\runonce.'+lockname)
  except Exception,e:
    if e[0] == 5:
      # NOTE: happens when the process is owned by another user
      #Traceback (most recent call last):
      #  File "b.py", line 7, in <module>
      #      mhandle = CreateMutex(None, 1, 'Global\\runonce.'+lockname)
      #      pywintypes.error: (5, 'CreateMutex', 'Access is denied.')
     
      # figure out where the lock is held
      pass
    else: 
      raise
  else:
    if GetLastError() == ERROR_ALREADY_EXISTS:
      # The lock is held, let's figure out where...
      pass
    else:
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




def releaseprocesslockmutex(lockname):
  if lockname in mutexhandle:
    from win32event import ReleaseMutex
    ReleaseMutex(mutexhandle[lockname])
    del mutexhandle[lockname]
