"""
<Program Name>
  make_base_installers.py

<Started>
  November 2008
    Revised May 23, 2009

<Author>
  Carter Butaud
    Revised by Zachary Boka

<Purpose>
  Builds the installers for one or more of the supported operating systems,
  depending on options given. Runs on Linux systems only.

  Usage: python make_base_installer.py m|l|w|i|a|t path/to/trunk/ pubkey
          privkey output/dir/ [version of seattle]
  Flags: m,l,w,i,a,t represent the OS for which the base installer is being
         created.  m = Macintosh, l = Linux, w = Windows, i = Windows Mobile,
         a = all systems. t = include tests in installer.

  Example of usage on command line:
    python ./Seattle/trunk/dist/make_base_installers.py a ./Seattle/trunk/
     user.publickey user.privatekey ./Installers/ 1.0a

"""

import os
import sys
import shutil
import subprocess
import tempfile
import zipfile
import tarfile

import clean_folder

# The name of the base directory in each installer.
BASE_INSTALL_DIR = "seattle" 
BASE_PROGRAM_FILES_DIR = "seattle/seattle_repy"
# The base name of each installer = for instance, "seattle_win.zip"
INSTALLER_NAME = "seattle"

# The path to the directory, relative the trunk, of the OS-specific files.
WINDOWS_PATH = "/dist/win/scripts"
WINMOB_PATH = "/dist/winmob/scripts"
LINUX_PATH = "/dist/linux/scripts"
MAC_PATH = "/dist/mac/scripts"

# The path to the directory, relative the trunk, of the OS-specific script
# wrappers.
WINDOWS_SCRIPT_WRAPPERS_PATH = "/dist/script_wrappers/win"
LINUX_SCRIPT_WRAPPERS_PATH = "/dist/script_wrappers/linux"
MAC_SCRIPT_WRAPPERS_PATH = "/dist/script_wrappers/mac"




def get_inst_name(dist, version):
  """
  <Purpose>
    Given the OS and the version, returns what the name of the installer
    will be.

  <Arguments>
    dist:
      The OS that the installer is intended for, should be Windows, Macintosh,
      Linux, or Winmob.

    version:

      A string to be appended between the dist and the extension - for
      instance, if version is "0.1d", then the Linux installer name will
      be "seattle_linux0.1d.tgz".

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    A string of the installer name for the specified OS and version.
  """

  base_name = INSTALLER_NAME + version + "_" + dist
  if "win" in dist or "Win" in dist or "WIN" in dist:
    base_name += ".zip"
  else:    
    base_name += ".tgz"
  return base_name




def check_flags(flags):
  """
  <Purpose>
    Checks that each character in 'flags' is a valid flag and that there is at
    least one valid flag (i.e., m,w,l,i,a).

  <Arguments>
    flags:

      String containing the flags passed in by the user.

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    If there is an invalid flag, returns a tuple containing False and the
    offending flag(s). If there is not at least one valid flag, this function
    returns a tuple containing False and the empty strings. Otherwise, if there
    are no problems, a tuple with True and the empty string is returned.
  """

  valid_flags = "mwliat"
  required_flags = "mwlia"
  got_required_flag = False
  no_invalid_flags = True
  badflag = ""

  # Check flags for invalid flags and required flags.
  for char in flags:
    if char not in valid_flags:
      no_invalid_flags = False
      if char not in badflag:
        badflag += char
    elif char in required_flags:
      got_required_flag = True

  # Return results.
  if no_invalid_flags and got_required_flag:
    return (True, badflag)
  else:
    return (False, badflag)




