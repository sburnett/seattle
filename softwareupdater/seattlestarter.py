"""
<Program Name>
  seattlestarter.py

<Started>
  November 16, 2008

<Author>
  Carter Butaud

<Purpose>
  Forces the seattle node manager and software updater to
  start after having been killed by seattlestopper.py.

  This removes the locks that are being held by seattlestopper
  and then starts nmmain.py and softwareupdater.py.
"""

import runonce
import time
import os
import nonportable
import platform

def main():
    # First, kill seattlestopper if it is running.
    retval = runonce.getprocesslock("seattlestopper")
    if retval != True and retval:
        nonportable.portablekill(retval)
    
    # Then, start the node manager and software updater,
    # using different files for Windows or Linux based
    # OSes.
    if platform.system() == "Windows":
        os.popen("start /min start_seattle.bat")
    else:
        os.popen("./start_seattle.sh&")

        


if __name__ == "__main__":
    main()
