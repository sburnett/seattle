"""
<Program Name>
  seattleuninstaller.py

<Started>
  August 24, 2009

<Author>
  Zachary Boka

<Purpose>
  Stops seattle from running and removes seattle from the Windows registry
  start-up key, and removes seattle from the user's startup folder, should
  seattle have been installed in either location.
"""
import sys
import os
import impose_seattlestopper_lock
import servicelogger
import time
import _winreg



def remove_value_from_registry(opened_key,remove_value_name):
  """
  <Purpose>
    Removes remove_value_name from opened_key in the Windows Registry.

  <Arguments>
    opened_key:
      A key opened using _winreg.OpenKey(...) or _winreg.CreateKey(...).

    remove_value_name:
      A string of the value name to be removed from opened_key.
  
  <Exceptions>
    WindowsError if the uninstaller is unable to access and manipulate the
    Windows registry, or if opened_key was not previously opened.

  <Side Effects>
    seattle is removed from the Windows registry key opened_key.

  <Returns>
    True if seattle was removed from the registry, False otherwise (indicating
    that seattle could not be found in the registry).
  """
  # The following try: block iterates through all the values contained in the
  # opened key.
  try:
    # The variable "index" will index into the list of values for the opened
    # key.
    index = 0
    # The list that will contain all the names of the values contained in the
    # key.
    value_name_list = []
    # Standard python procedure for _winreg: Continue indexing into the list of
    # values until a WindowsError is raised which indicates that there are no
    # more values to enumerate over.
    while True:
      value_name, value_data, value_type = _winreg.EnumValue(opened_key,index)
      value_name_list.append(value_name)
      index += 1
  except WindowsError:
    # Reaching this point means there are no more values left to enumerate over.
    # If the registry were corrupted, it is probable that a WindowsError will be
    # raised, in which case this function should simply return False.
    pass


  # The following test to see if the value seattle appears in the registry key
  # was not done in real-time in the above while-loop because it is potentially
  # possible that the _winreg.DeleteValue(...) command below could raise a
  # WindowsError.  In that case, it would not be possible for the parent
  # function to know whether the WindowsError was raised because the uninstaller
  # does not have access to the registry or because the value seattle does not
  # exist in the registry key since a WindowsError is raised to exit the while
  # loop when there are no more values to enumerate over.
  if remove_value_name in value_name_list:
    # ARGUMENTS:
    # startkey: the key that contains the value that will be deleted.
    # "seattle": the name of the value that will be deleted form this key.
    _winreg.DeleteValue(opened_key,remove_value_name)
    return True
  else:
    return False




def remove_seattle_from_win_startup_registry():
  """
  <Purpose>
    Removes seattle from the Windows startup registry key.

  <Arguments>
    None.
  
  <Exceptions>
    WindowsError if the uninstaller is unable to access and manipulate the
    Windows registry.

  <Side Effects>
    seattle is removed from the following Windows registry keys which runs
    programs at machine startup and user login:
    HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\Run
    HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run

  <Returns>
    True if seattle was removed from the registry, False otherwise (indicating
    that seattle could not be found in the registry).
  """
  # The startup key must first be opened before any operations, including
  # search, may be performed on it.
  # ARGUMENTS:
  # _winreg.HKEY_LOCAL_MACHINE: specifies the key containing the subkey used
  #                             to run programs at machine startup
  #                             (independent of user login).
  # "Software\\Microsoft\\Windows\\CurrentVersion\\Run": specifies the subkey
  #                                                      that runs programs on
  #                                                      machine startup.
  # 0: A reserved integer that must be zero.
  # _winreg.KEY_ALL_ACCESS: an integer that allows the key to be opened with all
  #                         access (e.g., read access, write access,
  #                         manipulaiton, etc.)
  startkey_Local_Machine = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,
                            "Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                             0,_winreg.KEY_ALL_ACCESS)
  removed_from_LM = remove_value_from_registry(startkey_Local_Machine,"seattle")



  # The startup key must first be opened before any operations, including
  # search, may be performed on it.
  # ARGUMENTS:
  # _winreg.HKEY_CURRENT_USER: specifies the key containing the subkey used
  #                             to run programs at user login.
  # "Software\\Microsoft\\Windows\\CurrentVersion\\Run": specifies the subkey
  #                                                      that runs programs on
  #                                                      user login.
  # 0: A reserved integer that must be zero.
  # _winreg.KEY_ALL_ACCESS: an integer that allows the key to be opened with all
  #                         access (e.g., read access, write access,
  #                         manipulaiton, etc.)
  startkey_Current_User = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,
                            "Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                             0,_winreg.KEY_ALL_ACCESS)
  removed_from_CU = remove_value_from_registry(startkey_Current_User,"seattle")


  if removed_from_LM or removed_from_CU:
    return True
  else:
    return False

  


