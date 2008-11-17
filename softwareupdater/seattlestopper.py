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

def main():
  
  # Is seattlestopper.py already running?
  retval = runonce.getprocesslock("seattlestopper")
  if retval == True:
    # For each locked process, find the PID of the process holding the lock...
    for lockname in locklist:
      retval = runonce.getprocesslock(lockname)
      if retval == True:
        # I got the lock, it wasn't running...
        print "The lock '"+lockname+"' was not held"
        pass
      elif retval == False:
        # Someone has the lock, but I can't do anything...
        print "The lock '"+lockname+"' is not held by an unknown process"

      else:
        # I know the process ID!   Let's stop the process...
        print "Stopping the process (pid: "+str(retval)+") with lock '"+lockname+"'"
        nonportable.portablekill(retval)
        # Now acquire the lock for ourselves, so that the process
        # can't start up again. Make sure that we actually have the
        # lock before proceeding.
        while runonce.getprocesslock(lockname) != True:
          pass
     
    while True:
      # Now sleep forever, checking every 30 secs to make sure we
      # shouldn't quit.
      if runonce.stillhaveprocesslock("seattlestopper"):
        time.sleep(30)
  else:
    print "seattlestopper.py is already running."

if __name__ == '__main__':
  main()
