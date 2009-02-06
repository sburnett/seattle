"""
<Author>
  Cosmin Barsan
  Edited to add an optional argument to also copy the repy tests by 
  Brent Couvrette on November 13, 2008.
<Start Date>
  October 3, 2008

<Description>
  This script has been adapted from the bash script preparetest.  The
  script first erases all the files in the target folder, then copies
  the necessary test files to it. Afterwards, the .mix files in the
  target folder are run through the preprocessor.  It is required that
  the folder passed in as an argument to the script exists.

<Usage>
  preparetest.py <target_folder> <-t>

  if -t is specified, the repy tests will also be included, otherwise, they will not

<Notes>
  This file is used as a library by trunk/www/deploy_state_transitions.py
  If you make ANY changes to this file please let Ivan know so that the
  other script can continue to function correctly. Thanks. (IB 01/19/09)

"""

import sys
import glob
import os
import shutil
import subprocess


#define a function to use for copying the files matching the file expression to the target folder
#file_expr may contain wildcards
#target must specify an existing directory with no wildcards
def copy_to_target(file_expr, target):
  files_to_copy = glob.glob(file_expr)
  for file_path in files_to_copy:
    if os.path.isfile(file_path):
      shutil.copyfile(file_path,target +"/"+os.path.basename(file_path))


#iterate through the .mix files in current folder and run them through the preprocessor
#script_path must specify the name of the preprocessor script
#the working directory must be set to the directory containing the preprocessor script prior to executing this function.
def process_mix(script_path):
  mix_files = glob.glob("*.mix")
 
  for file_path in mix_files:
    #generate a .py file for the .mix file specified by file_path
    processed_file_path = (os.path.basename(file_path)).replace(".mix",".py")
    (theout, theerr) =  exec_command("python " + script_path + " " + file_path + " " + processed_file_path)


def exec_command(command):
# Windows does not like close_fds and we shouldn't need it so...
  p =  subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  # get the output and close
  theout = p.stdout.read()
  p.stdout.close()

  # get the errput and close
  theerr = p.stderr.read()
  p.stderr.close()

  # FreeBSD prints on stdout, when it gets a signal...
  # I want to look at the last line.   it ends in \n, so I use index -2
  if len(theout.split('\n')) > 1 and theout.split('\n')[-2].strip() == 'Terminated':
    # lose the last line
    theout = '\n'.join(theout.split('\n')[:-2])
    
    # however we threw away an extra '\n' if anything remains, let's replace it
    if theout != '':
      theout = theout + '\n'

  # everyone but FreeBSD uses stderr
  if theerr.strip() == 'Terminated':
    theerr = ''

  # Windows isn't fond of this either...
  # clean up after the child
#  os.waitpid(p.pid,0)

  return (theout, theerr)


helpstring = """python preparetest.py [-t] <foldername>"""

# Prints the given error message and the help string, then exits
def help_exit(errMsg):
  print errMsg
  print helpstring
  sys.exit(1)

# checks to make sure the argument list has at least 2 entries
def checkArgLen():
  if len(sys.argv) < 2:
    help_exit('Invalid number of arguments')

def main():
  checkArgLen()
	
  repytest = False
	
  # -t means we will copy repy tests
  if sys.argv[1] == '-t':
    repytest = True
    sys.argv = sys.argv[1:]
    checkArgLen()

  #store root directory and get target directory
  target_dir = sys.argv[1]
  current_dir = os.getcwd()

  # Make sure they gave us a valid directory
  if not( os.path.isdir(target_dir) ):
    help_exit("given foldername is not a directory")

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
  copy_to_target("repy/*", target_dir)
  copy_to_target("nodemanager/*", target_dir)
  copy_to_target("portability/*", target_dir)
  copy_to_target("seattlelib/*", target_dir)
  copy_to_target("seash/*", target_dir)
  copy_to_target("softwareupdater/*", target_dir)
  
  if repytest:
    # Only copy the tests if they were requested.
    copy_to_target("repy/tests/*", target_dir)
    copy_to_target("nodemanager/tests/*", target_dir)
    copy_to_target("portability/tests/*", target_dir)
    copy_to_target("seash/tests/*", target_dir)


  #set working directory to the test folder
  os.chdir(target_dir)

  #call the process_mix function to process all mix files in the target directory
  process_mix("repypp.py")

  #go back to root project directory
  os.chdir(current_dir) 


if __name__ == '__main__':
  main()