def prepare_gen_files(trunk_location,temp_install_dir,include_tests,pubkey,
                      privkey,finalfiles):
  """
  <Purpose>
    Prepare the general non-installer-specific files (needed for all installers)
    and deposit them into the temporary folder designated to hold the files
    that will be present in the base installer(s), including the metainfo file.

  <Arguments>
    trunk_location:
      The path to the trunk of the repository, used to find all the requisite
      files that appear in the installer.

    pubkey:
      The path to a public key that will be used to generate the metainfo file.

    privkey: 
      The path to a private key that will be used to generate the metainfo file.

    temp_install_dir:
      The temporary directory where the general files to be included in the
      installer will be placed.

    include_tests:
      Boolean variable specifying whether or not to include tests in installer.

    finalfiles:
      Boolean variable specifying whether or not to prepare the final files
      after the metafile has been written

  <Exceptions>
    IOError on bad file paths.    

  <Side Effects>
    All general non-installer-specific files placed into the specified temporary
    installation directory.

  <Returns>
    List of all the files in the temporary installation directory, which will
    be added to the installer tarball.
  """

  # Run preparetest to generate and place all the general installation files
  # in the temporary installation directory.

  # To run /trunk/preparetest.py, we must be in that directory (probably a bug
  # in preparetest.py?)
  original_dir = os.getcwd()
  os.chdir(trunk_location)
  if include_tests:
    p = subprocess.Popen(["python",trunk_location + os.sep + "preparetest.py",
                          "-t",temp_install_dir])
    p.wait()
  else:
    p = subprocess.Popen(["python",trunk_location + os.sep + "preparetest.py",
                          temp_install_dir])
    p.wait()
  os.chdir(original_dir)


  # Copy Anthony Honstain's benchmarking scripts to the installer.
  shutil.copy2(trunk_location + "/resource/benchmark_resources.py", 
               temp_install_dir)
  shutil.copy2(trunk_location + "/resource/Mac_BSD_resources.py",
               temp_install_dir)
  shutil.copy2(trunk_location + "/resource/create_installer_state.py",
               temp_install_dir)
  shutil.copy2(trunk_location + "/resource/measuredisk.py", temp_install_dir)
  shutil.copy2(trunk_location + "/resource/vessel.restrictions",
               temp_install_dir)
  shutil.copy2(trunk_location + "/resource/Linux_resources.py",
               temp_install_dir)
  shutil.copy2(trunk_location + "/resource/measure_random.py",
               temp_install_dir)
  shutil.copy2(trunk_location + "/resource/Win_WinCE_resources.py",
               temp_install_dir)

  # Copy the universal installer and uninstaller to the program directory.
  shutil.copy2(trunk_location + "/dist/seattleinstaller.py", temp_install_dir)
  shutil.copy2(trunk_location + "/dist/seattleuninstaller.py", temp_install_dir)

  # Clean the folder of unnecessary files before generating metafile.
  clean_folder.clean_folder(trunk_location + "/dist/initial_files.fi",
                            temp_install_dir)

  # To run writemetainfo.py, we must be in that directory (probably a bug in
  # writemetainfo.py?)
  os.chdir(temp_install_dir)

  # Generate the metainfo file.
  p = subprocess.Popen(["python",temp_install_dir + os.sep + "writemetainfo.py",
                        privkey,pubkey,"-n"])
  p.wait()
  os.chdir(original_dir)



  # If specified, copy remaining files that should not be included in the
  # metafile into the temporary installation directory.
  if finalfiles:
    # Copy the static files to the program directory.
    shutil.copy2(trunk_location + "/dist/nodeman.cfg", temp_install_dir)
    shutil.copy2(trunk_location + "/dist/resources.offcut", temp_install_dir)
    # Run clean_folder a final time to ensure the final directory contains all
    # the necessary files now that the last files have been added.
    clean_folder.clean_folder(trunk_location + "/dist/final_files.fi",
                              temp_install_dir)


  return os.listdir(temp_install_dir)




def package_win_or_winmob(trunk_location, temp_install_dir, temp_tarball_dir,
                          inst_name, gen_files):
  """
  <Purpose>
    Packages the installation files for Windows or Windows Mobile into a zipfile
    and appends the specific installation scripts for this OS.

  <Arguments>
    trunk_location:
      The location of the repository trunk.

    temp_install_dir:
      The path to the temporary installation directory.

    temp_tarball_dir:
      The path to the directory in which the installer zipfile(s) is stored.

    inst_name:
      The name that the final installer should have.

    gen_files:
      A list of the general non-installer-specific files located in the
      temporary installer directory.

  <Exceptions>
    IOError on bad file paths.

  <Side Effects>
    Puts the final tarball in the temporary tarball directory.

  <Returns>
    None.  
   """

  # Open the Windows zipfile for writing, or create a zipfile for Windows
  # Mobile.
  if not "winmob" in inst_name:
    shutil.copy2(trunk_location + "/dist/win/partial_win.zip",
                 temp_tarball_dir + os.sep + inst_name)
    installer_zipfile = zipfile.ZipFile(temp_tarball_dir + os.sep + inst_name,
                                        "a")
  else:
    installer_zipfile = zipfile.ZipFile(temp_tarball_dir + os.sep + inst_name,
                                        "w")

  # Put all general program files into zipfile.
  for fname in gen_files:
    installer_zipfile.write(temp_install_dir + os.sep + fname,
                            BASE_PROGRAM_FILES_DIR + os.sep + fname)



  # Put all files specific to this installer into zipfile.

  # First, copy all scripts that belong in the BASE_PROGRAM_FILES_DIR.
  if not "winmob" in inst_name:
    specific_installer_dir = trunk_location + os.sep + WINDOWS_PATH
  else:
    specific_installer_dir = trunk_location + os.sep + WINMOB_PATH
  specific_files = os.listdir(specific_installer_dir)

  # Add OS-specific files to the zipfile.
  for fname in specific_files:
    if not "svn" in fname and fname != "manifest.txt":
      # Add the README and LICENSE files to the highest-level directory
      # (BASE_INSTALL_DIR).
      if "LICENSE" in fname or "README" in fname:
        installer_zipfile.write(specific_installer_dir + os.sep + fname,
                                BASE_INSTALL_DIR + os.sep + fname)
      else:
        installer_zipfile.write(specific_installer_dir + os.sep + fname,
                              BASE_PROGRAM_FILES_DIR + os.sep + fname)



  # Second, copy all script wrappers (which call those in the
  # BASE_PROGRAM_FILES_DIR) to the BASE_INSTALL_DIR.
  if "winmob" in inst_name:
    return
  else:
    script_wrappers_dir = trunk_location + os.sep + WINDOWS_SCRIPT_WRAPPERS_PATH
  script_wrappers = os.listdir(script_wrappers_dir)

  # Add script wrappers to the zipfile.
  for fname in script_wrappers:
    if not "svn" in fname:
      installer_zipfile.write(script_wrappers_dir + os.sep + fname,
                              BASE_INSTALL_DIR + os.sep + fname)


  installer_zipfile.close()
    



