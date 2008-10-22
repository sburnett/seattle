# To run build_installers, make sure it is located in the dist directory,
# and then call it with the desired name of the distribution as an argument.
# That is, if you want to produce the files "seattlex.x.x_win.zip",
# "seattlex.x.x_mac.tgz", and "seattlex.x.x_linux.tgz", just run
# "python build_installers.zip seattlex.x.x".
# NOTE: This script is not portable, and will only run on Linux (or
# probably OSX)

import sys
import os
import clean_folder
import shutil

DISTS = ["win", "linux"]
INSTALL_DIR = "seattle_repy"
UPDATER_PRIV_KEY = "updater_keys" + os.sep + "updater.privatekey"
UPDATER_PUB_KEY = "updater_keys" + os.sep + "updater.publickey"

def output(text):
    print text

def main(dist_name):
    # First, run preparetest once for each of the distributions,
    for dist in DISTS:
        output("Creating " + dist + " distribution...")
        prog_dir = dist + os.sep + INSTALL_DIR
        os.system("mkdir " + prog_dir + " &> /dev/null")
        os.chdir("..")
        os.system("python preparetest.py dist" + os.sep + prog_dir)
        # Next, do an initial cleaning of the directory created
        os.chdir("dist")
        clean_folder.main("preparetest.fi", prog_dir)
        # Generate the metainfo file
        os.chdir(prog_dir)
        os.system("python writemetainfo.py .." + os.sep + ".." + os.sep + UPDATER_PRIV_KEY + " .." + os.sep + ".." + os.sep + UPDATER_PUB_KEY)

        # Copy the nodeman.cfg file from the dist directory
        shutil.copyfile(".." + os.sep + ".." + os.sep + "nodeman.cfg", "nodeman.cfg")
        
        os.chdir(".." + os.sep + "..")
                
        output("Done!")
        
    # Package up the Windows installer
    output("Packaging win distribution...")
    os.chdir("win")
    win_dist = dist_name + "_win.zip"
    os.system("rm -f " + win_dist)
    os.system("cp partial_win.zip " + win_dist)
    os.system("cp scripts" + os.sep + "* " + INSTALL_DIR)
    os.system("zip -r " + win_dist + " " + INSTALL_DIR)
    output("Created " + win_dist)
    
    # Package up the Linux installer
    output("Packaging linux distribution...")
    os.chdir(".." + os.sep + "linux")
    linux_dist = dist_name + "_linux.tgz"
    os.system("cp -p scripts" + os.sep + "* " + INSTALL_DIR)
    os.system("rm -f " + linux_dist)
    os.system("tar -czf " + linux_dist + " " + INSTALL_DIR)
    output("Created " + linux_dist)

    # Copy the Linux installer to the Mac directory
    output("Copying linux distribution to mac folder...")
    mac_dist = dist_name + "_mac.tgz"
    os.system("cp " + linux_dist + " .." + os.sep + "mac" + os.sep + mac_dist)
    output("Created " + mac_dist)

        
    
if __name__ == "__main__":
    dist_name = ""
    if len(sys.argv) < 2:
        dist_name = "seattle"
    else:
        dist_name = sys.argv[1]
    main(dist_name)
