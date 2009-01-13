"""
<Program Name>
  uninstall.py

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
import seattlestopper



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



def uninstall(startup, starter_script):
  """
  <Purpose>
    Shuts down all seattle processes using seattlestopper.py
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
    if not os.path.exists(startup + "\\" + starter_script):
      raise UninstallError("Could not find startup file.")
        
    # Stop all instances of seattle from running
    seattlestopper.killall()
    
    # Remove the startup script
    os.remove(startup + "\\" + starter_script)
        
    # Alert the user that we're done
    print "seattle was successfully uninstalled."
    print "You may now delete the directory containing seattle, if you wish."

  except UninstallError, (e):
    print "Install failed:", e.parameter
    print "To uninstall manually, remove the file " + starter_script + " from your startup folder, then restart your computer."
    print "You can then delete the directory containing seattle, if you wish."



def main():
  if len(sys.argv) < 3:
    print "Usage: python uninstall.py path\\to\\startup\\folder\\ starter_script_name"
  else:
    uninstall(sys.argv[1], sys.argv[2])

if __name__ == "__main__":
  main()
