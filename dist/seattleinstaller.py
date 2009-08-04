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




SILENT_MODE = False
KEYBITSIZE = 1024
OS = nonportable.ostype
SUPPORTED_OSES = ["Windows", "WindowsCE", "Linux", "Darwin"]
SUPPORTED_WINDOWS_VERSIONS = ["XP", "Vista", "CE"]

# Import subprocess if not in WindowsCE
subprocess = None
if OS != "WindowsCE":
  import subprocess

# Import windows_api if in Windows or WindowsCE
windows_api = None
if OS == "WindowsCE":
  import windows_api




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
      be ignored, but lines that contain this symbol will be preprocessed up to
      that point. Defaults to "#", set as the empty string to preprocess all
      lines in the file.

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
    commentedLine = ""

    if comment == "" or not fileline.startswith(comment):

      # Substitute the replacement string into the uncommented file line
      # First, test whether there is an in-line comment.
      if comment != "" and comment in fileline:
        splitLine = fileline.split(comment)
        fileline = splitLine[0]
        for splitcomment in splitLine[1:]:
          commentedLine = commentedLine + comment + splitcomment

      for substitute in substitute_dict:
        fileline = fileline.replace(substitute, substitute_dict[substitute])

    edited_lines.append(fileline + commentedLine)

  base_fileobj.close()

  # Now, write those modified lines to the actual starter file location
  final_fileobj = open(filename, "w")
  final_fileobj.writelines(edited_lines)
  final_fileobj.close()




def get_win_startup_folder(version):
  """
  <Purpose>
    Given the Windows version it is running on, returns the path to the
    startup folder if it can be found.
  
  <Arguments>
    version:
      The current version of Windows; must be either "XP", "Vista", or "CE".

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    The path to the startup folder if it can be found, an empty string otherwise.
  """
  if (OS != "Windows" and OS != "WindowsCE") or version not in SUPPORTED_WINDOWS_VERSIONS:
    # The OS is not a version of Windows or a supported version of Windows
    raise UnsupportedOSError

  else:
    try:
      # See if the installer executable found the startup folder
      # in the registry
      startup_file = open("startup.dat")
      startup_path = ""
      for line in startup_file:
        if line:
          startup_path = line
        if startup_path and os.path.exists(startup_path):
          return startup_path
        else:
          raise Exception

    except:
      try:
        # If that file doesn't exist or is invalid, try checking the registry key.
        key_handle = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Shell Folders")
        (startup_path, data_type) = _winreg.QueryValueEx(key_handle, "Startup")
        if startup_path and os.path.exists(startup_path):
          return startup_path   

      except:
        # If that fails, look in a couple obvious places, based on OS version
        if version == "Vista":
          # Look in probable Vista places
          startup_path = os.environ.get("HOMEDRIVE") + os.environ.get("HOMEPATH") + "\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup"
          if os.path.exists(startup_path):
            return startup_path

        elif version == "XP":
          # Look in probable XP places
          startup_path = os.environ.get("HOMEDRIVE") + os.environ.get("HOMEPATH") + "\\Start Menu\\Programs\\Startup"
          if os.path.exists(startup_path):
            return startup_path

        elif version == "CE":
          # Look in probable Mobile places
          startup_path = "\\Windows\\Startup"
          if os.path.exists(startup_path):
            return startup_path
          # Zack: Deleted duplicate copy of "if os.path.exists(...) block


          # Else return blank to indicate failure
        return ""




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
    UnsupportedOSError if teh operating system requested is not supported.

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




def setup_startup(prog_path):
  """
  <Purpose>
    Sets up seattle to run at startup on the current computer. On Windows, this
    means adding a script to the startup folder, while on Unix systems it means
    adding a line to the crontab.

  <Arguments>
    prog_path:
      The path to the directory where the seattle files are located.

  <Exceptions>
    UnsupportedOSError if the os is not supported.
    AlreadyInstalledError if seattle has already been installed on the system.

  <Side Effects>
    None.

  <Returns>
    The path to the startup file on Windows if successful.
    True on Linux if successful.
    False if it fails.
  """

  # First check to make sure the OS is supported
  if OS == "Windows" or OS == "WindowsCE":
    _output("Adding a script to the startup folder...")
    # Try setting up the startup folder on a Windows system
    startup_path = get_win_startup_folder(platform.release())
    if not startup_path:
      return False

    # Check to see if we've already installed a startup script here
    startupscript = startup_path + os.sep + get_starter_file_name()
    if os.path.exists(startupscript):
      raise AlreadyInstalledError

    # Now that we have the startup folder, and we know seattle is not installed,
    # customize the start, stop, and uninstall batch files so the client is not
    # required to be in the seattle directory to run them.
    for batchfile in [get_starter_file_name(), get_stopper_file_name(), get_uninstaller_file_name()]:
      preprocess_file(prog_path + os.sep + get_starter_file_name(), {"%PROG_PATH%": prog_path})

    # Copy the start batch file to the startup folder.
    shutil.copy(prog_path + os.sep + get_starter_file_name(), startup_path + os.sep + get_starter_file_name())

    return startupscript


  elif OS == "Linux" or OS == "Darwin":
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
    
    # Generate a temp file with the user's crontab plus our task
    # (tempfile module used as suggested in Jacob Appelbaum's patch)
    cron_line = '*/10 * * * * "' + prog_path + '/' + \
        get_starter_file_name() + '" >> /dev/null 2>&1\n'
    crontab_contents = subprocess.Popen("crontab -l", shell=True, stdout=subprocess.PIPE).stdout
    filedescriptor, tmp_location = tempfile.mkstemp("temp", "seattle")
    for line in crontab_contents:
      os.write(filedescriptor, line)
    os.write(filedescriptor, cron_line)
    os.close(filedescriptor)

    # Now, replace the crontab with that temp file
    os.popen('crontab "' + tmp_location + '"')
    os.unlink(tmp_location)
    return True


  else:
    # The operating system is not supported
    raise UnsupportedOSError




