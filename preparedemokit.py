"""
<Author>
  richard@jordan.ham-radio-op.net

<Start Date>
  Fri Mar  6 11:20:47 PST 2009

<Description>
  Adapted from preparetest.py.  Trying to build demokit.

<Usage>
  preparedemokit.py <target_folder>
"""
import sys
import glob
import os
import shutil
import subprocess
import preparetest

helpstring = """python preparedemokit.py <foldername>"""

# checks to make sure the argument list has at least 2 entries
def checkArgLen():
  if len(sys.argv) < 2:
    preparetest.help_exit('Invalid number of arguments')

def main():
  checkArgLen()
	
  #store root directory and get target directory
  target_dir = sys.argv[1]
  current_dir = os.getcwd()

  ####################
  # Setup
  ###################

  # Make sure they gave us a valid directory
  if (os.path.exists(target_dir)):  # don't overwrite
  #  help_exit("given foldername already exists")
    pass
  else: # create it
    os.mkdir(target_dir)

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
