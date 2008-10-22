import os
import sys
import shutil

PROG_DIR = "seattle_repy"

def output(text):
    print text

def main(custom_dir, base_name, inst_name):
    if not os.path.exists(custom_dir):
        output("Could not find directory: " + custom_dir)
    else:
        shutil.copyfile("win" + os.sep + base_name + "_win.zip", inst_name + "_win.zip")
        shutil.copyfile("linux" + os.sep + base_name + "_linux.tgz", inst_name + "_linux.tgz")
                
        if os.path.exists(PROG_DIR):
            shutil.rmtree(PROG_DIR)
        
        # Update dinwos zip file
        shutil.copytree(custom_dir, PROG_DIR)
        os.system("zip -r " + inst_name + "_win.zip " + PROG_DIR)
        shutil.rmtree(PROG_DIR)

        # Update linux tar file
        os.system("tar -xzf " + inst_name + "_linux.tgz")
        os.system("cp -r " + custom_dir + os.sep + "* " + PROG_DIR)
        os.system("tar -czf " + inst_name + "_linux.tgz " + PROG_DIR)
        shutil.rmtree(PROG_DIR)
        
        # For now, just copy the linux file over for the mac one
        shutil.copyfile(inst_name + "_linux.tgz", inst_name + "_mac.tgz")

        output("Done! Files created:")
        output("\n".join([inst_name + "_win.zip", inst_name + "_linux.tgz", inst_name + "_mac.tgz"]))

if __name__ == "__main__":
    if len(sys.argv) < 4:
        output("usage: python customize_installers.py directory/to/add base_installer_name name_of_customized_installer")
    else:
        main(sys.argv[1], sys.argv[2], sys.argv[3])
        
