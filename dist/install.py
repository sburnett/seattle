"""
<Program Name>
  univ_install.py

<Started>
  February 10, 2009

<Author>
  Carter Butaud

<Purpose>
  Installs seattle on any supported system. This means setting up the computer to
  run seattle at startup, generating node keys, creating an uninstaller, customizing
  configuration files, and starting seattle itself.
"""

# Let's make sure the version of python is supported
import checkpythonversion
checkpythonversion.ensure_python_version_is_supported()

import os
import shutil
import platform
import subprocess
import sys
import getopt
import tempfile
import re

# Python should do this by default, but doesn't on Windows CE
sys.path.append(os.getcwd())
import nonportable
import createnodekeys
import repy_constants


SILENT_MODE = False
OS = nonportable.ostype
SUPPORTED_OSES = ["Windows", "WindowsCE", "Linux"]


class UnsupportedOSError(Exception):
  pass

class UnsupportedPythonError(Exception):
  def __init__(self, version):
    self.version = version

class AlreadyInstalledError(Exception):
  pass


def output(text):
  """
  For internal use.
  If the program is not in silent mode, prints the inputted text.
  """
  global SILENT_MODE
  if not SILENT_MODE:
    print text



def preprocess_file(fn, subs, comment="#"):
  """
  <Purpose>
    Looks through the given file and makes all substitutions indicated.

  <Arguments>
    fn:
      Path to the file which will be preprocesses.
    subs:
      Map of words to be substituted to their replacements, e.g.,
      {"word_in_file_1": "replacement1", "word_in_file_2": "replacement2"}
    comment:
      A string which demarks commented lines; lines that start with with
      this will be ignored. Defaults to "#", set as blank to preprocess
      all lines in the file.

  <Exceptions>
    IOError on bad filename.
  
  <Side Effects>
    None.

  <Returns>
    None.
  """
  edited_lines = []
  base_f = open(fn)
  for line in base_f:
    to_append = line
    if comment == "" or not line.startswith(comment):
      # Substitute the replacement string for all instances of sub_out on an
      # uncommented line.
      for sub_out in subs:
        to_append = to_append.replace(sub_out, subs[sub_out])
    edited_lines.append(to_append)
  base_f.close()

  # Now, write those modified lines to the actual starter file location
  final_f = open(fn, "w")
  final_f.writelines(edited_lines)
  final_f.close()



def get_startup_folder(version):
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
  global OS
  if (OS != "Windows" and OS != "WindowsCE") or version not in ["XP", "Vista", "CE"]:
    # If it's not a known version, return blank for failure
    return ""

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
        startup_path = "\\Windows\\StartUp"
        if os.path.exists(startup_path):
          return startup_path

      # Else return blank to indicate failure
      return ""


def get_starter_file_name():
  """
  <Purpose>
    Returns what the name of the starter file on the current operating system
    should be.

  <Arguments>
    None.

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    The name of the starter file on systems that should have a starter file, or an
    empty string on systems that shouldn't.
  """
  global OS
  if OS == "Windows":
    return "start_seattle.bat"
  if OS == "WindowsCE":
    return "start_seattle.py"
  if OS == "Linux":
    return "start_seattle.sh"
  return ""


def get_uninstaller_name():
  """
  <Purpose>
    Returns what the name of the uninstaller file on the current operating system
    should be.

  <Arguments>
    None.

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    The name of the uninstaller file.
  """
  global OS
  if OS == "Windows":
    return "uninstall.bat"
  if OS == "WindowsCE":
    return "uninstall.py"
  return "uninstall.sh"