def setup_win_uninstaller(prog_path, starter_file):
  """
  <Purpose>
    On Windows, customizes the base uninstaller located in the install directory so
    that it will remove the starter file from the startup folder when run.

  <Arguments>
    prog_path:
      The path to the directory where seattle is being installed.
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
  elif not os.path.exists(starter_file):
    raise IOError
  elif not os.path.exists(prog_path + os.sep + get_uninstaller_file_name()):
    raise IOError

  preprocess_file(prog_path + os.sep + get_uninstaller_file_name(), {"%STARTER_FILE%": starter_file})     



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
  



def start_seattle(prog_path):
  """
  <Purpose>
    Starts seattle by running the starter file on any system.

  <Arguments>
    prog_path:
      Path to the directory in which seattle is being installed.

  <Exceptions>
    IOError if the starter file can not be found under prog_path.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  starter_file_path = '"' + prog_path + os.sep + get_starter_file_name() + '"'
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
    Goes through all the steps necessary to install seattle on the current system, printing
    status messages if not in silent mode.

  <Arguments>
    prog_path:
      Path to the directory in which seattle is being installed.

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
  
  # First, generate the Node Manager keys since seattle does not need to be
  # setup to run at boot in order to be executed manually

  _output("Generating the Node Manager rsa keys.  This may take a few minutes...")

  # To avoid a race condition with cron on non-Windows systems, the keys must
  # always be generated before setting up seattle to run at boot
  generate_keys(prog_path)
  _output("Keys generated!")
    

  _output("Preparing Seattle to run automatically...")
  # Second, setup seattle to run at startup
  startup_success = setup_startup(prog_path)
  if startup_success:
    _output("Seattle is setup to run at startup!")
  
    # Next, if it is a Windows system and we were able to find the startup folder,
    # customize the uninstaller
    if "Windows" in OS:
      _output("Customizing uninstaller...")
      setup_win_uninstaller(prog_path, startup_success)
      _output("Done!")

    # Next, setup the sitecustomize.py file, if running on WindowsCE
    if OS == "WindowsCE":
      _output("Configuring python...")
      setup_sitecustomize(prog_path)
      _output("Done!")

    # Everything has been installed, so start seattle
    _output("Starting seattle...")
    start_seattle(prog_path)


    # The install went smoothly.
    _output("seattle was successfully installed and has been started!")
    _output("To learn more about useful, optional scripts related to running seattle, see the README file.")

    servicelogger.log(time.strftime(" seattle was installed on: %m-%d-%Y %H:%M:%S"))

  else: 
    # We weren't able to find the startup folder for Windows systems    
    servicelogger.log(time.strftime(" seattle was NOT installed on this system because the starter file could not be located: %m-%d-%Y at %H:%M:%S"))

    _output("seattle was not able to be setup to run at startup.")
    _output("seattle could not be installed correctly to run at startup on your machine because the starter folder for your system could not be located.")
    _output("To manually run seattle at any time, just run " +
            get_starter_file_name() + ".")


def usage():
  """
  Intended for internal use.
  Prints command line usage of script.
  """
  print "python seattleinstaller.py [nm-key-bitsize [--nm-ip ip] [--nm-iface iface] [--repy-ip ip] [--repy-iface iface] [--repy-nootherips] [--onlynetwork] [-s] [install_dir]]"
  print "Info:"
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

  #Set the specified bitsize for the nodemanager keys
  global KEYBITSIZE
  if len(sys.argv) > 1:
    KEYBITSIZE = int(sys.argv[1])


  global SILENT_MODE
  opts = None
  args = None
  try:
    # Armon: Changed getopt to accept parameters for Repy and NM IP/Iface restrictions, also a special disable flag
    # Zack: changed sys.argv[1:] to sys.argv[2:] because KEYBITSIZE global is specified by the first parameter.  see usage()  --> KEYBITSIZE must be specified first and is not optional if other arguments are being passed in
    opts, args = getopt.getopt(sys.argv[2:], "hs",["nm-ip=","nm-iface=","repy-ip=","repy-iface=","repy-nootherips","onlynetwork"])
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
  if len(args) > 1:
    install_dir = args[1]

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
  
