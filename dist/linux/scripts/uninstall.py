import re
import os

STARTER_SCRIPT_NAME = "start_seattle.sh"

def output(text):
    print text

def main():
    crontab_f = os.popen("crontab -l")
    temp_f = open("temp.txt", "w")
    found = False
    for line in crontab_f:
        if not re.search("/" + STARTER_SCRIPT_NAME, line):
            temp_f.write(line)
        else:
            found = True
    if found:
        crontab_f.close()
        os.popen('crontab "' + os.getcwd() + '/temp.txt"') 
        
        
        output("Seattle has been uninstalled.")
        output("If you wish, you may now delete this directory.")
    else:
        output("Could not detect a seattle installation on your computer.")
    
    os.popen("rm -f temp.txt")

if __name__ == "__main__":
    main()
