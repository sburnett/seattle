import re
import os
import seattlestopper
import tempfile

STARTER_SCRIPT_NAME = "start_seattle.sh"

def output(text):
    print text

def main():
    # Kill seattle
    seattlestopper.killall()
    crontab_f = os.popen("crontab -l")
    # Used module tempfile as suggested in Jacob Appelbaum's patch
    fd, s_tmp = tempfile.mkstemp("temp", "seattle")
    found = False
    for line in crontab_f:
        if not re.search("/" + STARTER_SCRIPT_NAME, line):
            os.write(fd, line)
        else:
            found = True
    if found:
        os.close(fd)
        os.popen('crontab "' + s_tmp + '"')
        output("Seattle has been uninstalled.")
        output("If you wish, you may now delete this directory.")
    else:
        os.close(fd)
        output("Could not detect a seattle installation on your computer.")
    os.unlink(s_tmp)

if __name__ == "__main__":
    main()
