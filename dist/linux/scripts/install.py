import os
import re
import sys

STARTER_SCRIPT_NAME = "start_seattle.sh"

class InstallFailed(Exception):
    def __init__(self, value=""):
        self.value = value
    
    def __str__(self):
        return repr(self.value)

# In case we want to silence or redirect output
# at some point, for internal use only
def output(text):
    print text

# If being run by itself, catch the exception and print output when
# the installation fails.
def main():
    try:
        install()
    except(InstallFailed):
        output "Installation failed."

def install():
    """
    <Purpose>
      Installs seattle on the computer by changing values in program 
      scripts and adding the starter scripts to the crontab. Must be 
      run from inside the root installation directory, where it is 
      originally located in the installer.
    
    <Arguments>
      None.

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
        output("Sorry, we don't support your version of Python (Python " + ".".join(version) + ").")
        output("Please install Python 2.5 and try again.")
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
        output("Seattle is already installed on your computer.")
        raise InstallFailed("Seattle already installed")
        
    # Now we know they don't, so we should add it
    output("Adding to startup...")
    # First, generate a temp file with the user's crontab plus
    # our task
    cron_line = '*/10 * * * * "' + os.getcwd() + '/' + STARTER_SCRIPT_NAME + '" &> "' + os.getcwd() + '/cron_log.txt"' +  os.linesep
    crontab_f = os.popen("crontab -l")
    temp_f = open("temp.txt", "w")
    for line in crontab_f:
        temp_f.write(line)
    temp_f.write(cron_line)
    temp_f.close()
    # Then, replace the crontab with that file
    os.popen('crontab "' + os.getcwd() + '/temp.txt"')
    output("Done.")
    
    # Next, run the script to generate the node's keys
    output("Generating identity key (may take a few minutes)...")
    os.popen("python createnodekeys.py > /dev/null")
    output("Done.")

    # Then, setup the starter script with the name of the installation
    # directory
    output("Starting seattle...")
    starter_f = open(STARTER_SCRIPT_NAME, "r")
    lines = []
    for line in starter_f:
        lines.append(re.sub("%PROG_PATH%", os.getcwd(), line))
    starter_f.close()
    starter_f = open(STARTER_SCRIPT_NAME, "w")
    starter_f.writelines(lines)
    starter_f.close()
    
    # Set permission on the starter script and
    # uninstall script
    os.popen("chmod u+x " + STARTER_SCRIPT_NAME) 
    os.popen("chmod u+x uninstall.sh")
    
    # Start the program
    os.popen("./" + STARTER_SCRIPT_NAME + ' "$PWD"&')
    output("Started!")
        
    # Inform the user of what happened
    output("Seattle was successfully installed on your computer.")
    output("If you would like to uninstall seattle at any time, run the uninstall.sh script located in this directory.")

if __name__ == "__main__":
    main()
