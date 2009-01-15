"""
<Program Name>
  seattlestopper.py

<Started>
  October 2008

<Author>
  Justin Cappos
  Carter Butaud

<Purpose>
  Forces the seattle node manager and software updater to quit if
  they are running, then holds onto the locks and sleeps forever
  so they can't start again.
"""

import runonce
import os
import sys
import nonportable
import time

locklist = [ "seattlenodemanager", "softwareupdater.old", "softwareupdater.new" ]

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
    retval = runonce.getprocesslock(lockname)
    if retval == True:
      # The process wasn't running
      print "The lock '"+lockname+"' was not held."
    elif retval == False:
      # The process is running, but I can't stop it
      print "The lock '" + lockname + "' was held by an unknown process."
    else:
      # We got the pid, we can stop the process
      print "Stopping the process (pid: " + str(retval) + ") with lock " + lockname + "."
      nonportable.portablekill(retval)

      # Now acquire the lock for ourselves, looping until we
      # actually get it.
      while (runonce.getprocesslock(lockname) != True):
        pass

def main():
  
  # Is seattlestopper.py already running?
  retval = runonce.getprocesslock("seattlestopper")
  if retval == True:
    killall()     
    while True:
      # Now sleep forever, checking every 30 secs to make sure we
      # shouldn't quit.
      if runonce.stillhaveprocesslock("seattlestopper"):
        time.sleep(30)
  else:
    print "seattlestopper.py is already running."

if __name__ == '__main__':
  main()
