"""
<Program Name>
  update_and_build.py

<Started>
  December 1, 2008

<Author>
  Carter Butaud

<Purpose>
  Builds an installer from the latest code and in the process
  copies the proper files to the directory that the software
  updaters check for updates.
"""

import make_base_installers
import os
import sys
import shutil
import subprocess

DEBUG = False

# For unique temp folders
PROGRAM_NAME = "build_and_update"
UPDATER_SITE = "/home/couvb/public_html/updatesite/real"
if DEBUG:
    UPDATER_SITE = "/home/couvb/public_html/updatesite/test"
INSTALL_DIR = "seattle_repy"
DIST_DIR = "/var/www/dist"
if DEBUG:
    DIST_DIR = "/home/butaud/temp/dist"

def main():
    if len(sys.argv) < 4:
        print "usage: python update_and_build.py trunk/location/ publickey privatekey [version]"
    else:
        if not DEBUG:
            # Confirm that the user really wants to update all the software
            print "This will update all of the client software!"
            print "Are you sure you want to proceed? (y/n)"
            if raw_input()[0].lower() == "y":
                if len(sys.argv) < 3:
                    build_and_update(sys.argv[1], sys.argv[2], sys.argv[3])
                else:
                    build_and_update(sys.argv[1], sys.argv[2], 
                                     sys.argv[3], sys.argv[4])
            else:
                print "Use make_base_installers instead to just create installers."
        else:
            # If we're in DEBUG mode, don't bother to confirm
            print "Operating in debug mode..."
            if len(sys.argv) < 3:
                build_and_update(sys.argv[1], sys.argv[2], sys.argv[3])
            else:
                build_and_update(sys.argv[1], sys.argv[2], 
                                 sys.argv[3], sys.argv[4])




def build_and_update(trunk_location, pubkey, privkey, version=""):
    """
    <Purpose>
      Builds the installers, copying the proper files to the software updater
      directory in the process, and deposits the installers in the dist
      directory. Only meant to be run on the actual seattle server.

    <Arguments>
      trunk_location:
        The path to the repository's trunk directory.
      version:
        The version of the distribution, which will be appended to the
        base name of each installer.

    <Exceptions>
      IOError on bad filepaths.

    <Side Effects>
      None.
     
    <Returns>
      None.
    """
    if not os.path.exists(trunk_location):
        raise IOError("Trunk could not be found at " + trunk_location)
    update_dir = UPDATER_SITE
    
    # First, make the temp directories
    temp_dir = "/tmp/" + PROGRAM_NAME + str(os.getpid())
    if not os.path.exists(temp_dir):
        os.mkdir(temp_dir)
    install_dir = temp_dir + "/" + INSTALL_DIR
    if os.path.exists(install_dir):
        shutil.rmtree(install_dir)
    os.mkdir(install_dir)
    
    # Next, prepare the installation files
    make_base_installers.prepare_initial_files(trunk_location, False, pubkey, privkey, install_dir)
    
    # Copy the files to the updater site
    p = subprocess.Popen("rm -f " + update_dir + "/*", shell=True)
    p.wait()
    p = subprocess.Popen("cp " + install_dir + "/* " + update_dir, shell=True)
    p.wait()

    # Finish preparing the installation files
    make_base_installers.prepare_final_files(trunk_location, install_dir)
    
    # Now, package each installer
    dist_dir = trunk_location + "/dist"
    make_base_installers.package_win(dist_dir, install_dir, make_base_installers.get_inst_name("win", version), DIST_DIR)
    make_base_installers.package_linux(dist_dir, install_dir, make_base_installers.get_inst_name("linux", version), DIST_DIR)
    make_base_installers.package_mac(dist_dir, install_dir, make_base_installers.get_inst_name("mac", version), DIST_DIR)

    # Remove the temp directory when done.
    shutil.rmtree(temp_dir)
    print "Done!"

if __name__ == "__main__":
    main()
