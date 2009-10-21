"""
<Program Name>
  impose_seattlestopper_lock.py

<Started>
  October 2008
    Revised June 4, 2009

<Author>
  Justin Cappos
  Carter Butaud
    Revised by Zachary Boka

<Purpose>
  Forces the seattle node manager and software updater to quit if they are
  running, then holds onto the locks and sleeps forever so they can't start
  again, or until the start_seattle script is run and kills this program.
"""

import runonce
import harshexit
import time

locklist = ["seattlenodemanager", "softwareupdater.old", "softwareupdater.new"]

def killall():
  """
  <Purpose>
    Kills all the seattle programs that might be running and acquires
    the locks so that they can't start again while this program is running.

  <Arguments>
    None.
  
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  for lockname in locklist:
    lockstate = runonce.getprocesslock(lockname)
    # If lockstate is a process pid, then we need to terminate it. Otherwise,
    # that lock is not being held by a program that needs to be terminated. 
    if not lockstate == True and not lockstate == False:
      # We got the pid, we can stop the process
      harshexit.portablekill(lockstate)

      # Now acquire the lock for ourselves, looping until we
      # actually get it.
      retrievedlock = runonce.getprocesslock(lockname)
      while retrievedlock != True:
        harshexit.portablekill(retrievedlock)
        retrievedlock = runonce.getprocesslock(lockname)

def main():
  
  # Is impose_seattlestopper_lock.py already running?
  lockstate = runonce.getprocesslock("seattlestopper")
  if lockstate == True:
    killall()
    # Now sleep forever, checking every 30 secs to make sure we
    # shouldn't quit.
    while runonce.stillhaveprocesslock("seattlestopper") == True:
      time.sleep(30)
  else:
    print "impose_seattlestopper_lock.py is already running."

if __name__ == '__main__':
  main()
