"""
<Program Name>
  make_base_installers.py

<Started>
  November 2008

<Author>
  Carter Butaud

<Purpose>
  Builds the base installers for one or more of the supported
  operating systems, depending on options given. Runs on Linux
  systems only.
"""

import os
import sys
import imp
import shutil
import subprocess

import clean_folder
import build_installers

# The name of the script (used to create a temp folder)
PROGRAM_NAME = "make_base_installers"
# The name of the base directory in each installer
INSTALL_DIR = "seattle_repy"
# The base name of each installer = for instance, "seattle_win.zip"
INSTALLER_NAME = "seattle"



def get_inst_name(dist, version):
    # Given the OS it is for and the version, returns
    # the proper name for the installer. Meant for
    # internal use.
    base_name = INSTALLER_NAME + version + "_" + dist
    if dist == "win":
        base_name += ".zip"
    if dist == "winmob":
        base_name += ".zip"
    if dist == "linux":
        base_name += ".tgz"
    if dist == "mac":
        base_name += ".tgz"
    return base_name



def check_args(argstr):
    """
    Checks that each character in the argument string is in valid_flags;
    returns a tuple containing False and the offending char if there are
    invalid characters.
    Also checks that there is at least one flag from each string in one_of,
    returns a tuple containing False and "req:" + the unsatisfied requirement
    string otherwise.
    Returns a tuple containing True and an empty string if no problems.
    """
    valid_flags = "mwliat"
    one_of = {"mwlia": False}
    passed = True
    offense = ""
    for char in argstr:
        if char not in valid_flags:
            passed = False
            if char not in offense:
                offense += char
        for reqstr in one_of:
            if char in reqstr:
                one_of[reqstr] = True
    for reqstr in one_of:
        if not one_of[reqstr]:
            return (False, "req:" + reqstr)
    return (passed, offense)


def prepare_initial_files(trunk_location, include_tests, pubkey, privkey, output_dir):
    """
    <Purpose>
      Given the location of the repository's trunk, it will prepare the
      files for the base installers (or for a software update) in a
      specified location, including all the files necessary for the
      metainfo file.
    
    <Arguments>
      trunk_location:
        The path to the trunk directory of the repository, used to
        find all the requisite files that make up the installer.
      pubkey:
        The path to a public key that will be used to generate the
        metainfo file.
      privkey: 
        The path to a private key that will be used to generate the
        metainfo file.
      output_dir:
        The directory where the installer files will be placed.
    
    <Exceptions>
      IOError on bad filepaths.
    
    <Side Effects>
      None.
      
    <Returns>
      None.
    """
    # Remember the original working directory
    orig_dir = os.getcwd()
    real_pubkey = os.path.realpath(pubkey)
    real_privkey = os.path.realpath(privkey)
    os.chdir(trunk_location)
    # Remember all important locations relative to the trunk
    dist_dir = os.getcwd() + "/dist"
    # Run preparetest, including the unit tests if necessary,
    # adding the files to the temp directory
    if include_tests:
        p = subprocess.Popen("python preparetest.py -t " + 
                             output_dir, shell=True)
        p.wait()
    else:
        p = subprocess.Popen("python preparetest.py " + 
                             output_dir, shell=True)
        p.wait()
    # Make sure that the folder is initially clean and correct
    clean_folder.clean_folder(dist_dir + "/initial_files.fi", output_dir)
    # Generate the metainfo file
    os.chdir(output_dir)
    writemetainfo = imp.load_source("writemetainfo", "writemetainfo.py")
    writemetainfo.create_metainfo_file(real_privkey, real_pubkey, True)
    os.chdir(orig_dir)



def prepare_final_files(trunk_location, output_dir):
    """
    <Purpose>
      Copies the files that should not be included in the metainfo file over to the
      install directory.
    
    <Arguments>
      trunk_location:
        The path to the trunk directory of the repository, used to
        find all the requisite files that make up the installer.
      output_dir:
        The directory where the installer files will be placed.
    
    <Exceptions>
      IOError on bad filepaths.
      
    <Side Effects>
      None.
    
    <Returns>
      None.
    """
    # Copy the static files to the program directory
    shutil.copy2(trunk_location + "/dist/nodeman.cfg", output_dir)
    shutil.copy2(trunk_location + "/dist/resources.offcut", output_dir)

    # Copy the universal installer to the program directory
    shutil.copy2(trunk_location + "/dist/install.py", output_dir)

    # Run clean_folder a second time to make sure the final
    # directory is in good shape.
    clean_folder.clean_folder(trunk_location + "/dist/final_files.fi", output_dir)