def remove_seattle_from_win_startup_folder(startup_folder_script_path):
  """
  <Purpose>
    Remove a link to the seattle starter script from the Windows startup folder.

  <Arguments>
    startup_folder_script_path:
      The absolute path of the link in the startup folder to the seattle
      starter script, regardless of whether or not the link actually exists.

  <Exceptions>
    Possible IOError raised during filepath manipulation.

  <Side Effects>
    Removes the link to the seattle starter script from the Windows startup
    folder should it exist there.

  <Returns>
    True if the function removed the link to the seattle starter script in the
    startup folder, False otherwise (indicating that the link did not exist).
  """

  if os.path.exists(startup_folder_script_path):
    os.remove(startup_folder_script_path)
    return True
  else:
    return False




def uninstall(startup_folder_script_path):
  """
  <Purpose>
    Shuts down all seattle processes using impose_seattlestopper_lock.py,
    and removes seattle from the Winodws registry startup key and/or the
    startup folder should either exist.  Lastly, this function notifies the user
    of whether or not seattle was successfully uninstalled.

  <Arguments>
    startup_folder_script_path:
      The absolute path of the link in the startup folder to the seattle
      starter script, regardless of whether or not the link actually exists.

  <Exceptions>
    Possible IOError could be caused by filepath manipulation from a
    sub-function.

  <Side Effects>
    Removes seattle from the Windows registry key and/or the Windows startup
    folder if it exists in either place.

  <Returns>
    None.
  """
  # Stop all instances of seattle from running.
  impose_seattlestopper_lock.killall()


  # First see if seattle appears as a value in the Windows startup registry key,
  # and remove it if it exists.
  # removed_from_registry is used later and thus must have a value in case the
  # try: block below raises an exception.
  removed_from_registry = False
  try:
    removed_from_registry = remove_seattle_from_win_startup_registry()
  except WindowsError:
    print "The uninstaller does not have access to the Windows registry " \
        + "startup key. This means that seattle is likely not installed in " \
        + "your Windows registry startup key, though you may want to " \
        + "manually check the following registry key and remove seattle from " \
        + "that key should it exist there: "
    print "HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\Run"
    # Distinguish the above-printed text from what will be printed later by
    # by printing a blank line.
    print
    servicelogger.log(" uninstaller could not access the Windows registry " \
                        + "during this attempted uninstall.")


  # Next, see if there is a link to the seattle starter script in the startup
  # folder and remove it if it is there.
  removed_from_startup_folder = \
      remove_seattle_from_win_startup_folder(startup_folder_script_path)


  # Check to see if uninstall actually removed seattle from the computer.
  if not removed_from_registry and not removed_from_startup_folder:
    print "seattle could not be detected as configured to run automatically " \
        + "at boot on this machine."
    print "If you wish to delete the directory containing seattle, you may " \
        + "do so now."
  elif removed_from_registry or removed_from_startup_folder:
    print "seattle was successfully uninstalled."
    print "You may now delete the directory containing seattle, if you wish."
    servicelogger.log(time.strftime(" seattle was UNINSTALLED on: " \
                                      + "%m-%d-%Y %H:%M:%S"))




def main():

  # Initialize the service logger.
  servicelogger.init('installInfo')

  if len(sys.argv) < 2:
    print "Usage: python seattleuninstaller.py " \
        + "absolute\\path\\to\\startup\\script"
  else:
    uninstall(sys.argv[1])

if __name__ == "__main__":
  main()
