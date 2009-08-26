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
     zack.publickey zack.privatekey ./Installers/ 1.0a

"""

import os
import sys
import shutil
import subprocess
import tempfile
import zipfile
import tarfile

import clean_folder

# The name of the base directory in each installer
BASE_INSTALL_DIR = "seattle_repy/"  # slash after name must be included
# The base name of each installer = for instance, "seattle_win.zip"
INSTALLER_NAME = "seattle"

# The path to the directory, relative the trunk, of specific files for Windows
WINDOWS_PATH = "/dist/win/scripts"
# The path to the directory, relative the trunk, of specific files for WinMob
WINMOB_PATH = "/dist/winmob/scripts"
# The path to the directory, relative the trunk, of specific files for Linux
LINUX_PATH = "/dist/linux/scripts"
# The path to the directory, relative the trunk, of specific files for Mac
MAC_PATH = "/dist/mac/scripts"




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
  if "win" in dist:
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
  passed = True
  badflag = ""

  for char in flags:
    if char not in valid_flags:
      passed = False
      if char not in badflag:
        badflag += char
    if char in required_flags:
      got_required_flag = True

  if passed and got_required_flag:
    return (True, badflag)
  else:
    return (False, badflag)



def prepare_gen_install_files(trunk_location, temp_install_dir, include_tests,
                              pubkey, privkey, finalfiles):
  """
  <Purpose>
    Prepare the general installation files needed for all installers and deposit
    them in the temporary folder designated to hold the installation files,
    including the metainfo file.

  <Arguments>
    trunk_location:

      The path to the trunk directory of the repository, used to find all the
      requisite files that make up the installer.

    pubkey:

      The path to a public key that will be used to generate the metainfo file.

    privkey: 

      The path to a private key that will be used to generate the metainfo file.

    temp_install_dir:

      The temporary directory where the general installer files will be placed.

    include_tests:

      Boolean variable specifying whether or not to include tests in installer.

    finalfiles:

      Boolean variable specifying whether or not to prepare the final files
      after the metafile has been written

  <Exceptions>
    IOError on bad file paths.    

  <Side Effects>
    All general installation files placed into the specified temporary
    installation directory.

  <Returns>
    List of all the files in the temporary installation directory, which will
    be added to the installer tarball.
  """

  # Run preparetest to generate and place all the general installation files
  # in the temporary installation directory
  os.chdir(trunk_location)
  if include_tests:
    p = subprocess.Popen("python preparetest.py -t " + 
                         temp_install_dir, shell=True)
    p.wait()
  else:
    p = subprocess.Popen("python preparetest.py " + 
                         temp_install_dir, shell=True)
    p.wait()

  # Copy Anthony Honstain's benchmarking scripts to the installer
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


  # Clean the folder of unnecessary files before generating metafile
  clean_folder.clean_folder(trunk_location + "/dist/initial_files.fi",
                            temp_install_dir)
    
  # Generate the metainfo file
  os.chdir(temp_install_dir)
  writemetainfocommand = "python writemetainfo.py " + privkey + " " + pubkey + " -n"
  p = subprocess.Popen(writemetainfocommand, shell=True)
  p.wait()

  # If specified, copy remaining files that should not be included in the
  # metafile into the temporary installation directory
  if finalfiles:
    # Copy the static files to the program directory
    shutil.copy2(trunk_location + "/dist/nodeman.cfg", temp_install_dir)
    shutil.copy2(trunk_location + "/dist/resources.offcut", temp_install_dir)
    # Copy the universal installer to the program directory
    shutil.copy2(trunk_location + "/dist/seattleinstaller.py", temp_install_dir)
    # Run clean_folder a final time to ensure the final directory only contains
    # the necessary files.
    clean_folder.clean_folder(trunk_location + "/dist/final_files.fi",
                              temp_install_dir)


  return os.listdir(temp_install_dir)



def package_win_or_winmob(trunk_location, temp_install_dir, temp_tarball_dir,
                          inst_name, install_files):
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

    install_files:

      A list of the general installation files located in the temporary
      installation directory.


  <Exceptions>
    IOError on bad file paths.

  <Side Effects>
    Puts the final tarball in the temporary tarball directory.

  <Returns>
    None.  
   """


  os.chdir(temp_tarball_dir)

  # Open the Windows zipfile for writing, or create a zipfile for Windows Mobile
  if not "winmob" in inst_name:
    shutil.copy2(trunk_location + "/dist/win/partial_win.zip",
                 temp_tarball_dir + "/" + inst_name)
    installer_zipfile = zipfile.ZipFile(inst_name, "a")
  else:
    installer_zipfile = zipfile.ZipFile(inst_name, "w")

  # Put all general installer files to zipfile
  os.chdir(temp_install_dir)
  for fname in install_files:
    installer_zipfile.write(fname, BASE_INSTALL_DIR + "/" + fname)

  # Put all files specific to this installer into zipfile
  if not "winmob" in inst_name:
    os.chdir(trunk_location + WINDOWS_PATH)
  else:
    os.chdir(trunk_location + WINMOB_PATH)
  curdir = os.getcwd()
  specific_files = os.listdir(curdir)

  # Remove any svn repository files
  for svn in specific_files:
    if "svn" in svn:
      specific_files.remove(svn)

  for fname in specific_files:
    installer_zipfile.write(fname, BASE_INSTALL_DIR + "/" + fname)
  installer_zipfile.close()
    