def setup_startup(prog_path):
  """
  <Purpose>
    Sets up seattle to run at startup on the current computer. On Windows, this means adding a script to the
    startup folder, while on Unix systems it means adding a line to the crontab.

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
  global OS
  global SUPPORTED_OSES
  # First check to make sure it's a supported os
  if OS not in SUPPORTED_OSES:
    raise UnsupportedOSError

  if OS == "Windows" or OS == "WindowsCE":
    # Try setting up the startup folder on a Windows system
    startup = get_startup_folder(platform.release())
    if not startup:
      return False

    # Check to see if we've already installed a startup script here
    if os.path.exists(startup + os.sep + get_starter_file_name()):
      raise AlreadyInstalledError
    
    # Now that we have the startup folder and we know seattle is not installed,
    # customize the starter file.
    preprocess_file(prog_path + os.sep + get_starter_file_name(), 
                    {"%PROG_PATH%": prog_path})
  
    # And copy it to the startup folder.
    shutil.copy(prog_path + os.sep + get_starter_file_name(), startup + os.sep + get_starter_file_name())
    
    return (startup + os.sep + get_starter_file_name())

  else:
    # Assume we're running on a Linux system, so add a line to the crontab
    
    # First, customize the starter file in the install directory
    preprocess_file(prog_path + os.sep + get_starter_file_name(),
                    {"%PROG_PATH%": prog_path})

    # Next check to see if the line is already there
    crontab_f = subprocess.Popen("crontab -l", shell=True, stdout=subprocess.PIPE).stdout
    found = False
    for line in crontab_f:
      if re.search(os.sep + get_starter_file_name(), line):
        found = True
    crontab_f.close()
    if found:
      raise AlreadyInstalledError
  
    # Now we know they don't, so we should add it
    
    # First, generate a temp file with the user's crontab plus our task
    # (tempfile module used as suggested in Jacob Appelbaum's patch)
    real_install_dir = os.path.realpath(prog_path)
    cron_line = '*/10 * * * * "' + real_install_dir + '/' + \
        get_starter_file_name() + '" >> "' + real_install_dir + \
        '/cron_log.txt"' + ' 2>> "' + real_install_dir + \
        '/cron_log.txt"' + os.linesep
    crontab_f = subprocess.Popen("crontab -l", shell=True, stdout=subprocess.PIPE).stdout
    fd, s_tmp = tempfile.mkstemp("temp", "seattle")
    for line in crontab_f:
      os.write(fd, line)
    os.write(fd, cron_line)
    os.close(fd)

    # Now, replace the crontab with that temp file
    os.popen('crontab "' + s_tmp + '"')
    os.unlink(s_tmp
)
    return True


def setup_uninstaller(prog_path, starter_file):
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
  global OS
  if OS != "Windows" and OS != "WindowsCE":
    raise UnsupportedOSError
  if not os.path.exists(starter_file):
    raise IOError
  if not os.path.exists(prog_path + os.sep + get_uninstaller_name()):
    raise IOError
  preprocess_file(prog_path + os.sep + get_uninstaller_name(), {"%STARTER_FILE%": starter_file})     



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
  global OS
  original_fn = prog_path + os.sep + "sitecustomize.py"
  if not OS == "WindowsCE":
    raise UnsupportedOSError
  if not os.path.exists(original_fn):
    raise IOError("Could not find sitecustomize.py under prog_path")
  if not os.isdir(repy_constants.PYTHON_PATH):
    raise IOError("Could not find repy_constants.PYTHON_PATH")
  preprocess_file(original_fn,
                  {"%PROG_PATH%": prog_path})
  shutil.move(original_fn, repy_constants.PYTHON_PATH + os.sep + 
              "sitecustomize.py")


def setup_constants(prog_path):
  """
  <Purpose>
    Customizes necessary constants in repy_constants.py.

  <Arguments>
    prog_path:
      Path to the directory in which seattle is being installed.

  <Exceptions>
    IOError if repy_constants.py does not exist under prog_path.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  if not os.path.exists(prog_path + os.sep + "repy_constants.py"):
    raise IOError
  preprocess_file(prog_path + os.sep + "repy_constants.py",
                  {"%PROG_PATH%": prog_path})


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
  createnodekeys.initialize_keys()
  os.chdir(orig_dir)
  

