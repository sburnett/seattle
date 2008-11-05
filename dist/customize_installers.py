import os
import sys
import shutil

PROG_DIR = "seattle_repy"
BASE_INST_PATH = "/var/www/dist"
OUTPUT_NAME = "seattle"

class ArgError(Exception):
    def __init__(self, value):
        self.parameter = value
    def __str__(self):
        return repr(self.parameter)

def output(text):
    print text
    #f = open("/tmp/out", "a")
    #f.write(text)
    #f.close()

def main(which_os, dir_to_add, output_path):
    global PROG_DIR

    if not os.path.exists(dir_to_add):
        raise ArgError("Could not find directory to add: " + dir_to_add)
    elif not os.path.exists(output_path):
        raise ArgError("Could not find output directory: " + output_path)
    else:
        # Customizing the installer for each os is encapsulated
        # in a try-except block so that the others can continue
        # if one fails

        if dir_to_add[0] != "/":
            dir_to_add = os.getcwd() + "/" + dir_to_add
        
        if output_path[0] != "/":
            output_path = os.getcwd() + "/" + output_path
        
        oldpwd = os.getcwd()
        temp = output_path + "/tmp"
        created_temp = False
        if not os.path.exists(temp):
            os.mkdir(temp)
            created_temp = True

        os.chdir(temp)
        if os.path.exists(PROG_DIR):
            shutil.rmtree(PROG_DIR)

        # Move the added directory to a new temporary
        # directory so that it will be added to the
        # installers at the right location
        # os.system("echo 'DIR_TO_ADD: ' && ls %s"%(dir_to_add))
        shutil.copytree(dir_to_add, PROG_DIR)
        dir_to_add = PROG_DIR
        created_installers = []

        for letter in which_os:

            if letter == "w":
                # Customize Windows installer
                output("Customizing Windows installer...")
                try:
                    base_link = "custom_win_base"
                    if not os.path.exists(BASE_INST_PATH + "/" + base_link):
                        raise Exception("Base Windows installer not found.")
                    inst_path = output_path + "/" + OUTPUT_NAME + "_win.zip"
                    shutil.copyfile(BASE_INST_PATH + "/" + base_link, inst_path)
                    os.system("zip -r " + inst_path + " " + dir_to_add)
                    created_installers.append(inst_path)

                except Exception, e:
                    output(e)
                    output("Failed to customize Windows installer.")
                output("Done.")

            if letter in "ml":
                # Customize Mac/Linux installer
                if letter == "m":
                    base_link = "custom_mac_base"
                    os_type = "mac"
                else:
                    base_link = "custom_linux_base"
                    os_type = "linux"
                
                output("Customizing %s installer..."%(os_type))
                try:
                    if not os.path.exists(BASE_INST_PATH + "/" + base_link):
                        raise Exception("Base %s installer not found."%(os_type))
                    inst_path = output_path + "/" + OUTPUT_NAME + "_%s.tgz"%(os_type)
                    shutil.copyfile(BASE_INST_PATH + "/" + base_link, inst_path)
                    os.system("gzip -d " + inst_path)
                    unzipped_inst_path = output_path + "/" + OUTPUT_NAME + "_%s.tar"%(os_type)
                    
                    os.system("tar -rf " + unzipped_inst_path + " " + dir_to_add)
                    os.system("gzip " + unzipped_inst_path)

                    os.rename(output_path + "/" + OUTPUT_NAME + "_%s.tar.gz"%(os_type), inst_path)
                    created_installers.append(inst_path)
                except Exception, e:
                    output("Failed to customize %s installer:"%(os_type))
                    output(e)
                output("Done.")
            
                os.chdir(oldpwd)
                if created_temp:
                    # If we were the ones that created the temp file, delete it
                    # when we finish

                    # os.system("rm -rf " + temp)
                    pass

        output("customize_installers finished. Created these installers:")
        output("/n".join(created_installers))

if __name__ == "__main__":
    if len(sys.argv) < 4:
        output("usage: python [m|l|w] <directory/to/add> <output/directory>")
    else:
        main(sys.argv[1], sys.argv[2], sys.argv[3])
        
