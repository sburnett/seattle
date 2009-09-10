"""
<Program Name>
  seattleinstaller.py

<Started>
  February 10, 2009
    Amended June 11, 2009
    Amended July 30, 2009

<Author>
  Carter Butaud
    Amended by Zachary Boka

<Purpose>
  Installs seattle on any supported system. This means setting up the computer
  to run seattle at startup, generating node keys, customizing configuration
  files, and starting seattle itself.
"""

# Let's make sure the version of python is supported
import checkpythonversion
checkpythonversion.ensure_python_version_is_supported()

import os
import shutil
import platform
import sys
import getopt
import tempfile
import re
import servicelogger
import time

# Python should do this by default, but doesn't on Windows CE
sys.path.append(os.getcwd())
import nonportable
import createnodekeys
import repy_constants
import persist # Armon: Need to modify the NM config file
import benchmark_resources
# Anthony - traceback is imported so that benchmarking can be logged
# before the vessel state has been created (servicelogger does not work
# without the v2 directory
import traceback 


SILENT_MODE = False
KEYBITSIZE = 1024
DISABLE_STARTUP_SCRIPT = False
OS = nonportable.ostype
SUPPORTED_OSES = ["Windows", "WindowsCE", "Linux", "Darwin"]
# Supported Windows Versions: XP, Vista
RESOURCE_PERCENTAGE = 10

# Import subprocess if not in WindowsCE
subprocess = None
if OS != "WindowsCE":
  import subprocess

# Import windows_api if in Windows or WindowsCE
windows_api = None
if OS == "WindowsCE":
  import windows_api

# Import _winreg if in Windows or WindowsCE
_winreg = None
if OS == "Windows" or OS == "WindowsCE":
  import _winreg



class UnsupportedOSError(Exception):
  pass

class AlreadyInstalledError(Exception):
  pass




def _output(text):
  """
  For internal use.
  If the program is not in silent mode, prints the input text.
  """
  if not SILENT_MODE:
    print text




def preprocess_file(filename, substitute_dict, comment="#"):
  """
  <Purpose>
    Looks through the given file and makes all substitutions indicated in lines
    the do not begin with a comment.

  <Arguments>
    filename:
      The name of the file that will be preprocessed.
    substitute_dict:
      Map of words to be substituted to their replacements, e.g.,
      {"word_in_file_1": "replacement1", "word_in_file_2": "replacement2"}
    comment:
      A string which demarks commented lines; lines that start with this will
      be ignored, but lines that contain this symbol somewhere else in the line 
      will be preprocessed up to the first instance of the symbol. Defaults to
      "#". To preprocess all lines in a file, set as the empty string.

  <Exceptions>
    IOError on bad filename.
  
  <Side Effects>
    None.

  <Returns>
    None.
  """
  edited_lines = []
  base_fileobj = open(filename, "r")

  for fileline in base_fileobj:
    commentedOutString = ""

    if comment == "" or not fileline.startswith(comment):
      # Substitute the replacement string into the file line.

      # First, test whether there is an in-line comment.
      if comment != "" and comment in fileline:
        splitLine = fileline.split(comment,1)
        fileline = splitLine[0]
        commentedOutString = comment + splitLine[1]

      for substitute in substitute_dict:
        fileline = fileline.replace(substitute, substitute_dict[substitute])

    edited_lines.append(fileline + commentedOutString)

  base_fileobj.close()

  # Now, write those modified lines to the actual starter file location.
  final_fileobj = open(filename, "w")
  final_fileobj.writelines(edited_lines)
  final_fileobj.close()




def get_filepath_of_win_startup_folder_with_link_to_seattle():
  """
  <Purpose>
    Gets what the full filepath would be to a link to the seattle starter script
    in the Windows startup folder.  Also tests whether or not that filepath
    exists (i.e., whether or not there is currently a link in the startup folder
    to run seattle at boot).
  
  <Arguments>
    None.

  <Exceptions>
    UnsupportedOSException if the operating system is not Windows or WindowsCE.
    IOError may be thrown if an error occurs while accessing a file.

  <Side Effects>
    None.

  <Returns>
    A tuple is returned whith the first value being the filepath to the link in
    the startup folder that will run seattle at boot.  The second value is a
    boolean value: True indicates the link currently exists in the startup
    folder, and False if it does not.
  """
  if OS == "WindowsCE":
    startup_path = "\\Windows\\Startup" + os.sep + get_starter_file_name()
    return (startup_path, os.path.exists(startup_path))

  elif OS != "Windows":
    raise UnsupportedOSError("The startup folder only exists on Windows.")


  version = platform.release()
  if version == "Vista":
    startup_path = os.environ.get("HOMEDRIVE") + os.environ.get("HOMEPATH") + "\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup" + os.sep + get_starter_shortcut_file_name()
    return (startup_path, os.path.exists(startup_path))

  elif version == "XP":
    startup_path = os.environ.get("HOMEDRIVE") + os.environ.get("HOMEPATH") + "\\Start Menu\\Programs\\Startup" + os.sep + get_starter_shortcut_file_name()
    return (startup_path, os.path.exists(startup_path))




