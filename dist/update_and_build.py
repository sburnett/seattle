"""
<Program Name>
  update_and_build.py

<Started>
  December 1, 2008

<Author>
  Carter Butaud
  Zachary Boka

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
import tempfile

DEBUG = False

# For unique temp folders
PROGRAM_NAME = "build_and_update"
UPDATER_SITE = "/home/couvb/public_html/updatesite/test"
if DEBUG:
    UPDATER_SITE = "/home/zackrb/test/updatesite/"
INSTALL_DIR = "seattle_repy"
DIST_DIR = "/var/www/dist"
if DEBUG:
    DIST_DIR = "/home/zackrb/test/dist/"



def get_digits(s):
    """
    Utility function, returns all the digits from the given string.
    """
    retval = ""
    for c in s:
        if c.isdigit():
            retval += c
    return retval


def sanity_checks(trunk_location, updater_site, pubkey, version):
    """
    <Purpose>
      Checks to make sure that the keys and updater site in the softwareupdater
      script are the same as the ones that this script was given, and that the
      version's release is the same as the version specified in the nodemanager
      script.

    <Arguments>
      trunk_location:
        The path to the repository's trunk, used to find the softwareupdater
        and nodemanager scripts.
      updater_site:
        The local directory where the update is going to be pushed to.
      pubkey:
        Path to the public key that will be used when building the metainfo file
        for the installers and the softwareupdater.
      version:
        Version of the intended release.

    <Exceptions>
      IOError if the softwareupdater script, nodemanager script, or public key
      are not found.
    
    <Side Effects>
      None.

    <Returns>
      A tuple representing which checks passed and failed (True for pass,
      for for fail). The first element represents the url check, the second
      represents the public key check, and the third represents the version
      check.
    """
    updater_path = os.path.realpath(trunk_location +
                                    "/softwareupdater/softwareupdater.mix")
    nm_path = os.path.realpath(trunk_location + "/nodemanager/nmmain.py")
    
    if not os.path.exists(updater_path):
        raise IOError("Could not find softwareupdater script at " + 
                      updater_path)
    if not os.path.exists(nm_path):
        raise IOError("Could not find nodemanager script at " + nm_path)

    if not os.path.exists(pubkey):
        raise IOError("Could not find public key at " +
                      os.path.realpath(pubkey))

    updater_site = os.path.realpath(updater_site)
        
    # Find the values in the softwareupdater script
    script_f = open(updater_path)
    script_url = None
    script_key = []
    for line in script_f:
        if "softwareurl = " in line:
            script_url = line.split('"')[1]
        if "softwareupdatepublickey = " in line:
            script_key.append(get_digits(line.split(",")[0]))
            script_key.append(get_digits(line.split(",")[1]))
    script_f.close()
    
    # Find the version in the nodemanager script
    script_f = open(nm_path)
    script_version = None
    for line in script_f:
        if "version = " in line:
            script_version = line.split('"')[1]
    script_f.close()

    # Get the public key info from the given key.
    key_f = open(pubkey)
    given_key = []
    for line in key_f:
        if line:
            given_key.append(line.split(" ")[0])
            given_key.append(line.split(" ")[1])
    
    # Get the relevant part of the script url (everything that comes 
    # after "couvb")
    script_url_end = script_url[script_url.find("couvb") + len("couvb"):]
    if script_url_end[-1] == "/":
        script_url_end = script_url_end[:-1]

    # Check and see if the updater path ends the same way.
    urls_match = True
    if not updater_site.endswith(script_url_end):
        urls_match = False
    
    # Check to see if the script key and the given key match,
    keys_match = True
    if not (script_key[0] == given_key[0] and script_key[1] == given_key[1]):
        keys_match = False
    
    # Check to see if the script version and the given version match.
    versions_match = True
    if not script_version == version:
        versions_match = False
        
    return (urls_match, keys_match, versions_match)


def build_and_update(trunk_location, pubkey, privkey, version):
    """
    <Purpose>
      Builds the installers, copying the proper files to the software updater
      directory in the process, and deposits the installers in the dist
      directory. Only meant to be run on the actual seattle server.

    <Arguments>
      trunk_location:
        The path to the repository's trunk directory.
      pubkey:
        The public key to be used in the installers.
      privkey:
        The private key to be used in the installers.
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

    # Perform some sanity checks on to make sure the softwareupdater script
    # matches up with the specified info.
    urls_match, keys_match, versions_match = sanity_checks(trunk_location, 
                                                           update_dir, pubkey, 
                                                           version)
    if not (urls_match and keys_match and versions_match):
        if not urls_match:
            print "Updater location does not match with url in softwareupdater.mix."
        if not keys_match:
            print "Given public key does not match with key in softwareupdater.mix."
        if not versions_match:
            print "Given version does not match with version in nmmain.py"
        return
    print "Sanity checks passed."

    # First, make the temp directories

    # Zack: Create temporary directory for the installation
    temp_install_dir = tempfile.mkdtemp()
    # Zack: Create temporary directory for creating the tarball(s)
    temp_tarball_dir = tempfile.mkdtemp()

    
    # Next, prepare the installation files
    install_files = make_base_installers.prepare_gen_install_files(trunk_location,
                                                   temp_install_dir, False,
                                                   pubkey, privkey, True)
    
    # Copy the essential files to the updater site
    p = subprocess.Popen("rm -f " + update_dir + "/*", shell=True)
    p.wait()
    # Zack: Exclude the files that did not belong in the metafile
    for fname in install_files:
      if "nodeman.cfg" != fname and "resources.offcut" != fname \
         and "install.py" != fname: 
         shutil.copy2(fname, update_dir)


    # Now, package each installer
    make_base_installers.package_win_or_winmob(trunk_location, temp_install_dir, temp_tarball_dir, make_base_installers.get_inst_name("win", version), install_files)
    make_base_installers.package_win_or_winmob(trunk_location, temp_install_dir, temp_tarball_dir, make_base_installers.get_inst_name("winmob", version), install_files)
    make_base_installers.package_linux_or_mac(trunk_location, temp_install_dir, temp_tarball_dir, make_base_installers.get_inst_name("linux", version), install_files)
    make_base_installers.package_linux_or_mac(trunk_location, temp_install_dir, temp_tarball_dir, make_base_installers.get_inst_name("mac", version), install_files)

    # Zack: Move the installers to the specified output directory
    os.chdir(temp_tarball_dir)
    for tarball in os.listdir(temp_tarball_dir):
      shutil.copy2(tarball, DIST_DIR)



    # Copy each versioned installer name over the corresponding base
    # base installer
    for dist in ["win", "winmob","linux", "mac"]:
        versioned_name = make_base_installers.get_inst_name(dist, version)
        unversioned_name = make_base_installers.get_inst_name(dist, "")
        shutil.copy2(DIST_DIR + "/" + versioned_name, DIST_DIR + "/" + unversioned_name)

    # Zack: Remove the temp directory when done.
    shutil.rmtree(temp_install_dir)
    shutil.rmtree(temp_tarball_dir)
    print "Done!"



def main():
    if len(sys.argv) < 5:
        print "usage: python update_and_build.py trunk/location/ publickey privatekey version"
    else:
        trunk_location = os.path.realpath(sys.argv[1])
        pubkey = os.path.realpath(sys.argv[2])
        privkey = os.path.realpath(sys.argv[3])
        if not DEBUG:
            # Confirm that the user really wants to update all the software
            print "This will update all of the client software!"
            print "Are you sure you want to proceed? (y/n)"
            if raw_input()[0].lower() == "y":
                build_and_update(trunk_location, pubkey, privkey, sys.argv[4])
            else:
                print "Use make_base_installers instead to just create installers."
        else:
            # If we're in DEBUG mode, don't bother to confirm
            print "Operating in debug mode..."
            build_and_update(trunk_location, pubkey, privkey, sys.argv[4])



if __name__ == "__main__":
    main()
