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
  deploy_geni_control.py <target_folder>
  
"""

import os
import sys

import preparetest

def main():
    
    if not len(sys.argv) == 3:
        print "python deploy_geni_control <geni_root> <svn_root>"
        return
    
    if not os.path.isdir(sys.argv[1]) or \
       not os.path.isdir(sys.argv[2]):
        print "ERROR: one (or both) of the paths given do not exist."
        return

    # alpers - moves dir to actual repy dir
    if not sys.argv[1][-1] == "/":
        sys.argv[1] += "/"
    sys.argv[1] += "geni/control/repy_dist"


    # this is for preparetest to work
    current_dir = os.getcwd()

    # makes this a full path, otherwise preparetest doesn't like it
    if not sys.argv[1][0] == "/":
        sys.argv[1] = current_dir + "/" + sys.argv[1]

    os.chdir(sys.argv[2])
    target_dir = sys.argv[1]
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
