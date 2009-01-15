"""
<Program Name>
  

<Started>
  

<Author>
  

<Purpose>
  

"""

import os
import re
import sys
import tempfile
import createnodekeys

STARTER_SCRIPT_NAME = "start_seattle.sh"

class InstallFailed(Exception):
    """
    <Purpose>

    <Side Effects>

    <Example Use>

    """
    def __init__(self, value=""):
        self.value = value
    
    def __str__(self):
        return repr(self.value)

# In case we want to silence or redirect output
# at some point, for internal use only
def output(text, silent=0):
    """
    <Purpose>
    
    <Arguments>

    <Exceptions>

    <Side Effects>

    <Returns>

    """
    if not silent == 1:
        print text
    
# If being run by itself, catch the exception and print output when
# the installation fails.
def main():
    """
    <Purpose>
    
    <Arguments>

    <Exceptions>

    <Side Effects>

    <Returns>

    """
    try:
        if len(sys.argv) < 2:
            install(".")
        elif len(sys.argv) == 2:
            if sys.argv[1] == "-s":
                install(".", 1)
            elif sys.argv[1] == "-h":
                print "Usage: python install.py [-s]"
            else:
                install(sys.argv[1])
        else:
            if "-s" in sys.argv[2:]:
                install(sys.argv[1], 1)
            else:
                install(sys.argv[1])
    except:
        output("Installation failed.")

def install(install_dir, silent=0):
    """
    <Purpose>
      Installs seattle on the computer by changing values in program 
      scripts and adding the starter scripts to the crontab. Must be 
      run from inside the root installation directory, where it is 
      originally located in the installer.
    
    <Arguments>
      install_dir:
        The seattle isntallation directory (containing nmmain.py,
        install.py, etc.).
      silent:
        Defaults to zero, prints no output if 1.

    <Exceptions>
      InstallFailed if the install fails for some reason.

    <Side Effects>
      None.

    <Returns>
      None.
    """
    # Check that we're running a supported version of Python
    version = sys.version.split(" ")[0].split(".")
    if version[0] != '2' or version[1] != '5':
        # If we're not, display an error and fail
        # TODO: This should be more robust - perhaps it can install the
        # correct version of Python, like the Windows installer
        output("Sorry, we don't support your version of Python (Python " + ".".join(version) + ").", silent)
        output("Please install Python 2.5 and try again.", silent)
        raise InstallFailed("Unsupported Python version")

    # Check the user's crontab to see if they already have
    # seattle installed
    crontab_f = os.popen("crontab -l")
    found = False
    for line in crontab_f:
        if re.search("/" + STARTER_SCRIPT_NAME, line):
            found = True
    crontab_f.close()
    if found:
        # If they do, print an error message and quit
        output("Seattle is already installed on your computer.", silent)
        raise InstallFailed("Seattle already installed")
        
    # Now we know they don't, so we should add it
    output("Adding to startup...", silent)
    # First, generate a temp file with the user's crontab plus
    # our task (tempfile module used as suggested in Jacob
    # Appelbaum's patch)
    real_install_dir = os.path.realpath(install_dir)
    cron_line = '*/10 * * * * "' + real_install_dir + '/' + \
        STARTER_SCRIPT_NAME + '" >> "' + real_install_dir + \
        '/cron_log.txt"' + ' 2>> "' + real_install_dir + \
        '/cron_log.txt"' +  os.linesep
    crontab_f = os.popen("crontab -l")
    fd, s_tmp = tempfile.mkstemp("temp", "seattle")
    for line in crontab_f:
        os.write(fd, line)
    os.write(fd, cron_line)
    os.close(fd)

    # Then, replace the crontab with that file
    os.popen('crontab "' + s_tmp + '"')
    os.unlink(s_tmp)
    output("Done.", silent)
    
    # Next, run the script to generate the node's keys
    output("Generating identity key (may take a few minutes)...", silent)
    orig_dir = os.getcwd()
    os.chdir(install_dir)
    createnodekeys.initialize_keys()
    os.chdir(orig_dir)
    output("Done.", silent)

    # Then, setup the starter script with the name of the installation
    # directory
    output("Starting seattle...", silent)
    starter_f = open(install_dir + "/" + STARTER_SCRIPT_NAME, "r")
    lines = []
    install_dir_real = os.path.realpath(install_dir)
    for line in starter_f:
        lines.append(re.sub("%PROG_PATH%", install_dir_real, line))
    starter_f.close()
    starter_f = open(install_dir + "/" + STARTER_SCRIPT_NAME, "w")
    starter_f.writelines(lines)
    starter_f.close()
    
    # Set permission on the starter script and
    # uninstall script
    os.popen("chmod u+x " + install_dir + "/" + STARTER_SCRIPT_NAME) 
    os.popen("chmod u+x " + install_dir + "/uninstall.sh")
    
    # Start the program
    os.popen(install_dir + "/" + STARTER_SCRIPT_NAME + ' > /dev/null 2> /dev/null&')
    output("Started!", silent)
        
    # Inform the user of what happened
    output("Seattle was successfully installed on your computer.", silent)
    output("If you would like to uninstall seattle at any time, run the uninstall.sh script located in this directory.", silent)


if __name__ == "__main__":
    main()
