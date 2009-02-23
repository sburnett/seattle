"""
<Program Name>
  deploy_geni_control

<Started>
  February 5, 2008

<Author>
  Alper Sarikaya
  alpers@cs.washington.edu

<Purpose>
  Deploys the django control scripts along with all the necessary
  repy libs into a single directory. Uses preparetest.py internally
  and has similar behavior.

<Description>
  The script first erases all the files in the target folder, then
  copies the necessary test files to it. Afterwards, the .mix files in
  the target folder are run through the preprocessor.  It is required
  that the folder passed in as an argument to the script exists.

<Usage>
  export PYTHONPATH=$PYTHONPATH:/loc/of/svn_trunk && 
  deploy_geni_control.py <target_folder_to_build GENI> <svn_trunk>
  
"""

import os
import sys
import shutil

import preparetest

def main():
    
    if not len(sys.argv) == 3:
        print "python deploy_geni_control <geni_root> <svn_root>"
        return
    
    geni_root = sys.argv[1]
    svn_trunk = sys.argv[2]
    
    # check for existence of svn trunk
    if not os.path.isdir(svn_trunk):
        print "ERROR: the path to the SVN root given does not exist."
        return

    # warn the user if we're about to overwrite files
    if os.path.isdir(geni_root):
        ans = raw_input("WARNING: directory found at geni_root location.  Delete? [y/n]")
        ans = str.lower(ans)
        if not ans == 'y':
            exit()
        else:
            shutil.rmtree(geni_root)

    # copy over most recent build of geni from SVN to specified directory
    if not svn_trunk.endswith("/"):
        svn_trunk += "/"
    geni_svn = svn_trunk + "www/geni/"

    print "copied"
    shutil.copytree(geni_svn, geni_root)

    # alpers - moves dir to actual repy dir
    if not geni_root.endswith("/"):
        geni_root += "/"
    geni_repy = geni_root + "control/repy_dist"

    # make the repy directory if it doesn't exist
    if not os.path.isdir(geni_repy):
        os.mkdir(geni_repy)

    # need to modify argument so preparetest can pick it up
    sys.argv[1] = geni_repy

    # this is for preparetest to work
    current_dir = os.getcwd()

    # makes this a full path, otherwise preparetest doesn't like it
    if not os.path.isabs(sys.argv[1]):
        sys.argv[1] = os.path.abspath(sys.argv[1])

    os.chdir(svn_trunk)
    target_dir = sys.argv[1]
    print sys.argv[1]
    preparetest.main()

    
    # set working directory back to the folder we've started in
    os.chdir(current_dir)
    
    # alpers - I don't think this is necessary since all dependencies are
    # using the fully qualified name

    # copy files to target dir (this is supposed to be geni/control)
    preparetest.copy_to_target(target_dir + "/../*.mix", target_dir)
    
    # set working dir to target
    os.chdir(target_dir)
  
    # call the process_mix function to process all mix files in the target directory
    preparetest.process_mix("repypp.py")
    
    # go back to root project directory
    os.chdir(current_dir) 

if __name__ == '__main__':
    main()
