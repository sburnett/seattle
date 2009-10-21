"""
<Program Name>
  seattleuninstaller.py

<Started>
  October 2008

<Author>
  Carter Butaud

<Purpose>
  Kills any seattle processes that are running and
  removes the starter line from the crontab.
"""

import re
import os
import impose_seattlestopper_lock
import tempfile
import sys
import servicelogger
import time

STARTER_SCRIPT_NAME = "start_seattle.sh"

def output(text, silent=0):
    # For internal use, in case we want to silence the program
    # at some point
    if silent != 1:
        print text



def uninstall(silent = 0):
    """
    <Purpose>
      Kills any seattle processes that are running using
      impose_seattlestopper_lock and removes the starter line from
      the crontab.

    <Arguments>
      silent:
        Optional argument, prints no output if silent is set
        to 1, else prints regular output.

    <Exceptions>
      None.

    <Side Effects>
      None.

    <Returns>
      None.
    """
    # Kill seattle
    impose_seattlestopper_lock.killall()
    crontab_f = os.popen("crontab -l")
    # Used module tempfile as suggested in Jacob Appelbaum's patch
    fd, s_tmp = tempfile.mkstemp("temp", "seattle")
    found = False
    for line in crontab_f:
        if not re.search("/" + STARTER_SCRIPT_NAME, line):
            os.write(fd, line)
        else:
            found = True
    if found:
        os.close(fd)
        os.popen('crontab "' + s_tmp + '"')
        output("Seattle has been uninstalled.", silent)
        output("If you wish, you may now delete this directory.", silent)
        servicelogger.log(time.strftime(" seattle was UNINSTALLED on: " \
                                            "%m-%d-%Y %H:%M:%S"))
    else:
        os.close(fd)
        output("seattle is not currently installed.", silent)
    os.unlink(s_tmp)




def main():

    #Initialize the service logger.
    servicelogger.init('installInfo')

    if len(sys.argv) < 2:
        uninstall()
    else:
        if sys.argv[1] == "-h":
            print "Usage: python seattleuninstaller.py [-s]"
        elif sys.argv[1] == "-s":
            uninstall(1)


if __name__ == "__main__":
    main()