def package_linux_or_mac(trunk_location, temp_install_dir, temp_tarball_dir,
                         inst_name, gen_files):
  """
  <Purpose>
    Packages the installation files specific to Linux or Macintosh into a
    tarball and appends the specific installation scripts for this OS.

  <Arguments>
    trunk_location:
      The location of the repository trunk.

    temp_install_dir:
      The path to the temporary installation directory.

    temp_tarball_dir:
      The path to the directory in which the installer tarball(s) is stored.

    inst_name:
      The name that the final installer should have.

    gen_files:
      A list of the general non-installer-specific files located in the
      temporary installer directory.

  <Exceptions>
    IOError on bad file paths.

  <Side Effects>
    Puts the final tarball in the temporary tarball directory.

  <Returns>
    None.  
   """

  installer_tarfile = tarfile.open(temp_tarball_dir + os.sep + inst_name,"w:gz")
    
  # Put all general installer files into the tar file.
  for fname in gen_files:
    installer_tarfile.add(temp_install_dir + os.sep + fname,
                          BASE_PROGRAM_FILES_DIR + os.sep + fname,False)



  # Put all Linux- and Mac-specific files in to tarball.


  # First, copy all scripts that belong in BASE_PROGRAM_FILES_DIR.
  if "linux" in inst_name:
    specific_installer_dir = trunk_location + os.sep + LINUX_PATH
  else:
    specific_installer_dir = trunk_location + os.sep + MAC_PATH
  specific_files = os.listdir(specific_installer_dir)

  # Add the OS-specific files to the tarfile.
  for fname in specific_files:
    if not "svn" in fname and fname != "manifest.txt":
      if "README" in fname or "LICENSE" in fname:
        installer_tarfile.add(specific_installer_dir + os.sep + fname,
                              BASE_INSTALL_DIR + os.sep + fname,False)
      else:
        installer_tarfile.add(specific_installer_dir + os.sep + fname,
                              BASE_PROGRAM_FILES_DIR + os.sep + fname,False)



  # Second, copy all script wrappers (which call those in the
  # BASE_PROGRAM_FILES_DIR) to the BASE_INSTALL_DIR.
  if "linux" in inst_name:
    script_wrappers_dir = trunk_location + os.sep + LINUX_SCRIPT_WRAPPERS_PATH
  else:
    script_wrappers_dir = trunk_location + os.sep + MAC_SCRIPT_WRAPPERS_PATH
  script_wrappers = os.listdir(script_wrappers_dir)

  # Add script wrappers to the zipfile.
  for fname in script_wrappers:
    if not "svn" in fname:
      installer_tarfile.add(script_wrappers_dir + os.sep + fname,
                            BASE_INSTALL_DIR + os.sep + fname,False)



  installer_tarfile.close()




def build(systems, trunk_location, pubkey, privkey, output_dir, version=""):
  """
  <Purpose>
    This function creates a base installer for each specified OS and deposits
    them in the specified output directory.
  
  <Arguments>
    systems:
      A string of the flags (identifying the operating systems for which to
      create installers) specified by the user on the command line.  This string
      may also contain the optional character "t" to have tests included in the
      installer.

    trunk_location:
      The path to the trunk directory of the repository, used to find all the
      requisite files that make up the installer.

    pubkey:
      The path to a public key that should be used to generate the metainfo
      file.

    privkey:
      The path to a private key that should be used to generate the metainfo
      file.

    output_dir:
      The directory in which the completed installer(s) will be placed.

    version:
      (Optional) Specifies the version of seattle for which the installer(s) are
      being created (blank by default) which will be appended to the installer
      name.
      For instance, setting version to "0.01a" will produce installers named
      "seattle0.01a_win.zip", "seattle0.01a_linux.tar", etc.

  <Exceptions>
    None.

  <Side Effects>
    Prints status updates and deposits installers into specified output
    directory.

  <Returns>
    None.
  """