def get_starter_file_name():
  """
  <Purpose>
    Returns the name of the starter file on the current operating system.

  <Arguments>
    None.

  <Exceptions>
    UnsupportedOSError if the operating system requested is not supported.

  <Side Effects>
    None.

  <Returns>
    A string containing the name of the starter file.
  """

  if OS == "Windows":
    return "start_seattle.bat"
  elif OS == "WindowsCE":
    return "start_seattle.py"
  elif OS == "Linux" or OS == "Darwin":
    return "start_seattle.sh"
  else:
    raise UnsupportedOSError




def get_starter_shortcut_file_name():
  """
  <Purpose>
    Returns the name of the starter shortcut file on the current operating
    system.

  <Arguments>
    None.

  <Exceptions>
    UnsupportedOSError if the operating system requested is not supported.

  <Side Effects>
    None.

  <Returns>
    A string containing the name of the starter shortcut file.
  """

  if OS == "Windows":
    return "start_seattle_shortcut.bat"
  else:
    raise UnsupportedOSError("Only the Windows installer contains a shortcut " \
                               + "for the seattle starter batch file.")




def get_stopper_file_name():
  """
  <Purpose>
    Returns the name of the stopper file on the current operating syste

  <Arguments>
    None.

  <Exceptions>
    UnsupportedOSError if the operating system requested is not supported.

  <Side Effects>
    None.

  <Returns>
    A string containing the name of the stopper file.  Returns an empty string
    if the supported operating system does not contain a stopper file.
  """

  if OS == "Windows":
    return "stop_seattle.bat"
  elif OS == "WindowsCE":
    return ""
  elif OS == "Linux" or OS == "Darwin":
    return "stop_seattle.sh"
  else:
    raise UnsupportedOSError




def get_uninstaller_file_name():
  """
  <Purpose>
    Returns the name of the uninstaller file on the current operating
    system.

  <Arguments>
    None.

  <Exceptions>
    UnsupportedOSError if the operating system requested is not supported.

  <Side Effects>
    None.

  <Returns>
    The name of the uninstaller file.
  """
  if OS == "Windows":
    return "uninstall.bat"
  elif OS == "WindowsCE":
    return "uninstall.py"
  elif OS == "Linux" or OS == "Darwin":
    return "uninstall.sh"
  else:
    raise UnsupportedOSError




def search_value_in_win_registry_key(opened_key,seeking_value_name):
  """
  <Purpose>
    Searches a given key to see if a given value exists for that key.

  <Arguments>
    opened_key:
      An already opened key that will be searched for the given value.  For a
      key to be opened, it must have had the _winreg.OpenKey(...) or
      _winreg.CreateKey(...) functions performed on it.

    seeking_value_name:
      A string containing the name of the value to search for within the
      opened_key.

  <Exceptions>
    UnsupportedOSError if the operating system is not Windows or WindowsCE.
    WindowsError if opened_key has not yet been opened.

  <Side Effects>
    None.

  <Returns>
    True if seeking_value_name is found within opened_key.
    False otherwise.

  """
  if OS != "Windows" and OS != "WindowsCE":
    raise UnsupportedOSError("This operating system must be Windows or " \
                               + "WindowsCE in order to manipulate registry " \
                               + "keys.")

  # Test to make sure that opened_kay was actually opened by obtaining
  # information about that key.
  # Raises a WindowsError if opened_key has not been opened.
  # subkeycount: the number of subkeys opened_key contains. (not used).
  # valuescount: the number of values opened_key has.
  # modification_info: long integer stating when the key was last modified.
  #                    (not used)
  subkeycount, valuescount, modification_info = _winreg.QueryInfoKey(opened_key)
  if valuescount == 0:
    return False


  try:
    value_data,value_type = _winreg.QueryValueEx(opened_key,seeking_value_name)
    # No exception was raised, so seeking_value_name was found.
    return True
  except WindowsError:
    return False




def remove_seattle_from_win_startup_folder():
  """
  <Purpose>
    Removes the seattle startup script from the Windows startup folder if it
    exists.

  <Arguments>
    None.

  <Exceptions>
    UnsupportedOSError if the os is not supported (i.e., a Windows machine).
    IOError may be raised if an error occurs during file and filepath
      manipulation.

  <Side Effects>
    Removes the seattle startup script from the Windows startup folder if it
    exists.

  <Returns>
    True if the function removed the link to the startup script, meaning it
         previously existd.
    False otherwise, meaning that a link to the startup script did not
    previously exist.
  """
  if OS != "Windows" and OS != "WindowsCE":
    raise UnsupportedOSError("This must be a Windows operating system to " \
                               + "access the startup folder.")

  # Getting the startup path in order to see if a link to seattle has been
  # installed there.
  full_startup_file_path,file_path_exists = \
      get_filepath_of_win_startup_folder_with_link_to_seattle()
  if file_path_exists:
    os.remove(full_startup_file_path)
    return True
  else:
    return False