def package_linux_or_mac(trunk_location, temp_install_dir, temp_tarball_dir,
                         inst_name, install_files):
  """
  <Purpose>
    Packages the installation files for Linux or Macintosh into a tarball
    and appends the specific installation scripts for this OS.

  <Arguments>
    trunk_location:
      
      The location of the repository trunk.

    temp_install_dir:

      The path to the temporary installation directory.

    temp_tarball_dir:

      The path to the directory in which the installer tarball(s) is stored.

    inst_name:

      The name that the final installer should have.

    install_files:

      A list of the general installation files located in the temporary
      installation directory.


  <Exceptions>
    IOError on bad file paths.

  <Side Effects>
    Puts the final tarball in the temporary tarball directory.

  <Returns>
    None.  
   """

  os.chdir(temp_tarball_dir)
  installer_tarfile = tarfile.open(inst_name, "w:gz")
    
  # Put all general installer files into the tar file
  os.chdir(temp_install_dir)
  for fname in install_files:
    installer_tarfile.add(fname, BASE_INSTALL_DIR + "/" + fname, False)

  # Put all files specific to this installer into tar file
  if "linux" in inst_name:
    os.chdir(trunk_location + LINUX_PATH)
  else:
    os.chdir(trunk_location + MAC_PATH)
  curdir = os.getcwd()
  specific_files = os.listdir(curdir)

  # Remove any svn repository files
  for svn in specific_files:
    if "svn" in svn:
      specific_files.remove(svn)

  for fname in specific_files:
    installer_tarfile.add(fname, BASE_INSTALL_DIR + "/" + fname, False)
  installer_tarfile.close()



def build(systems, trunk_location, pubkey, privkey, output_dir, version=""):
  """
  <Purpose>
    This function creates a base installer for each specified OS and deposits
    them in the specified output directory.
  
  <Arguments>
    systems:
      
      A string of the flags (identifying the OS for which to create an
      installer) specified by the user on the command line.  This string may
      also contain the optional character "t" to have tests included in the
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

  print "Creating installer(s) - this may take a few moments...."

  # Create temporary directory for the installation
  temp_install_dir = tempfile.mkdtemp()
  # Create temporary directory for creating the tarball(s)
  temp_tarball_dir = tempfile.mkdtemp()


  # Create all general files to go into installer
  include_tests = False
  if "t" in systems:
      include_tests = True
  install_files = prepare_gen_install_files(trunk_location, temp_install_dir,
                                            include_tests, pubkey, privkey,
                                            True)



  # Build individual installer(s)
  packages = []

  # Package the Windows installer
  if "w" in systems or "a" in systems:
    inst_name = get_inst_name("win", version)
    package_win_or_winmob(trunk_location, temp_install_dir, temp_tarball_dir,
                          inst_name, install_files)
    packages.append(inst_name)


  # Package the Linux installer
  if "l" in systems or "a" in systems:
    inst_name = get_inst_name("linux", version)
    package_linux_or_mac(trunk_location, temp_install_dir, temp_tarball_dir,
                         inst_name, install_files)
    packages.append(inst_name)


  # Package the Mac installer
  if "m" in systems or "a" in systems:
    inst_name = get_inst_name("mac", version)
    package_linux_or_mac(trunk_location, temp_install_dir, temp_tarball_dir,
                         inst_name, install_files)
    packages.append(inst_name)


  # Package the Windows Mobile installer
  if "i" in systems or "a" in systems:
    inst_name = get_inst_name("winmob", version)
    package_win_or_winmob(trunk_location, temp_install_dir, temp_tarball_dir,
                          inst_name, install_files)
    packages.append(inst_name)



  # Move the installer tarball(s) to the specified output directory
  os.chdir(temp_tarball_dir)
  for tarball in os.listdir(temp_tarball_dir):
    shutil.copy2(tarball, output_dir)

  # Remove the temporary directories
  shutil.rmtree(temp_install_dir)
  shutil.rmtree(temp_tarball_dir)

  print ""
  print "Finished building installers"
  print ""
  print "Created the following files in " + output_dir + ":"
  for package in packages:
      print package


    
def usage():
  print "usage: python make_base_installer.py m|l|w|i|a|t path/to/trunk/ pubkey privkey output/dir/ [version of seattle]"
  print "flags: m,l,w,i,a,t represent the OS for which the base installer is being created.  m = Macintosh, l = Linux, w = Windows, i = Windows Mobile, a = all systems. t = include tests in installer."



def main():
  # Test argument flags
  if len(sys.argv) < 6 or len(sys.argv) > 7:
    usage()
    return
  flags = sys.argv[1]
  passed, offense = check_flags(flags)
  if not passed:
    if offense == "":
      print "Requires at least one of these flags: m,l,w,i,a"
      usage()
    else:
      print "Invalid flag(s): " + offense
    return

  # Test argument paths
  if not os.path.exists(sys.argv[2]):  # Test trunk
    raise IOError("Trunk not found at " + trunk_location)
  if not os.path.exists(sys.argv[5]):  # Test output directory
    raise IOError("Output directory does not exist.")
  if not os.path.exists(sys.argv[3]):  # Test public key
    raise IOError("Public key not found.")
  if not os.path.exists(sys.argv[4]):  # Test private key
    raise IOError("Private key not found.")

  # Get full, canonical path names from arguments
  trunk_location = os.path.realpath(sys.argv[2])
  pubkey = os.path.realpath(sys.argv[3])
  privkey = os.path.realpath(sys.argv[4])
  output_dir = os.path.realpath(sys.argv[5])
  
  # Build installer(s)
  if len(sys.argv) == 6:
    build(flags, trunk_location, pubkey, privkey, output_dir)
  else:
    build(flags, trunk_location, pubkey, privkey, output_dir, sys.argv[6])



if __name__ == "__main__":
    main()
