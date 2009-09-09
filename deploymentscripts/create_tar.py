"""
<Program Name>
  create_tar.py

<Started>
  May 2009

<Author>
  n2k8000@u.washington.edu
  Konstantin Pik

<Purpose>
  Builds up a .tar file with the files specified in the files
  string. This is hardcoded for now as the files shouldn't change
  and if they do it will be easier to add them to this script (separated
  by spaces).

  Function creates a file named deploy.tar. 
  TODO: Specify outfilename as a parameter. 

<Usage>
  Currently only takes one extra fn for simplicity & testing
  ./create_tar.py [extra_fn1 extra_fn2 extra_fnN]
"""

import os
import sys
import subprocess



def shellexec(cmd_str):
  """
  <Purpose>
    Uses subprocess to execute the command string in the shell.
     
  <Arguments>
    cmd_str:  The string to be treated as a command (or set of commands,
                separated by ;).
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    A tuple containing (stdout, strerr, returncode)

    Detailed:
    stdout: stdout printed to console during command execution.
    strerr: error (note: some programs print to strerr instead of stdout)
    returncode: the return code of our call. If there are multiple commands, 
                then this is the return code of the last command executed.
  """

  # get a handle to the subprocess we're creating..
  handle = subprocess.Popen(cmd_str, shell=True, 
      stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  # execute and grab the stdout and err
  stdoutdata, strerrdata = handle.communicate("")

  # The return code...  
  returncode = handle.returncode
  
  return stdoutdata, strerrdata, returncode

  
  
# TODO: add args as 'extra' script files to execute.
def main():
  """
  <Purpose>
    Main entyr point into the program. Checks that everytyhing is in order, 
    and then creates the tar file to deploy.
     
  <Arguments>
    None.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """

  print "Starting tar-maker script.."
  # String of files we're going to be looking for
  files="runlocaltests.py testprocess.py verifyfiles.mix cleanup_deploy.py hashes.dict upgrade_nodes.sh deploy_helper.py"

  # TODO: add list of 'optional files' to include

  # get the files passed in as arguments
  files_from_args = ''
  # 1 skips this file name
  print
  
  for eachfile in range(1, len(sys.argv)):
    print "Adding custom file: "+sys.argv[eachfile]
    files_from_args+=' '+sys.argv[eachfile]
  print
  # mash the two strings together now
  files+=files_from_args

  # Total number of files split by spaces
  total_files=len(files.split(' '))

  # Counter for found files
  num_files_found=0

  # Temporary tar, incrementally we'll build it up
  # Will remove the temp files (since I use -update flag)
  # for building up the .tar
  if os.path.isfile('./deploy.tar.temp'):
    os.remove('./deploy.tar.temp')


  for filename in files.split(' '):
    print ' Looking for '+filename+' in '+os.getcwd()
    if os.path.isfile('./'+filename):
      print '  File found!'
      num_files_found += 1
      shellexec('tar -rf deploy.tar.temp '+filename)
    else:
      print '  WARNING: '+filename+' NOT FOUND'

  print
  print "Found "+str(num_files_found)+" of "+str(total_files)+" necessary files."
  print

  # Did we find all of the files?
  if num_files_found == total_files:
    print
    print 'All files found, finishing tar..'
    # rename the file to the final name.
    # this will over-write current deploy.tar in the dir if one exists  
    shellexec('mv deploy.tar.temp deploy.tar')
    return 0
  else:
    print 'FATAL ERROR: Not all the files where found, please check that '
    print '            this script is in the same directory as the files. '
    print
    print "Cleaning up temp files..."
    
    # remove deploy.tar.temp only if it exists.
    if os.path.isfile('./deploy.tar.temp'):
      os.remove('./deploy.tar.temp')
    
    print
    print 'Finished (with errors)'
    return 1

    
    
if __name__ == "__main__":
  main()