def add_seattle_to_win_startup_folder(prog_path):
  """
  <Purpose>
    Add the seattle startup script to the Windows startup folder.

  <Arguments>
    prog_path:
      The absolute path to the seattle_repy directory.

  <Exceptions>
    UnsupportedOSError if the os is not supported (i.e., a Windows machine).
    IOError may be raised if an error occurs during file and filepath
      manipulation.

  <Side Effects>
    Adds the seattle startup script to the Windows startup folder.

  <Returns>
    None.
  """
  if OS != "Windows" and OS != "WindowsCE":
    raise UnsupportedOSError("This must be a Windows operating system to " \
                               + "access the startup folder.")

  # Getting the startup path in order to copy the startup file there which will
  # make seattle start when the user logs in.
  full_startup_file_path,file_path_exists = \
      get_filepath_of_win_startup_folder_with_link_to_seattle()
  if file_path_exists:
    raise AlreadyInstalledError("seattle was already installed in the " \
                                  + "startup folder.")
  else:
    shutil.copy(prog_path + os.sep + get_starter_shortcut_file_name(),
                full_startup_file_path)




def add_to_win_registry_Local_Machine_key(prog_path):
  """
  <Purpose>
    Adds seattle to the Windows registry key Local_Machine which runs programs
    at machine startup (regardless of which user logs in).

  <Arguments>
    prog_path:
      The path to the directory where the seattle program files are located.

  <Exceptions>
    UnsupportedOSError if the os is not supported (i.e., a Windows machine).
    AlreadyInstalledError if seattle has already been installed on the system.

  <Side Effects>
    Adds a value named "seattle", which contains the absolute file path to the
    seattle starter script, to the startup registry key.

  <Returns>
    True if succeeded in adding seattle to the registry,
    False otherwise.
  """

  if OS != "Windows" and OS != "WindowsCE":
    raise UnsupportedOSError("This machine must be running Windows in order " \
                               + "to access the Windows registry.")

  # The following entire try: block attempts to add seattle to the Windows
  # registry to run seattle at machine startup regardless of user login.
  try:
    # The startup key must first be opened before any operations, including
    # searching its values, may be performed on it.

    # ARGUMENTS:
    # _winreg.HKEY_LOCAL_MACHINE: specifies the key containing the subkey used
    #                             to run programs at machine startup
    #                             (independent of user login).
    # "Software\\Microsoft\\Windows\\CurrentVersion\\Run": specifies the subkey
    #                                                      that runs programs on
    #                                                      machine startup.
    # 0: a reserved integer that must be zero.
    # _winreg.KEY_ALL_ACCESS: an integer that acts as an access map that
    #                         describes desired security access for this key.
    #                         In this case, we want all access to the key so it
    #                         can be modified. (Default: _winreg.KEY_READ)
    startup_key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,
                            "Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                            0, _winreg.KEY_ALL_ACCESS)
  except WindowsError:
    return False

  else:
    # The key was successfully opened.  Now check to see if seattle was
    # previously installed in this key. *Note that the key should be closed in
    # this else: block when it is no longer needed.
    if search_value_in_win_registry_key(startup_key, "seattle"):
      # Close the key before raising AlreadyInstalledError.
      _winreg.CloseKey(startup_key)
      raise AlreadyInstalledError("seattle is already installed in the " \
                                    + "Windows registry starup key.")

    try:
      # seattle has not been detected in the registry from a previous
      # installation, so attempting to add the value now.
      
      # _winreg.SetValueEx(...) creates the value "seattle", if it does not
      #                         already exist, and simultaneously adds the given
      #                         data to the value.
      # ARGUMENTS:
      # startup_key: the opened subkey that runs programs on startup.
      # "seattle": the name of the new value to be created under startup_key 
      #            that will make seattle run at machine startup.
      # 0: A reserved value that can be anything, though zero is always passed
      #    to the API according to python documentation for this function.
      # _winreg.REG_SZ: Specifies the integer constant REG_SZ which indicates
      #                 that the type of the data to be stored in the value is a
      #                 null-terminated string.
      # prog_path + os.sep + get_starter_file_name(): The data of the new
      #                                               value being created
      #                                               containing the full path
      #                                               to seattle's startup
      #                                               script.
      _winreg.SetValueEx(startup_key, "seattle", 0, _winreg.REG_SZ,
                       prog_path + os.sep + get_starter_file_name())
      servicelogger.log(" seattle was successfully added to the Windows " \
                          + "registry key to run at startup: " \
                          + "HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows" \
                          + "\\CurrentVersion\\Run")
      # Close the key before returning.
      _winreg.CloseKey(startup_key)
      return True
      
    except WindowsError:
      # Close the key before falling through the try: block.
      _winreg.CloseKey(startup_key)
      return False






