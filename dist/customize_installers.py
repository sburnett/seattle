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

def main(which_os, dir_to_add, output_path):
    if not os.path.exists(dir_to_add):
        raise ArgError("Could not find directory to add: " + dir_to_add)
    elif not os.path.exists(output_path):
        raise ArgError("Could not find output directory: " + output_path)
    else:
        # Customizing the installer for each os is encapsulated
        # in a try-except block so that the others can continue
        # if one fails
        
        temp = otuput_path + "/tmp"
        created_temp = False
        if not os.path.exists(temp):
            os.mkdir(temp)
            created_temp = True
        
        # Move the added directory to a new temporary
        # directory so that it will be added to the
        # installers at the right location
        shutil.copytree(dir_to_add, temp + "/" + PROG_DIR)
        dir_to_add = temp + "/" + PROG_DIR
        created_installers = []

        if "w" in which_os:
            # Customize Windows installer
            output("Customizing Windows installer...")
            try:
                base_link = "custom_win_base"
                if not os.path.exists(BASE_INST_PATH + "" + base_link):
                    raise Exception("Base Windows installer not found.")
                inst_path = output_path + "/" + OUTPUT_NAME + "_win.zip"
                shutil.copyfile(BASE_INST_PATH + "/" + base_link, inst_path)
                os.system("zip -r " + inst_path + " " + dir_to_add)
                created_installers.append(inst_path)

            except Exception, e:
                output(e)
                output("Failed to customize Windows installer.")
            output("Done.")

        if "l" in which_os:
            # Customize Linux installer
            output("Customizing Linuz installer...")
            try:
                base_link = "custom_linux_base"
                if not os.path.exists(BASE_INST_PATH + "/" + base_link):
                    raise Exception("Base Linux installer not found.")
                inst_path = output_path + "/" + OUTPUT_NAME + "_linux.tgz"
                shutil.copyfile(BASE_INST_PATH + "/" + base_link, inst_path)
                os.system("gzip -d " + inst_path)
                unzipped_inst_path = output_path + "/" + OUTPUT_NAME + "_linux.tar"
                os.system("tar -rf " + unzipped_inst_path + " " + dir_to_add)
                os.system("gzip " + unzipped_inst_path)
                os.rename(output_path + "/" + OUTPUT_NAME + "_linux.tar.gz", inst_path)
                created_installers.append(inst_path)
            except Exception, e:
                output("Failed to customize Linux installer.")
                output(e)
            output("Done.")

        if "m" in which_os:
            # Customize Mac installer
            output("Customizing Mac installer...")
            try:
                base_link = "custom_mac_base"
                if not os.path.exists(BASE_INST_PATH + "/" + base_link):
                    raise Exception("Base Mac installer not found.")
                inst_path = output_path + "/" + OUTPUT_NAME + "_mac.tgz"
                shutil.copyfile(BASE_INST_PATH + "/" + base_link, inst_path)
                os.system("gzip -d " + inst_path)
                unzipped_inst_path = output_path + "/" + OUTPUT_NAME + "_mac.tar"
                os.system("tar -rf " + unzipped_inst_path + " " + dir_to_add)
                os.system("gzip " + unzipped_inst_path)
                os.rename(output_path + "/" + OUTPUT_NAME + "_mac.tar.gz", inst_path)
                created_installers.append(inst_path)
            except Exception, e:
                output("Failed to customize Mac installer.")
                output(e)
            output("Done.")
            
            if created_temp:
                # If we were the ones that created the temp file, delete it
                # when we finish
                os.system("rm -rf " + temp)

            output("customize_installers finished. Created these installers:")
            output("/n".join(created_installers))

if __name__ == "__main__":
    if len(sys.argv) < 4:
        output("usage: python [m|l|w] <directory/to/add> <output/directory>")
    else:
        main(sys.argv[1], sys.argv[2], sys.argv[3])
        