def package_win(dist_dir, install_dir, inst_name, output_dir):
    """
    <Purpose>
      Packages the installation files and appends the necessary scripts
      to create the Windows installer.
    
    <Arguments>
      dist_dir:
        The location of the dist directory in the trunk.
      install_dir:
        The location of the installation files.
      inst_name:
        The name that the final installer should have.
      output_dir:
        The final location of the installer.
    
    <Exceptions>
      IOError on bad filepaths.
    
    <Side Effects>
      None.
      
    <Returns>
      None.
    """
    # First, copy the partial zip file over from the repository
    shutil.copy2(dist_dir + "/win/partial_win.zip", output_dir + "/" + inst_name)
    # Now, append the files in the install directory to the
    # zip file.
    build_installers.append_to_zip(output_dir + "/" + inst_name, install_dir, INSTALL_DIR)
    # Finally, add the Windows specific scripts to the zip file
    build_installers.append_to_zip(output_dir + "/" + inst_name, dist_dir + "/win/scripts", INSTALL_DIR)




def package_winmob(dist_dir, install_dir, inst_name, output_dir):
    """
    <Purpose>
      Packages the installation files and appends the necessary scripts to create the Linux installer.
      
    <Arguments>
      dist_dir:
        The location of the dist directory in the trunk.
      install_dir:
        The location of the installation files.
      inst_name:
        The name that the final installer should have.
      output_dir:
        The final location of the installer.

    <Exceptions>
      IOError on bad filepaths.

    <Side Effects>
      None.

    <Returns>
      None.      
    """
    # First, package up the install directory into a zip file
    temp_zipfile = inst_name + "temp_" + str(os.getpid()) + ".zip"
    orig_dir = os.getcwd()
    os.chdir(install_dir + "/..")
    p = subprocess.Popen("zip -r " + temp_zipfile + " " 
                         + INSTALL_DIR + " >/dev/null", shell=True)
    p.wait()
    shutil.move(temp_zipfile, orig_dir)
    os.chdir(orig_dir)
    shutil.move(temp_zipfile, output_dir + "/" + inst_name)
    
    # Now, append the Mobile specific files to the tarball
    build_installers.append_to_zip(output_dir + "/" + inst_name, 
                                   dist_dir + "/winmob/scripts",
                                   INSTALL_DIR)



def package_linux(dist_dir, install_dir, inst_name, output_dir):
    """
    <Purpose>
      Packages the installation files and appends the necessary scripts
      to create the Linux installer.
    
    <Arguments>
      dist_dir:
        The location of the dist directory in the trunk.
      install_dir:
        The location of the installation files.
      inst_name:
        The name that the final installer should have.
      output_dir:
        The final location of the installer.
    
    <Exceptions>
      IOError on bad filepaths.
    
    <Side Effects>
      None.
      
    <Returns>
      None.
    """
    # First, package up the install directory into a tarball
    temp_tarball = inst_name + "temp_" + str(os.getpid()) + ".tgz"
    orig_dir = os.getcwd()
    os.chdir(install_dir + "/..")
    p = subprocess.Popen("tar -czf " + temp_tarball + 
                         " " + INSTALL_DIR, shell=True)
    p.wait()
    shutil.move(temp_tarball, orig_dir)
    os.chdir(orig_dir)
    shutil.move(temp_tarball, output_dir + "/" + inst_name)
    # Now, append the Linux-specific scripts to the tarball
    build_installers.append_to_tar(output_dir + "/" + inst_name, dist_dir + "/linux/scripts", INSTALL_DIR)



def package_mac(dist_dir, install_dir, inst_name, output_dir):
    """
    <Purpose>
      Packages the installation files and appends the necessary scripts
      to create the Mac installer.
    
    <Arguments>
      dist_dir:
        The location of the dist directory in the trunk.
      install_dir:
        The location of the installation files.
      inst_name:
        The name that the final installer should have.
      output_dir:
        The final location of the installer.
    
    <Exceptions>
      IOError on bad filepaths.
    
    <Side Effects>
      None.
      
    <Returns>
      None.
    """
    # Uncomment the following to build the Mac installer separately,
    # but make sure that the appropriate files are in the /mac/scripts
    # directory first.
    
    # First, create a new tarball with the standard files
    temp_tarball = inst_name + "temp_" + str(os.getpid()) + ".tgz"
    orig_dir = os.getcwd()
    os.chdir(install_dir + "/..")
    p = subprocess.Popen("tar -czf " + temp_tarball + 
                         " " + INSTALL_DIR, shell=True)
    p.wait()
    shutil.move(temp_tarball, orig_dir)
    os.chdir(orig_dir)
    shutil.move(temp_tarball, output_dir + "/" + inst_name)
    
    # Now, append the Mac specific files to the created tarball
    build_installers.append_to_tar(output_dir + "/" + inst_name, 
                                   dist_dir + "/mac/scripts",
                                   INSTALL_DIR)
    