def add_to_win_registry_Current_User_key(prog_path):
  """
  <Purpose>
    Sets up seattle to run at user login on this Windows machine.

  <Arguments>
    prog_path:
      The path to the directory where the seattle program files are located.

  <Exceptions>
    UnsupportedOSError if the os is not supported (i.e., a Windows machine).
    AlreadyInstalledError if seattle has already been installed on the system.

  <Side Effects>
    Adds a value named "seattle", which contains the absolute file path to the
    seattle starter script, to the user login registry key.

  <Returns>
    True if succeeded in adding seattle to the registry,
    False otherwise.
  """
  if OS != "Windows" and OS != "WindowsCE":
    raise UnsupportedOSError("This machine must be running Windows in order " \
                               + "to access the Windows registry.")

  # The following entire try: block attempts to add seattle to the Windows
  # registry to run seattle at user login.
  try:
    # The startup key must first be opened before any operations, including
    # searching its values, may be performed on it.

    # ARGUMENTS:
    # _winreg.HKEY_CURRENT_MACHINE: specifies the key containing the subkey used
    #                             to run programs at user login.
    # "Software\\Microsoft\\Windows\\CurrentVersion\\Run": specifies the subkey
    #                                                      that runs programs on
    #                                                      user login.
    # 0: a reserved integer that must be zero.
    # _winreg.KEY_ALL_ACCESS: an integer that acts as an access map that
    #                         describes desired security access for this key.
    #                         In this case, we want all access to the key so it
    #                         can be modified. (Default: _winreg.KEY_READ)
    startup_key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,
                            "Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                            0, _winreg.KEY_ALL_ACCESS)
  except WindowsError:
    return False

  else:
    # The key was successfully opened.  Now check to see if seattle was
    # previously installed in this key. *Note that the key should be closed in
    # this else: block when it is no longer needed.
    if search_value_in_win_registry_key(startup_key, "seattle"):
      # Close the key before raising AlreadyInstalledError.
      _winreg.CloseKey(startup_key)
      raise AlreadyInstalledError("seattle is already installed in the " \
                                    + "Windows registry starup key.")

    try:
      # seattle has not been detected in the registry from a previous
      # installation, so attempting to add the value now.
      
      # _winreg.SetValueEx(...) creates the value "seattle", if it does not
      #                         already exist, and simultaneously adds the given
      #                         data to the value.
      # ARGUMENTS:
      # startup_key: the opened subkey that runs programs on user login.
      # "seattle": the name of the new value to be created under startup_key 
      #            that will make seattle run at user login.
      # 0: A reserved value that can be anything, though zero is always passed
      #    to the API according to python documentation for this function.
      # _winreg.REG_SZ: Specifies the integer constant REG_SZ which indicates
      #                 that the type of the data to be stored in the value is a
      #                 null-terminated string.
      # prog_path + os.sep + get_starter_file_name(): The data of the new
      #                                               value being created
      #                                               containing the full path
      #                                               to seattle's startup
      #                                               script.
      _winreg.SetValueEx(startup_key, "seattle", 0, _winreg.REG_SZ,
                       prog_path + os.sep + get_starter_file_name())
      servicelogger.log(" seattle was successfully added to the Windows " \
                          + "registry key to run at user login: " \
                          + "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows" \
                          + "\\CurrentVersion\\Run")
      # Close the key before returning.
      _winreg.CloseKey(startup_key)
      return True
      
    except WindowsError:
      # Close the key before falling through the try: block.
      _winreg.CloseKey(startup_key)
      return False





