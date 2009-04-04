"""
<Author>
  richard@jordan.ham-radio-op.net

<Start Date>
  Fri Mar  6 11:20:47 PST 2009

<Description>
  Adapted from preparetest.py.  Trying to build demokit.

<Usage>
  python preparedemokit.py

<Side Effects> 
  Creates a directory called "demokit".  If "demokit" exists,
  overwrites it.
""" 

import sys 
import glob 
import os 
import shutil 
import subprocess 
import preparetest

def main():
  #store root directory and get target directory
  target_dir = "demokit"
  current_dir = os.getcwd()

  ####################
  # Setup
  ###################

  # Make sure they gave us a valid directory
  if (os.path.exists(target_dir)):  # remove it
    if os.path.isdir(target_dir):
      shutil.rmtree(target_dir)		
    else:
      os.remove(target_dir)    

  # recreate it
  os.mkdir(target_dir)

  ####################
  # Build Repy
  ####################

  # core
  preparetest.copy_to_target("nodemanager/servicelogger.mix", target_dir)
  preparetest.copy_to_target("repy/*.py", target_dir)
  preparetest.copy_to_target("seattlelib/*.repy", target_dir)
  preparetest.copy_to_target("portability/*.py", target_dir)
  preparetest.copy_to_target("nodemanager/advertise.mix", target_dir)
  preparetest.copy_to_target("nodemanager/persist.py", target_dir)
  preparetest.copy_to_target("nodemanager/timeout_xmlrpclib.py", target_dir)
  preparetest.copy_to_target("nodemanager/openDHTadvertise.py", target_dir)

  # utils
  preparetest.copy_to_target("seattlelib/repypp.py", target_dir)
  preparetest.copy_to_target("seash/seash.mix", target_dir)

  # extras
  preparetest.copy_to_target("repy/apps/allpairsping/allpairsping.repy", target_dir)
  preparetest.copy_to_target("repy/apps/old_demokit/*", target_dir)

  #set working directory to the test folder
  os.chdir(target_dir)

  #call the process_mix function to process all mix files in the target directory
  preparetest.process_mix("repypp.py")

  # rm mix src files
  files_to_remove = glob.glob("*.mix")
  for fn in files_to_remove: 
    os.remove(fn)

  #go back to root project directory
  os.chdir(current_dir) 

if __name__ == '__main__':
  main()
