"""
<Program Name>
  seattleuninstaller.py

<Started>
  January 12, 2009

<Author>
  Carter Butaud

<Purpose>
  Shuts down seattle and removes the starter script
  from the user's startup folder.
"""
import sys
import os
import impose_seattlestopper_lock
import servicelogger
import time



class UninstallError(Exception):
  """
  <Purpose>
    Signals a failure in the uninstaller.

  <Side Effects>
    None.

  <Example Use>
    raise UninstallError("Could not find starter script.")
  """
  def __init__(self, value):
    self.parameter = value
  def __str__(self):
      return repr(self.parameter)



def uninstall(starter_script):
  """
  <Purpose>
    Shuts down all seattle processes using impose_seattlestopper_lock.py
    and removes the starter script from the startup folder.

  <Arguments>
    startup:
      The absolute path to the computer's startup folder.
    starter_script:
      The name of the starter script located inside the startup folder.

  <Exceptions>
    UninstallError if the starter file cannot be found.

  <Returns>
    None.
  """
  try:
    if not os.path.exists(starter_script):
      raise UninstallError("Could not find startup file.")
        
    # Stop all instances of seattle from running
    impose_seattlestopper_lock.killall()
    
    # Remove the startup script
    os.remove(starter_script)
        
    # Alert the user that we're done
    print "seattle was successfully uninstalled."
    print "You may now delete the directory containing seattle, if you wish."

    servicelogger.log(time.strftime(" seattle was UNINSTALLED on: %m-%d-%Y %H:%M:%S"))

  except UninstallError, (e):
    print "Uninstall failed:", e.parameter
    print "To uninstall manually, remove the file " + os.path.basename(starter_script) + " from your startup folder, then restart your computer."
    print "You can then delete the directory containing seattle, if you wish."



def main():

  # Initialize the service logger.
  servicelogger.init('installInfo')

  if len(sys.argv) < 2:
    print "Usage: python seattleuninstaller.py path\\to\\startup\\script"
  else:
    uninstall(sys.argv[1])

if __name__ == "__main__":
  main()
