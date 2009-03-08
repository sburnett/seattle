"""
<Program Name>
  deploy_geni

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
  deploy_geni.py <target_folder_to_build GENI> <svn_trunk>
  
"""

import os
import sys
import shutil

try:
  import preparetest
except ImportError:
  print "Error importing preparetest, make sure that it is in your PYTHONPATH"
  print "\te.x.: export PYTHONPATH=$PYTHONPATH:/loc/of/svn_trunk"
  sys.exit(0)

def main():
    
    if not len(sys.argv) == 3 and not len(sys.argv) == 4:
        print "python deploy_geni [-t] <loc/of/geni_root> <loc/of/svn_trunk>"
        return
    
    start_arg = 1
    do_tests = False
    if sys.argv[1] == '-t':
        do_tests = True
        start_arg = start_arg + 1

    geni_root = sys.argv[start_arg]
    svn_trunk = sys.argv[start_arg + 1]
    
    # check for existence of svn trunk
    if not os.path.isdir(svn_trunk):
        print "ERROR: the path to the SVN root given does not exist."
        return

    if not svn_trunk.endswith("/"):
        svn_trunk += "/"

    # make sure this is the svn trunk
    if not os.path.exists(svn_trunk + "www"):
        print svn_trunk + "www"
        print "ERROR: the given SVN doesn't look like SVN (/loc/of/trunk/www missing)"
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
    geni_svn = svn_trunk + "www/geni/"
    shutil.copytree(geni_svn, geni_root, symlinks=True)
    print "copied successfully (symlinks intact)"

    # alpers - moves dir to actual repy dir
    if not geni_root.endswith("/"):
        geni_root += "/"
    geni_repy = geni_root + "control/repy_dist"

    # make the repy_dist directory if it doesn't exist
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
    # this is node_state_transitions/changeusers.mix
    changeusers_path = os.path.abspath(svn_trunk) + "/www/node_state_transitions/changeusers.mix"
    print "changeusers_path:", changeusers_path
    preparetest.copy_to_target(changeusers_path, target_dir)
    
    # if do_tests is true, let's copy over tests too..
    if do_tests:
        preparetest.copy_to_target(target_dir + "/../tests/*.mix", target_dir)

    # set working dir to target
    os.chdir(target_dir)
  
    # call the process_mix function to process all mix files in the target directory
    preparetest.process_mix("repypp.py")

    # touch __init__.py
    open("__init__.py", "w").close()

    # go back to root project directory
    os.chdir(current_dir) 

if __name__ == '__main__':
    main()
