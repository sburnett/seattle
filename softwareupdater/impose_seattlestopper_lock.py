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
import nonportable
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
    if lockstate == True:
      # The process wasn't running
      print "The lock '" + lockname + "' was not being held."
    elif lockstate == False:
      # The process is running, but I can't stop it
      print "The lock '" + lockname + "' is being held by an unknown process."
    else:
      # We got the pid, we can stop the process
      print "Stopping the process (pid: " + str(lockstate) + ") with lock '" + lockname + "'."
      nonportable.portablekill(lockstate)

      # Now acquire the lock for ourselves, looping until we
      # actually get it.
      retrievedlock = runonce.getprocesslock(lockname)
      while retrievedlock != True:
        nonportable.portablekill(retrievedlock)
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