def setup_permissions(prog_path):
  """
  <Purpose>
    On a Linux system, sets the permissions to scripts in the install directory correctly.

  <Arguments>
    prog_path:
      Path to the directory in which seattle is being installed.

  <Exceptions>
    UnsupportedOSError if run on a Windows system.
    IOError if any of the scripts do not exist.

  <Side Effects>
    None.
  
  <Returns>
    None.
  """
  global OS
  if OS == "Windows" or OS == "WindowsCE":
    raise UnsupportedOSError
  scripts = [get_starter_file_name(), get_uninstaller_name()]
  for script in scripts:
    if not os.path.exists(prog_path + os.sep + script):
      raise IOError("Could not find script " + script + " under prog_path.")
  for script in scripts:
    os.chmod(prog_path + os.sep + script, 0744)


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
  global OS
  starter_fn = prog_path + os.sep + get_starter_file_name()
  if OS == "Windows":
    p = subprocess.Popen("start /min " + starter_fn)
    p.wait()
  elif OS == "WindowsCE":
    windows_api.launchPythonScript(starter_fn)
  else:
    p = subprocess.Popen(starter_fn)
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
    UnsupportedPythonError if the Python version is unsupported.
    
  <Side Effects>
    None.
    
  <Returns>
    None.
  """
  global OS
  # Make sure we're running a supported version of Python
  version = sys.version.split(" ")[0].split(".")
  if version[0] != '2' or version[1] != '5':
    # If it's not Python 2.5
    raise UnsupportedPythonError(version[0] + "." + version[1])

  prog_path = os.path.realpath(prog_path)

  # First, setup seattle to run at startup
  output("Preparing seattle to run at startup...")
  startup_retval = setup_startup(prog_path)
  if startup_retval:
    output("Done!")
  else:
    output("Failed.")
  
  # Next, if it is a Windows system and we were able to find the startup folder,
  # customize the uninstaller
  if (OS == "Windows" or OS == "WindowsCE") and startup_retval:
    output("Creating uninstaller...")
    setup_uninstaller(prog_path, startup_retval)
    output("Done!")

  # Next, setup the sitecustomize.py file, if running on WindowsCE
  if OS == "WindowsCE":
    ouput("Configuring python...")
    setup_sitecustomize(prog_path)
    output("Done!")
  
  # Next, customize the constants file
  output("Configuing seattle constants...")
  setup_constants(prog_path)
  output("Done!")

  # Next, generate the node keys
  output("Generating node keys (may take a few minutes)...")
  generate_keys(prog_path)
  output("Done!")
  
  # If on a Linux-like system, make sure that the scripts have the right permissions
  if OS != "Windows" and OS != "WindowsCE":
    output("Setting script permissions...")
    setup_permissions(prog_path)
    output("Done!")
    
  # Everything has been installed, so start seattle
  output("Starting seattle...")
  start_seattle(prog_path)
  output("Started!")
  
  # Display final messages
  if startup_retval:
    # The install went smoothly.
    output("seattle was successfully installed and has been started!")
    output("If you would like to uninstall seattle at any time, just run " +
           get_uninstaller_name() + ".")
    output("After running it, you can remove the directory containing seattle.")
  else:
    # We weren't able to find the startup folder
    output("seattle could not be installed correctly to run at startup, but it has been started.")
    output("If you would like to manually run seattle at any time, just run " + 
           get_starter_file_name() + ".")


def usage():
  """
  Intended for internal use.
  Prints command line usage of script.
  """
  print "python install.py [-s] [install_dir]"


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
  global SILENT_MODE
  opts = None
  args = None
  try:
    opts, args = getopt.getopt(sys.argv[1:], "hs")
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
  
  try:
    install(install_dir)
  except UnsupportedPythonError, err:
    print "Your version of Python (" + err.version + ") is not supported."
  except AlreadyInstalledError:
    print "seattle was already installed."


if __name__ == "__main__":
  main()