def setup_win_startup(prog_path,scripts_path):
  """
  <Purpose>
    Sets up seattle to run at startup on this Windows machine. First, this means
    adding a value, with absolute file path to the seattle starter script, to
    the machine startup and user login registry keys (HKEY_LOCAL_MACHINE and 
    HKEY_CURRENT_USER) which will run seattle at startup regardless of which
    user logs in and when the current user logs in (in the case where a machine
    is not shut down between users logging in and out). Second, if that fails,
    this method attempts to add a link to the Windows startup folder which will
    only run seattle when this user logs in.

  <Arguments>
    prog_path:
      The path to the directory where the seattle program files are located.

    scripts_path:
      The path to the direcotory where the seattle scripts are located.

  <Exceptions>
    UnsupportedOSError if the os is not supported (i.e., a Windows machine).
    AlreadyInstalledError if seattle has already been installed on the system.
    IOError may be raised if an error occurs during file and filepath
      manipulation in one of the sub-functions called by this method.

  <Side Effects>
    Adds a value named "seattle", which contains the absolute file path to the
    seattle starter script, to the startup registry key, or adds seattle to the
    startup folder if adding to the registry key fails.

    If an entry is successfully made to the registry key and a pre-existing link
    to seattle exists in the startup folder, the entry in the startup foler is
    removed.

  <Returns>
    None.
  """

  # Check to make sure the OS is supported
  if OS != "Windows" and OS != "WindowsCE":
    raise UnsupportedOSError("This operating system must be Windows or " \
                               + "WindowsCE in order to modify a registry " \
                               + "or startup folder.")

  try:
    added_to_CU_key = add_to_win_registry_Current_User_key(prog_path)
    added_to_LM_key = add_to_win_registry_Local_Machine_key(prog_path)
  except Exception,e:
    # Fall through try: block to setup seattle in the startup folder.
    _output("seattle could not be installed in the Windows registry for the " \
              + "following reason: " + str(e))
    servicelogger.log(" seattle was NOT setup in the Windows registry " \
                        + "for the following reason: " + str(e))
  else:
    if added_to_CU_key or added_to_CU_key:
      # Succeeded in adding seattle to the registry key, so now remove seattle
      # from the startup folder if there is currently a link there from a
      # previous installation.
      if remove_seattle_from_win_startup_folder():
        _output("seattle was detected in the startup folder.")
        _output("Now that seattle has been successfully added to the " \
                  + "Windows registry key, the link to run seattle has been " \
                  + "deleted from the startup folder.")
        servicelogger.log(" A link to the seattle starter file from a " \
                            + "previous installation was removed from the " \
                            + "startup folder during the current installation.")
        # Since seattle was successfully installed in the registry, the job of
        # this function is finished.
      return

    else:
      _output("This user does not have permission to access the user registry.")
      
    



  # Reaching this point means modifying the registry key failed, so add seattle
  # to the startup folder.
  _output("Attempting to add seattle to the startup folder as an " \
            + "alternative method for running seattle at startup.")
  add_seattle_to_win_startup_folder(prog_path)
  servicelogger.log(" A link to the seattle starter script was installed in " \
                      + "the Windows startup folder rather than in the " \
                      + "registry.")




def setup_linux_or_mac_startup(prog_path,scripts_path):
  """
  <Purpose>
    Sets up seattle to run at startup on this Linux or Macintosh machine. This
    means adding an entry to crontab.

  <Arguments>
    prog_path:
      The path to the directory where the seattle program files are located.

    scripts_path:
      The path to the directory where the seattle scripts are located.

  <Exceptions>
    UnsupportedOSError if the os is not supported.
    AlreadyInstalledError if seattle has already been installed on the system.

  <Side Effects>
    None.

  <Returns>
    None.
  """

  if OS != "Linux" and OS != "Darwin":
    raise UnsupportedOSError

  else:

    _output("Adding an entry to the crontab...")
    # First check to see if crontab has already been modified to run seattle
    crontab_contents = subprocess.Popen("crontab -l", shell=True, stdout=subprocess.PIPE).stdout
    found = False
    for line in crontab_contents:
      if re.search(os.sep + get_starter_file_name(), line):
        found = True
        break
    crontab_contents.close()
    if found:
      raise AlreadyInstalledError
  
    # Since seattle is not already installed, crontab should be modified

    # First, get the service vessel to where any output from cron will be
    # logged.
    service_vessel = servicelogger.get_servicevessel()
    
    # Generate a temp file with the user's crontab plus our task
    # (tempfile module used as suggested in Jacob Appelbaum's patch)
    cron_line = '@reboot if [ -e "' + scripts_path + '/' \
        + get_starter_file_name() + '" ]; then "' + scripts_path + '/' \
        + get_starter_file_name() + '" >> "' + prog_path + '/' \
        + service_vessel + '/cronlog.txt" 2>&1; else crontab -l | ' \
        + 'sed \'/start_seattle.sh/d\' > /tmp/seattle_crontab_removal && ' \
        + 'crontab /tmp/seattle_crontab_removal && ' \
        + 'rm /tmp/seattle_crontab_removal; fi' + os.linesep
    crontab_contents = subprocess.Popen("crontab -l", shell=True, stdout=subprocess.PIPE).stdout
    filedescriptor, tmp_location = tempfile.mkstemp("temp", "seattle")
    for line in crontab_contents:
      os.write(filedescriptor, line)
    os.write(filedescriptor, cron_line)
    os.close(filedescriptor)

    # Now, replace the crontab with that temp file
    os.popen('crontab "' + tmp_location + '"')
    os.unlink(tmp_location)
    return




