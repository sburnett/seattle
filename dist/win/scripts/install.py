import os
import platform
import subprocess

STARTER_SCRIPT_NAME = "start_seattle.bat"


def output(text):
    print text

def get_startup_folder(version):
    # Returns the startup folder if it can be found,
    # takes version either "XP" or "Vista"
    try:
        # See if the installer executable found the startup folder
        # in the registry
        startup_file = open("startup.dat")
        startup_path = ""
        for line in startup_file:
            if line:
                startup_path = line
        if startup_path and os.path.exists(startup_path):
            return startup_path
        else:
            raise Exception
    except:
        # If that fails, look in a couple obvious places, based on OS version
        if version == "Vista":
            # Look in probable Vista places
            startup_path = os.environ.get("HOMEDRIVE") + os.environ.get("HOMEPATH") + "\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup"
            if os.path.exists(startup_path):
                return startup_path
        elif version == "XP":
            # Look in probable XP places
            startup_path = os.environ.get("HOMEDRIVE") + os.environ.get("HOMEPATH") + "\\Start Menu\\Programs\\Startup"
            if os.path.exists(startup_path):
                return startup_path
        return ""


def main():
    global STARTER_SCRIPT_NAME
    added_to_startup = 0
    prog_path = os.getcwd()
    output("Checking OS...")
    if platform.system() != "Windows":
        # If it's not Windows, this isn't the right installer
        output("This installer is designed for use on Windows XP or Vista only.")
        output("Please download the correct installer for your operating system and try again.")
    else:
        if not (platform.release() == "Vista" or platform.release() == "XP"):
            # If it's not XP or Vista, display error and fail
            output("Unsupported Windows Version: " + platform.system + " " + platform.release)
        else:
            # Correct version of Windows, go ahead with the install
            output("Done.")
            output("Locating startup folder...")
            startup = get_startup_folder(platform.release())
            if (startup):
                # If we did find the location of the startup folder
                output("Done.")
                added_to_startup = 1
                if os.path.exists(startup + "\\" + STARTER_SCRIPT_NAME):
                    # If the starter script is already in the User's startup folder, assume that
                    # it is already installed and quit
                    output("Seattle is already installed on this computer.")
                else:
                    # Assume seattle is not installed, and move ahead
                    # Generate a script to run from the startup folder
                    output("Generating startup script...")
                    starter_script_f = open(startup + "\\" + STARTER_SCRIPT_NAME, "w")
                    script_lines = []
                    script_lines.append("@echo off\n")
                    script_lines.append("if not exist \""  + prog_path + "\\softwareupdater.py\" goto SeattleGone\n")
                    script_lines.append("start /min \"" + prog_path + "\\pythonw.exe\" \"" + prog_path + "\\softwareupdater.py\"\n")
                    script_lines.append("start /min \"" + prog_path + "\\pythonw.exe\" \"" + prog_path + "\\nmmain.py\"\n")
                    script_lines.append("goto End\n")
                    script_lines.append(":SeattleGone\n")
                    script_lines.append("if exist \"%0.bat\" del \"%0.bat\"\n")
                    script_lines.append("if exist \"%0\" del \"%0\"\n")
                    script_lines.append(":End\n")
                    script_lines.append("exit\n")
                    starter_script_f.writelines(script_lines)
                    starter_script_f.close()
                    output("Done.")
                    
                    # Generate an uninstaller, which will just delete the startup script
                    output("Generating uninstaller script...")
                    uninstaller_f = open("uninstall.bat", "w")
                    script_lines = []
                    script_lines.append("@echo off\n")
                    script_lines.append('python "' + os.getcwd() + '\\uninstall.py" "' + startup + '" "' + STARTER_SCRIPT_NAME + '"\n')
                    uninstaller_f.writelines(script_lines)
                    uninstaller_f.close()
                    output("Done.")

                    post_startup_steps(prog_path, added_to_startup)
                    
            else:
                # We couldn't find the startup folder, note that we couldn't,
                # but move on with the install
                # TODO: It should be relatively simple to allow the user to
                # manually enter the location of their startup file, if they
                # so desire
                output("Failed.")
                added_to_startup = 0
                post_startup_steps(prog_path, added_to_startup)

def post_startup_steps(prog_path, added_to_startup):
    # Next, generate keys for the node by calling the appropriate script
    output("Generating identity key (may take a few minutes)...")
    subprocess.call(["pythonw.exe", "createnodekeys.py"])
    output("Done.")
    # Finally, call the script that starts the node manager and software
    # updater
    os.system("start /min start_seattle.bat")
    if added_to_startup == 1:
        # If everything went smoothly, display basic success messages
        output("Seattle was successfully installed on your computer.")
        output("If you would like to uninstall Seattle at any time, run the uninstall.bat script located in this directory.")
    else:
        # If we weren't able to locate the startup folder, inform the user
        # about this, and give some alternative instructions
        output("We were unable to find the startup folder on your computer.")
        output("Seattle has been started, but it will not automatically run when you start your computer.")
        output("You can manually start it at any time, just run the start_seattle.bat script in this directory.")
        output("This will only start Seattle if it is not already running, so you don't have to worry about multiple instances taking up too much memory.")
      
if __name__ == "__main__":
    main()
