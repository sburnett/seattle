"""
<Program Name>
  startstop_test.py

<Started>
  June 4, 2009

<Author>
  Zachary Boka

<Purpose>
  Prints out the processes holding the keys: "seattlenodemanager",
  "softwareupdater.old", "softwareupdater.new", and "seattlestopper". Created to
  be inserted into the start_seattle and stop_seattle scripts, both before and
  after the original programs in those scripts, to confirm what programs are
  holding the the locks before and after the scripts are run.
"""

import runonce
import os
import time


locklist = ["seattlenodemanager", "softwareupdater.old", "softwareupdater.new",\
                "seattlestopper"]


def main():
  # Give time for any changes in acquiring/relinquishing keys to take effect
  time.sleep(2)
  for lockname in locklist:
      status = runonce.getprocesslock(lockname)
      if status == True:
        print "The lock '" + lockname + "' was not being held."
        runonce.releaseprocesslock(lockname)
      elif status == False:
        print "There was an error getting the lock '" + lockname + "'."
      else:
        print "The lock '" + lockname + "' is currently being used by process pid: " + str(status)



if __name__ == '__main__':
  main()
