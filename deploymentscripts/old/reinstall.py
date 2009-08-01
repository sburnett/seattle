"""
<Program Name>
  reinstall.py

<Started>
  January 2009

<Author>
  Carter Butaud

<Purpose>
  Removes an old installation of seattle from
  a Linux computer and installs a fresh version.
"""

import os
import sys
import shutil

import uninstall


class ReinstallError(Exception):
    def __init__(self, value):
        self.parameter = value

    def __str__(self):
        return repr(self.parameter)


def error(text):
    """
    <Purpose>
      Prints an error message, formatting it according to the
      agreed upon standard.
    
    <Arguments>
      text:
        The string to be printed.
    
    <Exceptions>
      None.
      
    <Side Effects>
      None.
    
    <Returns>
      None.
    """
    print "ERROR: " + text

def warn(text):
    """
    <Purpose>
      Prints a warning message in the agreed upon format.

    <Arguments>
      text:
        The text to be printed.

    <Exceptions>
      None.

    <Side Effects>
      None.
    
    <Returns>
      None.
    """
    print "WARNING: " + text

def remove_old(seattle_dir):
    """
    <Purpose>
      Runs the uninstaller to delete the seattle starter line
      from the crontab, then deletes the seattle install
      directory.

    <Arguments>
      seattle_dir:
        The directory that seattle is installed in, which
        will be deleted.

    <Exceptions>
      None, but prints error messages if seattle_dir doesn't exist.

    <Side Effects>
      None.

    <Returns>
      None.
    """
    try:
        uninstall.uninstall(1)
        if not os.path.exists(seattle_dir):
            raise ReinstallError("Couldn't find old installation directory.")
        shutil.rmtree(seattle_dir)
    except ReinstallError, e:
        error(e.parameter)

def check_cleaned(seattle_dir):
    """
    <Purpose>
      Checks to make sure that the crontab doesn't
      have the seattle starter line in it and that
      seattle_dir is indeed gone. If so, produces 
      no output. Else, prints output prefaced with 
      error_pref.
    
    <Arguments>
      seattle_dir:
        The directory that originally contained seattle on
        the system.
    
    <Exceptions>
      None.
    
    <Side Effects>
      None.

    <Returns>
      None.
    """
    # First, check that the crontab line is gone
    crontab_f = os.popen("crontab -l")
    found = False
    for line in crontab_f:
        if uninstall.STARTER_SCRIPT_NAME in line:
            found = True
    if found:
        error("Failed to remove starter line from crontab.")
    
    # Next, check that the installation directory is gone
    if os.path.exists(seattle_dir):
        error("Failed to delete seattle directory.")



def install_new(parent_dir):
    """
    <Purpose>
      Copies the installer package from the current directory to
      the parent of the intended install directory, unzips it,
      and runs the installer.

    <Arguments>
      parent_dir:
        The directory where the install directory should be located.

    <Exceptions>
      None.
    
    <Side Effects>
      None.

    <Returns>
      None.
    """
    installer_name = "seattle_linux.tgz"
    install_dir = "seattle_repy"
    try:
        if not os.path.exists(parent_dir):
            raise ReinstallError("Intended parent directory could not be found.")
        # Copy the installer package to the parent directory and unzip it
        shutil.copyfile(installer_name, parent_dir + "/" + installer_name)
        orig_dir = os.getcwd()
        # Navigate to the parent directory so that the package is untarred
        # in the right place.
        os.chdir(parent_dir)
        os.popen("tar -xzf " + installer_name)
        os.chdir(orig_dir)

        # Run the installer script, passing it the install directory
        # as its argument and telling it to run silently.
        os.popen("python " + parent_dir + "/" + install_dir + "/seattleinstaller.py " + 
                 parent_dir + "/" + install_dir + " -s")
        
    except ReinstallError, e:
        # Have ReinstallErrors printed to stdout
        error(e.parameter)
    

def check_installed():
    """
    <Purpose>
      Checks that the program was installed correctly, printing
      errors if it isn't.

    <Arguments>
      None.

    <Exceptions>
      None.

    <Side Effects>
      None.

    <Returns>
      None.
    """
    crontab_f = os.popen("crontab -l")
    found = False
    for line in crontab_f:
        if uninstall.STARTER_SCRIPT_NAME in line:
            found = True
    if not found:
        error("Could not find starter line in crontab.")


def reinstall(parent_dir):
    """
    <Purpose>
      Removes an old installation of seattle located in parent_dir,
      and installs a fresh copy in the same directoryfrom an 
      installer package. Prints errors if any of the above steps fail.
      
    <Arguments>
      parent_dir:
        The parent directory of the old seattle installation directory
        (so it should contain a directory called seattle_repy).
        
    <Exceptions>
      None.
      
    <Side Effects>
      None.

    <Returns>
      None.
    """
    install_dir = "seattle_repy"
    remove_old(parent_dir + "/" + install_dir)
    check_cleaned(parent_dir + "/" + install_dir)
    install_new(parent_dir)
    check_installed()



def main():
    if len(sys.argv) < 2:
        print "Usage: python reinstall.py parent_dir"
    else:
        reinstall(sys.argv[1])



if __name__ == "__main__":
    main()
