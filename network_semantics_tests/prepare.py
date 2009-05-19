"""
<Author>

  Adapted from trunk/preparetest  by Eric Kimbrel,  Striped away extra functionality so i could use this 
  code as a build script for network_semantics_testing, May 2009

<Start Date>
  October 3, 2008

<Description>
  This script has been adapted from the bash script preparetest.  The
  script first erases all the files in built folder, and then copies tests
  and resources to the built folder

<Usage>
  prepare.py 
  WARNING: Assumes that a test directory named mytest has been previously setup
           with the most recent updates.
           eg cd trunk
              python preparetest -t mytest/

           you can change the name from mytest by changing the constant below



"""

import sys
import glob
import os
import shutil
import subprocess

REPY_TEST_DIR = "mytest"

#define a function to use for copying the files matching the file expression to the target folder
#file_expr may contain wildcards
#target must specify an existing directory with no wildcards
def copy_to_target(file_expr, target,prefix=''):
  files_to_copy = glob.glob(file_expr)
  for file_path in files_to_copy:
    if os.path.isfile(file_path):
      shutil.copyfile(file_path,target +"/"+prefix+os.path.basename(file_path))




helpstring = """python preparetest.py [-t] <foldername>"""

# Prints the given error message and the help string, then exits
def help_exit(errMsg):
  print errMsg
  print helpstring
  sys.exit(1)



def main():
	
	
  #store root directory, set target directory to 'built'
  target_dir = 'built'
  current_dir = os.getcwd()

  # Make sure they gave us a valid directory
  if not os.path.isdir(target_dir):
    os.makedirs(target_dir)

  #set working directory to the test folder
  os.chdir(target_dir)	
  files_to_remove = glob.glob("*")

  #clean the test folder
  for f in files_to_remove: 
    if os.path.isdir(f):
      shutil.rmtree(f)		
    else:
      os.remove(f)

  #go back to root project directory
  os.chdir(current_dir) 

  #now we copy the necessary files to the test folder
  copy_to_target("tests/*/*", target_dir,prefix='test_')
  copy_to_target("resource/*", target_dir)
  copy_to_target("../repy/*", target_dir)
  copy_to_target("../"+REPY_TEST_DIR+"/repyportability.py",target_dir)
  copy_to_target("../"+REPY_TEST_DIR+"/persist.py",target_dir)
  copy_to_target("../"+REPY_TEST_DIR+"/servicelogger.py",target_dir)  

  # make the output directory
  os.chdir(target_dir) 
  os.makedirs('output')
  os.chdir(current_dir)



if __name__ == '__main__':
  main()
