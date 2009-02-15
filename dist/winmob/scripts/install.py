"""
<Program Name>
  install.py

<Date Started>
  January 27, 2009

<Author>
  Carter Butaud

<Purpose>
  Installs seattle on a Windows Mobile device.
"""

import os
import platform
import sys
sys.path.append(os.getcwd())
import windows_api
import nonportable


STARTER_SCRIPT_NAME = "start_seattle.py"


def output(text):
    print text


def get_startup_folder(version):
    # Returns the startup folder if it can be found,
    # takes version either "XP" or "Vista"
    try:
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
            # Try locating the startup folder by looking at the registry key
            key_handle = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Shell Folders")
            (startup_path, data_type) = _winreg.QueryValueEx(key_handle, "Startup")
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
        elif version == "WindowsCE":
            # Look in probable Mobile places
            startup_path = "\\Windows\\Startup"
            if os.path.exists(startup_path):
                return startup_path
            startup_path = "\\Windows\\StartUp"
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
        if not (nonportable.ostype == "WindowsCE"):
            # If it's not Windows Mobile, display error and fail
            output("Unsupported Windows Version: " + platform.system() + " " + platform.release())
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
                    
                    # First, create the sitecustomize file
                    ouput("Configuring python...")
                    script_lines = []
                    script_lines.append("import sys\n")
                    script_lines.append("sys.path.append(\"" + prog_path + "\")\n")
                    sitecust_f = open(PYTHON_PATH + "\\sitecustomize.py")
                    sitecust_f.writelines(script_lines)
                    sitecust_f.close()
                    output("Done.")

                    # Generate a script to run from the startup folder
                    output("Generating startup script...")
                    script_lines = []
                    script_lines.append("import windows_api\n")
                    script_lines.append("\n")
                    script_lines.append("SEATTLE_DIR = r\"" + prog_path + "\"\n")
                    script_lines.append("\n")
                    script_lines.append("def main():\n")
                    script_lines.append("  windows_api.launchPythonScript(INSTALL_DIR + \"\\start_seattle.py\")\n")
                    script_lines.append("\n")
                    script_lines.append("if __name__ == \"__main__\":\n")
                    script_lines.append("  main()\n")
                    starter_f = open(startup + "\\" + STARTER_SCRIPT_NAME, "w")
                    starter_f.writelines(script_lines)
                    starter_f.close()
                    output("Done.")
                    
                                        
                    # Generate an uninstaller, which will just delete the startup script
                    output("Generating uninstaller script...")
                    uninstaller_f = open("uninstall.py", "w")
                    script_lines = []
                    script_lines.append("import os\n")
                    script_lines.append("\n")
                    script_lines.append("STARTER_SCRIPT = r\"" + startup + "\\" + STARTER_SCRIPT_NAME + "\"\n")
                    script_lines.append("\n")
                    script_lines.append("def main():\n")
                    script_lines.append("  os.remove(STARTER_SCRIPT)\n")
                    script_lines.append("  print \"seattle has been uninstalled. You may now remove the installation " + 
                                        "files from your computer, if you wish.\"\n")
                    script_lines.append("\n")
                    script_lines.append("if __name__ == \"__main__\":\n")
                    script_lines.append("  main()\n")
                    uninstaller_f.writelines(script_lines)
                    uninstaller_f.close()
                    output("Done.")



                    post_startup_steps(prog_path, added_to_startup)
                    
            else:
                # We couldn't find the startup folder, note that we couldn't,
                # but move on with the install
                # TODO: It should be relatively simple to allow the user to
                # manually enter the location of their startup folder, if they
                # so desire
                output("Failed.")
                added_to_startup = 0
                post_startup_steps(prog_path, added_to_startup)

def post_startup_steps(prog_path, added_to_startup):
    # Next, generate keys for the node by calling the appropriate script
    output("Generating identity key (may take a few minutes)...")
    windows_api.launchPythonScript("createnodekeys.py")
    output("Done.")

    # Set the program's path in repyconstants.py
    const_f = open(prog_path + "/repy_constants.py")
    lines = []
    for line in const_f:
        to_append = line
        if line.startswith("PATH_SEATTLE_INSTALL"):
            to_append = 'PATH_SEATTLE_INSTALL = "' + prog_path + '"\n'
        lines.append(to_append)
    const_f.close()
    const_f = open(prog_path + "/repy_constants.py", "w")
    const_f.writelines(lines)
    const_f.close()


    # Finally, call the script that starts the node manager and software
    # updater
    windows_api.launchPythonScript("start_seattle.py")
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