def test_arguments(arguments):
  """
  """
  # Test argument flags
  if len(arguments) < 6 or len(arguments) > 7:
    return False
  flags = arguments[1]
  passed, offenses = check_flags(flags)
  if not passed:
    if offenses == "":
      print "Requires at least one of these flags: m,l,w,i,a"
    else:
      print "Invalid flag(s): " + offenses
    return False


  # Test argument paths, and get their absolute paths.
  # Test trunk path.
  if not os.path.exists(arguments[2]):
    raise IOError("Trunk not found at " + arguments[2])

  # Test output directory path.
  if not os.path.exists(sys.argv[5]):
    raise IOError("Output directory does not exist.")

  # Test public key path.
  if not os.path.exists(sys.argv[3]):
    raise IOError("Public key not found.")

  # Test private key path.
  if not os.path.exists(sys.argv[4]):
    raise IOError("Private key not found.")



  # All arguments are valid.
  return True




def usage():
  print "usage: python make_base_installer.py m|l|w|i|a|t path/to/trunk/ " \
      + "pubkey privkey output/dir/ [version of seattle]"
  print "flags: m,l,w,i,a,t represent the OS for which the base installer is " \
      + "being created.  m = Macintosh, l = Linux, w = Windows, " \
      + "i = Windows Mobile, a = all systems. t = include tests in installer."



def main():

  # Prepare to create installer(s).

  # Test arguments and find full pathnames.
  arguments_valid = test_arguments(sys.argv)
  if not arguments_valid:
    usage()
    return

  # Reaching this point means all arguments are valid, so set the variables and
  # get full pathnames when necessary.
  installer_type = sys.argv[1]
  trunk_location = os.path.realpath(sys.argv[2])
  output_dir = os.path.realpath(sys.argv[5])
  pubkey = os.path.realpath(sys.argv[3])
  privkey = os.path.realpath(sys.argv[4])
  version = ""
  if len(sys.argv) != 6:
    version = sys.argv[6]




  # Begin creating base installers.
  print "Creating installer(s) - this may take a few moments...."

  # Create temporary directory for the files to go into the installer.
  temp_install_dir = tempfile.mkdtemp()
  # Create temporary directory for creating the tarball(s) / zipfile(s).
  temp_tarball_dir = tempfile.mkdtemp()


  # Prepare all general non-installer-specific files to go into installer.
  print "Preparing all general non-OS-specific files...."
  include_tests = False
  if "t" in installer_type:
      include_tests = True
  gen_files = prepare_gen_files(trunk_location,temp_install_dir,include_tests,
                                pubkey,privkey,True)
  print "Complete."


  # Build individual installer(s).
  print "Customizing installer(s) for the specified operating system(s)...."
  created_installers = []

  # Package the Windows installer.
  if "w" in installer_type or "a" in installer_type:
    inst_name = get_inst_name("win", version)
    package_win_or_winmob(trunk_location, temp_install_dir, temp_tarball_dir,
                          inst_name, gen_files)
    created_installers.append(inst_name)


  # Package the Linux installer.
  if "l" in installer_type or "a" in installer_type:
    inst_name = get_inst_name("linux", version)
    package_linux_or_mac(trunk_location, temp_install_dir, temp_tarball_dir,
                         inst_name, gen_files)
    created_installers.append(inst_name)


  # Package the Mac installer.
  if "m" in installer_type or "a" in installer_type:
    inst_name = get_inst_name("mac", version)
    package_linux_or_mac(trunk_location, temp_install_dir, temp_tarball_dir,
                         inst_name, gen_files)
    created_installers.append(inst_name)


  # Package the Windows Mobile installer.
  if "i" in installer_type or "a" in installer_type:
    inst_name = get_inst_name("winmob", version)
    package_win_or_winmob(trunk_location, temp_install_dir, temp_tarball_dir,
                          inst_name, gen_files)
    created_installers.append(inst_name)



  # Move the installer tarball(s) / zipfile(s)  to the specified output
  # directory.
  for tarball in os.listdir(temp_tarball_dir):
    shutil.copy2(temp_tarball_dir + os.sep + tarball, output_dir)

  # Remove the temporary directories
  shutil.rmtree(temp_install_dir)
  shutil.rmtree(temp_tarball_dir)

  print
  print "Finished." 
  print
  print "The following base installers have been placed in " + output_dir + ":"
  for installer in created_installers:
      print installer




if __name__ == "__main__":
    main()
