"""
<Program Name>
  make_base_installers.py

<Started>
  November 2008

<Author>
  Carter Butaud

<Purpose>
  Builds the base installers for one or more of the supported
  operating systems, depending on options given.
"""

import os
import sys
import imp
import shutil

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
    if dist == "linux":
        base_name += ".tgz"
    if dist == "mac":
        base_name += ".tgz"
    return base_name

def prepare_files(trunk_location):


def build(which_os, trunk_location, output_dir, version=""):
    """
    <Purpose>
      Given the operating systems it should build installers for,
      the location of the repository's trunk, and an output directory,
      build will create a base installer for each specified OS and
      deposit them all in the output directory.

    <Arguments>
      which_os:
        Letters which represent the OSes that build will build
        installers for. Include "w" for Windows, "l" for Linux,
        and "m" for Mac.
      trunk_location:
        The path to the trunk directory of the repository, used
        to find all the requisite files that make up the installer.
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
    # Run preparetest, adding the files to the temp directory
    os.popen("python preparetest.py " + install_dir)
    os.chdir(temp_dir)
    # Make sure that the folder is initially clean and correct
    clean_folder.clean_folder(dist_dir + "/initial_files.fi", install_dir)
    # Generate the metainfo file
    os.chdir(install_dir)
    writemetainfo = imp.load_source("writemetainfo", "writemetainfo.py")
    writemetainfo.create_metainfo_file(keys_dir + "/updater.privatekey", keys_dir + "/updater.publickey")
    # Copy the static files to the program directory
    shutil.copy2(dist_dir + "/nodeman.cfg", ".")
    shutil.copy2(dist_dir + "/resources.offcut", ".")
    # Run clean_folder a second time to make sure the final
    # directory is in good shape.
    clean_folder.clean_folder(dist_dir + "/final_files.fi", ".")
    os.chdir(orig_dir)

    # Now, package up the installer for each specified OS.
    if "w" in which_os.lower():
        # Package the Windows installer
        dist = "win"
        inst_name = get_inst_name(dist, version)
        # First, copy the partial zip file over from the repository
        shutil.copy2(dist_dir + "/win/partial_win.zip", temp_dir)
        os.chdir(temp_dir)
        os.rename("partial_win.zip", inst_name)
        # Now, append the files in the install directory to the
        # zip file.
        build_installers.append_to_zip(inst_name, install_dir, INSTALL_DIR)
        # Finally, add the Windows specific scripts to the zip file
        build_installers.append_to_zip(inst_name, dist_dir + "/win/scripts", INSTALL_DIR)
        os.chdir(orig_dir)
    
    if "l" in which_os.lower():
        # Package the Linux installer
        dist = "linux"
        inst_name = get_inst_name(dist, version)
        # First, package up the install directory into a tarball
        os.chdir(temp_dir)
        os.popen("tar -czf " + inst_name + " " + install_dir)
        # Now, append the Linux-specific scripts to the tarball
        build_installers.append_to_tar(inst_name, dist_dir + "/linux/scripts", INSTALL_DIR)
        os.chdir(orig_dir)

    if "m" in which_os.lower():
        # Package the Linux installer
        dist = "mac"
        inst_name = get_inst_name(dist, version)
        # First, package up the install directory into a tarball
        os.chdir(temp_dir)
        os.popen("tar -czf " + inst_name + " " + install_dir)
        # Since the Mac installer is currently identical to the
        # Linux installer, append the Linux scripts to the tarball
        build_installers.append_to_tar(inst_name, dist_dir + "/linux/scripts", INSTALL_DIR)
        os.chdir(orig_dir)

def main():
    if len(sys.argv) < 4:
        print "usage: python make_base_installer.py m|l|w path/to/trunk/ output/dir"
    else:
        build(sys.argv[1], sys.argv[2], sys.argv[3])

if __name__ == "__main__":
    main()