def build(options, trunk_location, pubkey, privkey, output_dir, version=""):
    """
    <Purpose>
      Given the operating systems it should build installers for,
      the location of the repository's trunk, and an output directory,
      build will create a base installer for each specified OS and
      deposit them all in the output directory.

    <Arguments>
      options:
        Various options that influence how the installer is created.
        At least one of "m", "l", "w", "i", or "a" must be included to indicate
        which installer should be created - "m" for Mac, "l" for Linux,
        "w" for Windows, "i" for Windows Mobile, or "a" for all.
        Include "t" to indicate that the unit tests should be included \
        in the installers.
      trunk_location:
        The path to the trunk directory of the repository, used
        to find all the requisite files that make up the installer.
      pubkey:
        The path to a public key that should be used to generate
        the metainfo file.
      privkey:
        The path to a private key that should be used to generate 
        the metainfo file.
      output_dir:
        The directory that the base installers will end up in.
      version:
        Appended to the name of the installers, blank by default.
        For instance, setting version to "0.01a" will produce
        installers named "seattle0.01a_win.zip",
        "seattle0.01a_linux.tar", etc.

    <Exceptions>
      IOError on bad filepaths.
      
    <Side Effects>
      Prints status updates.

    <Returns
      None.
    """
    if not os.path.exists(trunk_location):
        raise IOError("Trunk not found at " + trunk_location)
    if not os.path.exists(output_dir):
        raise IOError("Output directory does not exist.")
    if not os.path.exists(pubkey):
        raise IOError("Public key not found.")
    if not os.path.exists(privkey):
        raise IOError("Private key not found.")
    orig_dir = os.getcwd()
    
    # First, create a temp directory
    temp_dir = "/tmp/" + PROGRAM_NAME + str(os.getpid())
    if not os.path.exists(temp_dir):
        os.mkdir(temp_dir)
    install_dir = temp_dir + "/" + INSTALL_DIR
    if os.path.exists(install_dir):
        shutil.rmtree(install_dir)
    os.mkdir(install_dir)
    os.chdir(trunk_location)
    
    # Remember all important locations relative to the trunk
    dist_dir = os.getcwd() + "/dist"
    keys_dir = dist_dir + "/updater_keys"
    os.chdir(orig_dir)
    include_tests = False
    if "t" in options:
        include_tests = True
    prepare_initial_files(trunk_location, include_tests, pubkey, privkey, install_dir)
    prepare_final_files(trunk_location, install_dir)

    # Now, package up the installer for each specified OS.
    packages = []
    if "w" in options.lower() or "a" in options.lower():
        # Package the Windows installer
        dist = "win"
        inst_name = get_inst_name(dist, version)
        package_win(dist_dir, install_dir, inst_name, temp_dir)
        shutil.copy2(temp_dir + "/" + inst_name, output_dir)
        packages.append(inst_name)
    
    if "l" in options.lower() or "a" in options.lower():
        # Package the Linux installer
        dist = "linux"
        inst_name = get_inst_name(dist, version)
        package_linux(dist_dir, install_dir, inst_name, temp_dir)
        shutil.copy2(temp_dir + "/" + inst_name, output_dir)
        packages.append(inst_name)

    if "m" in options.lower() or "a" in options.lower():
        # Package the Mac installer
        dist = "mac"
        inst_name = get_inst_name(dist, version)
        package_mac(dist_dir, install_dir, inst_name, temp_dir)
        shutil.copy2(temp_dir + "/" + inst_name, output_dir)
        packages.append(inst_name)

    if "i" in options.lower() or "a" in options.lower():
        # Package the Windows Mobile installer
        dist = "winmob"
        inst_name = get_inst_name(dist, version)
        package_winmob(dist_dir, install_dir, inst_name, temp_dir)
        shutil.copy2(temp_dir + "/" + inst_name, output_dir)
        packages.append(inst_name)

    # Clean up the temp directory
    shutil.rmtree(temp_dir)

    print ""
    print "Done!"
    print "Created the following files in " + output_dir + ":"
    for package in packages:
        print package


    
def usage():
    print "usage: python make_base_installer.py m|l|w|i|a|t path/to/trunk/ pubkey privkey output/dir/"



def main():
    if len(sys.argv) < 6:
        usage()
        return
    passed, offense = check_args(sys.argv[1])
    if not passed:
        if offense.startswith("req:"):
            print "Requires at least one of these flags: " + offense[4:]
            usage()
            return
        print "Invalid flag(s): " + offense
        return
    build(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])

if __name__ == "__main__":
    main()