def setup_win_uninstaller_and_starter_shortcut_script(prog_path,scripts_path,starter_file):
  """
  <Purpose>
    On Windows, customizes the base uninstaller located in the install directory so
    that it will remove the starter file from the startup folder when run.

  <Arguments>
    prog_path:
      The path to the directory containing the seattle files (seattle_repy).
    scripts_path:
      The path to the directory containing the seattle scripts.
    starter_file:
      The path to the starter file.

  <Exceptions>
    UnsupportedOSError if OS is not Windows\WindowsCE.
    IOError if starter_file is an invalid path or if the base uninstaller doesn't already
    exist.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  if OS != "Windows" and OS != "WindowsCE":
    raise UnsupportedOSError
  elif not os.path.exists(scripts_path + os.sep + get_uninstaller_file_name()):
    raise IOError

  for filename in [get_uninstaller_file_name(),
                   get_starter_shortcut_file_name()]:
    preprocess_file(prog_path + os.sep + filename,
                    {"%STARTER_FILE%": starter_file})     




def setup_sitecustomize(prog_path):
  """
  <Purpose>
    On Windows CE, edits the sitecustomize.py file to reference the right
    program path, then copies it to the python directory.

  <Arguments>
    prog_path:
      Path where seattle is being installed.

  <Exceptions>
    Raises UnsupportedOSError if the version is not Windows CE.
    Raises IOError if the original sitecustomize.py file doesn't exist or 
    if the python path specified in repy_constants doesn't exist.

  <Side Effects>
    None.
    
  <Returns>
    None.
  """
  original_fname = prog_path + os.sep + "sitecustomize.py"
  if not OS == "WindowsCE":
    raise UnsupportedOSError
  elif not os.path.exists(original_fname):
    raise IOError("Could not find sitecustomize.py under " + prog_path)
  else: 
    python_dir = os.path.dirname(repy_constants.PATH_PYTHON_INSTALL)
    if not os.path.isdir(python_dir):
      raise IOError("Could not find repy_constants.PATH_PYTHON_INSTALL")
    elif os.path.exists(python_dir + os.sep + "sitecustomize.py"):
      raise IOError("sitecustomize.py already existed in python directory")
    else:
      preprocess_file(original_fname, {"%PROG_PATH%": prog_path})
      shutil.copy(original_fname, python_dir + os.sep + "sitecustomize.py")




def generate_keys(prog_path):
  """
  <Purpose>
    Uses createnodekeys module to generate the keys for the node.

  <Arguments>
    prog_path:
      The path to the directory where seattle is being installed.

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  orig_dir = os.getcwd()
  os.chdir(prog_path)

  createnodekeys.initialize_keys(KEYBITSIZE)
  os.chdir(orig_dir)
  



