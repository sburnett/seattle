"""
<Author>
  Cosmin Barsan
  
  Edited to add an optional argument to also copy the repy tests by 
  Brent Couvrette on November 13, 2008.

  Conrad Meyer, Thu Nov 26 2009: Move dynamic ports code from run_tests.py
  to preparetest.py.
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

  This file is also used directly by trunk/dist/make_base_installers.py. Also
  let Zack know if any adaptions are made to this file so the base installers
  can continue to be created correctly.  See ticket #501 about removing or
  adapting make_base_installer.py's dependence on this file.  (Zack 7/2/09)

"""

import sys
import glob
import os
import random
import shutil
import optparse
import subprocess

sys.path.insert(0, os.path.join(os.getcwd(), "repy", "tests"))
import testportfiller
sys.path = sys.path[1:]

# Whether to copy files that enable shims. In case of major bugs in shims,
# simply turn it off to revert back to the shim-less architecture. Added by
# Danny Yuxing Huang.
USE_SHIMS = False

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
def process_mix(script_path, verbose):
  mix_files = glob.glob("*.mix")
  error_list = []

  for file_path in mix_files:
    #generate a .py file for the .mix file specified by file_path
    processed_file_path = (os.path.basename(file_path)).replace(".mix",".py")
    (theout, theerr) =  exec_command(sys.executable+" " + script_path + " " + file_path + " " + processed_file_path)

    # If there was any problem processing the files, then notify the user.
    if theerr:
      print "Unable to process the file: " + file_path
      error_list.append((file_path, theerr))
      # If the verbose option is on then print the error.
      
  if verbose:
    print "\n" + '#'*50 + "\nPrinting all the exceptions (verbose option)\n" + '#'*50
    if len(error_list) == 0:
      print "NONE!!"
    for file_name, error in error_list:
      print "\n" + file_name + ":"
      print error
      print '-'*80


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


helpstring = """python preparetest.py [-t | -v] <foldername>"""

# Prints the given error message and the help string, then exits
def help_exit(errMsg, parser):
  print errMsg
  parser.print_help()
  sys.exit(1)

def main():
  repytest = False
  RANDOMPORTS = False
  verbose = False
	
  target_dir = None

  # Parse the options provided.
  parser = optparse.OptionParser()

  parser.add_option("-t", "--include-test-files", action="store_true",
                    dest="include_tests", help="Include the test " +
                    "files in the output directory.")
  parser.add_option("-v", "--verbose", action="store_true",
                    dest="verbose", help="Show more output on failure")
  parser.add_option("-r", "--randomports", action="store_true", 
                    dest="randomports", help="Fill in the ports randomly")

  (options, args) = parser.parse_args()

  # Set certain variables according to the options provided.
  if options.include_tests:
    repytest = True
  if options.randomports:
    RANDOMPORTS = True
  if options.verbose:
    verbose = True

  # Extract the target directory if available.
  if len(args) == 0:
    help_exit("Please pass the target directory as a parameter.", parser)
  else:
    target_dir = args[0]


  #store root directory
  current_dir = os.getcwd()

  # Make sure they gave us a valid directory
  if not( os.path.isdir(target_dir) ):
    help_exit("given foldername is not a directory", parser)

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
  shutil.copytree("seash/pyreadline/", target_dir + os.sep + 'pyreadline/')
  shutil.copytree("seash/modules/", target_dir + os.sep + 'modules/')
  copy_to_target("softwareupdater/*", target_dir)
  copy_to_target("autograder/nm_remote_api.mix", target_dir)
  copy_to_target("keydaemon/*", target_dir)
  # The license must be included in anything we distribute.
  copy_to_target("LICENSE.TXT", target_dir)

  if USE_SHIMS:
    # Copy over the files needed for using shim.
    copy_to_target("production_nat_new/src/*", target_dir)
    copy_to_target("production_nat_new/src/nmpatch/nmmain.py", target_dir)
    copy_to_target("production_nat_new/src/nmpatch/nminit.mix", target_dir)
    copy_to_target("production_nat_new/src/nmpatch/nmclient.repy", target_dir)
    copy_to_target("production_nat_new/src/nmpatch/nmclient_shims.mix", target_dir)
    copy_to_target("production_nat_new/src/nmpatch/sockettimeout.repy", target_dir)

  
  # Only copy the tests if they were requested.
  if repytest:
    # The test framework itself.
    copy_to_target("utf/*.py", target_dir)
    # The various tests.
    copy_to_target("repy/tests/*", target_dir)
    copy_to_target("nodemanager/tests/*", target_dir)
    copy_to_target("portability/tests/*", target_dir)  	
    copy_to_target("seash/tests/*", target_dir)
    copy_to_target("oddball/tests/*", target_dir)
    copy_to_target("seattlelib/tests/*", target_dir)
    copy_to_target("keydaemon/tests/*", target_dir)
    copy_to_target("utf/tests/*", target_dir)
    # jsamuel: This file, dist/update_crontab_entry.py, is directly included by
    # make_base_installers and appears to be a candidate for removal someday.
    # I assume zackrb needed this for installer testing.
    copy_to_target("dist/update_crontab_entry.py", target_dir)

    if USE_SHIMS:
      # Unit tests for shims
      copy_to_target("production_nat_new/src/unit_tests/*", target_dir)

  #set working directory to the test folder
  os.chdir(target_dir)


  # set up dynamic port information
  if RANDOMPORTS:
    print "\n[ Randomports option was chosen ]\n"+'-'*50
    portstouseasints = random.sample(range(52000, 53000), 3)
    portstouseasstr = []
    for portint in portstouseasints:
      portstouseasstr.append(str(portint))
    
    print "Randomly chosen ports: ",portstouseasstr
    testportfiller.replace_ports(portstouseasstr, portstouseasstr)

    # Replace the string <nodemanager_port> with a random port
    random_nodemanager_port = random.randint(53000, 54000)
    print "Chosen random nodemanager port: " + str(random_nodemanager_port)
    print '-'*50 + "\n"
    replace_string("<nodemanager_port>", str(random_nodemanager_port), "*nm*")
    replace_string("<nodemanager_port>", str(random_nodemanager_port), "*securitylayers*")
    
  else:
    # if this isn't specified, just use the default ports...
    testportfiller.replace_ports(['12345','12346','12347'], ['12345','12346','12347'])

    # Use default port 1224 for the nodemanager port if --random flag is not provided.
    replace_string("<nodemanager_port>", '1224', "*nm*")
    replace_string("<nodemanager_port>", '1224', "*securitylayers*")



  #call the process_mix function to process all mix files in the target directory
  process_mix("repypp.py", verbose)

  #go back to root project directory
  os.chdir(current_dir) 




def replace_string(old_string, new_string, file_name_pattern="*"):
  """
  <Purpose>
    Go through all the files in the current folder and replace
    every match of the old string in the file with the new
    string.

  <Arguments>
    old_string - The string we want to replace.
 
    new_string - The new string we want to replace the old string
      with.

    file_name_pattern - The pattern of the file name if you want
      to reduce the number of files we look at. By default the 
      function looks at all files.

  <Exceptions>
    None.

  <Side Effects>
    Many files may get modified.

  <Return>
    None
  """

  for testfile in glob.glob(file_name_pattern):
    # Read in the initial file.
    inFile = file(testfile, 'r')
    filestring = inFile.read()
    inFile.close()

    # Replace any form of the matched old string with
    # the new string.
    filestring = filestring.replace(old_string, new_string)

    # Write the file back.
    outFile = file(testfile, 'w')
    outFile.write(filestring)
    outFile.close()






if __name__ == '__main__':
  main()