def start_seattle(scripts_path):
  """
  <Purpose>
    Starts seattle by running the starter file on any system.

  <Arguments>
    scripts_path:
      Path to the directory containing the seattle scripts.

  <Exceptions>
    IOError if the starter file can not be found under scripts_path.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  starter_file_path = '"' + scripts_path + os.sep + get_starter_file_name() + '"'
  if OS == "Windows":
    p = subprocess.Popen('"' + starter_file_path + '"', shell=True)
    p.wait()
  elif OS == "WindowsCE":
    windows_api.launch_python_script(starter_file_path)
  else:
    p = subprocess.Popen(starter_file_path, shell=True)
    p.wait()




def install(prog_path):
  """
  <Purpose>
    Goes through all the steps necessary to install seattle on the current
    system, printing status messages if not in silent mode.

  <Arguments>
    prog_path:
      Path to the directory containing the seattle program files.

  <Exceptions>
    None.
    
  <Side Effects>
    None.
    
  <Returns>
    None.
  """

  if OS not in SUPPORTED_OSES:
    raise UnsupportedOSError


  # Anthony - This will test if os.urandom is implemented on the OS
  # If we did not check here and os.urandom raised a NotImplementedError
  # the next step (setup_start) would surely fail when it tried
  # to generate a keypair.
  try:
    os.urandom(1)
  except NotImplementedError:
    _output("Failed.")
    _output("No source of OS-specific randomness")
    _output("On a UNIX-like system this would be /dev/urandom, and on Windows it is CryptGenRandom.")
    _output("Please email the Seattle project for additional support")
    return


  prog_path = os.path.realpath(prog_path)
  scripts_path = os.path.realpath(prog_path + os.sep + "..")


# Run the benchmarks to benchmark system resources and generate
  # resource files and the vesseldict.
  _output("System benchmark starting...")
  # Anthony - this file will be logged to until the v2 directory has
  # been created, this will not happen until after the benchmarks
  # have run and the majority of the installer state has been created.
  benchmark_logfileobj = file("installer_benchmark.log", 'a+')
    
  try:
    benchmark_resources.main(prog_path, RESOURCE_PERCENTAGE, benchmark_logfileobj)
  except benchmark_resources.InsufficientResourceError:
    exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
    traceback.print_exception(exceptionType, exceptionValue, \
                              exceptionTraceback, file=benchmark_logfileobj)
    _output("Failed.")
    _output("This install cannot succeed because resources are " + \
            "insufficient. This could be because the percentage of donated " + \
            "resources is to small or because a custom install had to many " + \
            "vessels. ")
    _output("Please email the Seattle project for additional support, if you can send the installer_benchmark.log and vesselinfo files they will help us diagnose the issue.")
    benchmark_logfileobj.close()
    return
  except Exception:
    exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
    traceback.print_exception(exceptionType, exceptionValue, \
                              exceptionTraceback, file=benchmark_logfileobj)
    _output("Failed.")
    _output("Seattle encountered an error, this install cannot succeed either because required installation info is corrupted or resources are insufficient.")
    _output("Please email the Seattle project for additional support, if you can send the installer_benchmark.log and vesselinfo files they will help us diagnose the issue.")
    benchmark_logfileobj.close()
    return
  
  # Transfer the contents of the file used to log the benchmark and creation
  # of vessel states. The service logger cannot be used sooner because
  # the seattle vessel directory has not yet been created.
  # Initialize the service logger.
  servicelogger.init('installInfo')
  benchmark_logfileobj.seek(0)
  servicelogger.log(benchmark_logfileobj.read())
  benchmark_logfileobj.close()
  os.remove(benchmark_logfileobj.name)
  
  _output("Benchmark complete and vessels created!")

  _output("Generating the Node Manager rsa keys.  This may take a few " \
            + "minutes...")
  # Generate the Node Manager keys separately from setting up seattle to run at
  # startup since seattle does not need to be setup to run at boot in order to
  # be executed manually.
  # To avoid a race condition with cron on non-Windows systems, the keys must
  # always be generated before setting up seattle to run at boot.
  generate_keys(prog_path)
  _output("Keys generated!")
    



  # If it is a Windows system, customize the batch files.
  if "Windows" in OS:
    _output("Customizing seattle batch files...")

    # Customize the start, stop, and uninstall batch files so the client is
    # not required to be in the seattle directory to run them.
    for batchfile in [get_starter_file_name(), get_stopper_file_name(),
                      get_uninstaller_file_name()]:
      preprocess_file(scripts_path + os.sep + get_starter_file_name(),
                      {"%PROG_PATH%": prog_path})

    preprocess_file(prog_path + os.sep + get_starter_shortcut_file_name(),
                    {"%PROG_PATH%": prog_path})

    full_startup_file_path,file_path_exists = \
        get_filepath_of_win_startup_folder_with_link_to_seattle()
    setup_win_uninstaller_and_starter_shortcut_script(prog_path,scripts_path,
                                                      full_startup_file_path)
    _output("Done!")



  # Setup the sitecustomize.py file, if running on WindowsCE.
  if OS == "WindowsCE":
    _output("Configuring python...")
    setup_sitecustomize(prog_path)
    _output("Done!")



  # Configure seattle to run at startup if this hasn't been disabled by the
  # command-line option.
  if not DISABLE_STARTUP_SCRIPT:
    _output("Preparing Seattle to run automatically at startup...")
    # This try: block attempts to install seattle to run at startup. If it
    # fails, continue on with the rest of the install process.
    try:
      if OS == "Windows" or OS == "WindowsCE":
        setup_win_startup(prog_path,scripts_path)
      elif OS == "Linux" or OS == "Darwin":
        setup_linux_or_mac_startup(prog_path,scripts_path)
        _output("Seattle is setup to run at startup!")

    except UnsupportedOSError,u:
      raise UnsupportedOSError(u)
    except AlreadyInstalledError,a:
      raise AlreadyInstalledError(a)
    # If an unpredicted error is raised while setting up seattle to run at
    # startup, it is caught here.
    except Exception,e:
      _output("seattle could not be installed to run automatically at " \
                + "startup for the following reason: " + str(e))
      _output("Continguing with the installation process now.  To manually " \
                + "run seattle at any time, just run " \
                + get_starter_file_name())
      servicelogger.log(time.strftime(" seattle was NOT installed on this " \
                                        + "system for the following reason: " \
                                        + str(e) + ". %m-%d-%Y  %H:%M:%S"))



  # Everything has been installed, so start seattle
  _output("Starting seattle...")
  start_seattle(scripts_path)



  # The install went smoothly.
  _output("seattle was successfully installed and has been started!")
  _output("To learn more about useful, optional scripts related to running seattle, see the README file.")

  servicelogger.log(time.strftime(" seattle completed installation on: " \
                                    + "%m-%d-%Y %H:%M:%S"))




def usage():
  """
  Intended for internal use.
  Prints command line usage of script.
  """
  print "python seattleinstaller.py [--usage] [--disable-startup-script] [--percent float] [--nm-key-bitsize bitsize] [--nm-ip ip] [--nm-iface iface] [--repy-ip ip] [--repy-iface iface] [--repy-nootherips] [--onlynetwork] [-s] [install_dir]]"
  print "Info:"
  print "--disable-startup-script\tDoes not install the Seattle startup script, meaning that Seattle will not automatically start running at machine start up. It is recommended that this option only be used in exceptional circumstances."
  print "--percent percent\ Specifies the desired percentage of available system resources to donate. Default percentage: " + str(RESOURCE_PERCENTAGE)
  print "--nm-key-bitsize bitsize\tSpecifies the desired bitsize of the Node Manager keys. Default bitsize: " + str(KEYBITSIZE)
  print "--nm-ip IP\t\tSpecifies a preferred IP for the NM. Multiple may be specified, they will be used in the specified order."
  print "--nm-iface iface\tSpecifies a preferred interface for the NM. Multiple may be specified, they will be used in the specified order."
  print "--repy-ip, --repy-iface. See --nm-ip and --nm-iface. These flags only affect repy and are separate from the Node Manager."
  print "--repy-nootherips\tSpecifies that repy is only allowed to use explicit IP's and interfaces."
  print "--onlynetwork\t\tDoes not reinstall Seattle, but updates the network restrictions information."




def in_opts(opts, flag):
  """
  Intended for internal use.
  Checks through the list of tuples containing options that getopt returns
  to see if flag is in them.
  """
  for tup in opts:
    if flag in tup:
      return True
  return False




def main():
  """
  Intended for internal use.
  If you want to run the installer from another script, use
  install.install(prog_path).
  Parses command line arguments and calls install() accordingly.
  """
  #Initialize the service logger.
  servicelogger.init('installInfo')

  global SILENT_MODE
  global RESOURCE_PERCENTAGE
  opts = None
  args = None
  try:
    # Armon: Changed getopt to accept parameters for Repy and NM IP/Iface restrictions, also a special disable flag
    opts, args = getopt.getopt(sys.argv[1:], "hs",["percent=", "nm-key-bitsize=","nm-ip=","nm-iface=","repy-ip=","repy-iface=","repy-nootherips","onlynetwork","disable-startup-script","usage"])
  except getopt.GetoptError, err:
    print str(err)
    usage()
    return
  if in_opts(opts, "-h"):
    usage()
    return
  if in_opts(opts, "-s"):
    SILENT_MODE = True
  # The install directory defaults to the current directory.
  install_dir = "."
  if len(args) > 0:
    install_dir = args[0]

  # Armon: Special flag for testing purposes, disables the actual install
  disable_install = False

  # Armon: Generate the Restrictions Information for the NM and Repy
  repy_restricted = False
  repy_nootherips = False
  repy_user_preference = []
  nm_restricted = False
  nm_user_preference = []
  
  # Iterate through the flags, checking for IP/Iface restrictions, maintain order 
  for (flag, value) in opts:
    if flag == "--onlynetwork":
      disable_install = True
    elif flag == "--percent":
      # Check to see that the desired percentage of system resources is valid
      # I do not see a reason someone couldnt donate 20.5 percent so it
      # will be allowed for now.
      try:
        RESOURCE_PERCENTAGE = float(value)
      except ValueError:
        usage()
        return      
      if RESOURCE_PERCENTAGE <= 0.0 or RESOURCE_PERCENTAGE > 100.0:
        usage()
        return
    elif flag == "--nm-ip":
      nm_restricted = True
      nm_user_preference.append((True, value))
    elif flag == "--nm-iface":
      nm_restricted = True
      nm_user_preference.append((False, value))
    elif flag == "--repy-ip":
      repy_restricted = True
      repy_user_preference.append((True, value))
    elif flag == "--repy-iface":
      repy_restricted = True
      repy_user_preference.append((False,value))
    elif flag == "--repy-nootherips":
      repy_restricted = True
      repy_nootherips = True
    elif flag == "--nm-key-bitsize":
      global KEYBITSIZE
      KEYBITSIZE = int(value)
    elif flag == "--disable-startup-script":
      global DISABLE_STARTUP_SCRIPT
      DISABLE_STARTUP_SCRIPT = True
      _output("Seattle will not be configured to run automatically at boot.")
    elif flag == "--usage":
      usage()
      return


  
  # Build the configuration dictionary
  config = {}
  config['nm_restricted'] = nm_restricted
  config['nm_user_preference'] = nm_user_preference
  config['repy_restricted'] = repy_restricted
  config['repy_user_preference'] = repy_user_preference
  config['repy_nootherips'] = repy_nootherips 

  # Armon: Inject the configuration information
  configuration = persist.restore_object("nodeman.cfg")
  configuration['networkrestrictions'] = config
  persist.commit_object(configuration,"nodeman.cfg") 
  
  if not disable_install:
    try:
      install(install_dir)
    except AlreadyInstalledError:
      print "seattle was already installed."


if __name__ == "__main__":
  main()
  
