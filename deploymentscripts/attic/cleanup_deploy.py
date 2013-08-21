"""
<Program Name>
  cleanup_deploy.py

<Started>
  May 2009

<Author>
  n2k8000@u.washington.edu
  Konstantin Pik

<Purpose>
  Executes on each test machine and prepares it for runlocaltest.py by 
  cleaning old log files (if any) and old directory locks (if any).

<Usage>
  Note: Not indended to run as a standalone.
  
  python cleanup_deploy.py myhostname

  myhostname:   Required. The hostname of this computer. Used for some path
                  information (logs, etc).
"""

import os
import sys
import subprocess

# for logging purposes we keep this global
my_host_name = ''



def format_print(data):
  """
  <Purpose>
    Wrapper for printing stuff to stdout. Just appends the name of this script
    and my ip.

  <Arguments>
    data: the data to print to console.

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """

  global my_host_name

  # prints and puts a 'description string' identifying the msg from this 
  # script. so long as string isn't empty
  if data.strip('\n '):
    print my_host_name+': Cleanup & Setup Script: '+data

    
    
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
    A tuple containing (stdout, strerr)

    Detailed:
    stdout: stdout printed to console during command execution.
    strerr: error (note: some programs print to strerr instead of stdout)
  """
  handle = subprocess.Popen(cmd_str, shell=True, 
      stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  stdoutdata, strerrdata = handle.communicate("")

  return stdoutdata, strerrdata 

  
  
def find_seattle_installs():
  """
  <Purpose>
    Finds all seattle install directories. (cares only about the first
      one found)

    Priority:
      1. ./seattle_repy folder (exit after find)
      2. ./[remotehost]/seattle_repy folder (exit after find)
      3. search ALL folder with search depth 1 for a seattle_repy folder

    Also assumes that seattle_repy is the name of the install directory.
     
  <Arguments>
    None.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    A list containing the path to the folder containing seattle_repy install
  """
  global my_host_name

  # This will keep track of which folders have a seattle installation
  valid_folder = []
  # Check for seattle_repy dir from where we are now.. 
  if os.path.isdir("./"+my_host_name+"/seattle_repy"):
    valid_folder.append("./"+my_host_name+"/seattle_repy")
  elif os.path.isdir("./seattle_repy"):
    valid_folder.append("./seattle_repy")
  else:
    # search each folder in current directory
    # otherwise check all folders with depth one.
    for folder in os.listdir('.'):
      # if inside that folder we have a seattle install, add it to our list
      if os.path.isdir("./"+folder+"/seattle_repy"):
        valid_folder.append("./"+folder+"/seattle_repy")
        return valid_folder
  
  # return list (with one element, the path) folder with a seattle_install
  return valid_folder

  
  
def clean_locks(paths):
  # OBSOLETE
  """
  <Purpose>
    Cleans DIR.lock files (possibly) left behind by previous runlocaltests.py
    script so that this run will be a clean one. runlocaltests.py will check 
    for a DIR.lock file and if one is found it will skip over it - we don't 
    want that. 
     
  <Arguments>
    paths:  Path's discovered to have seattle_repy directories (same method as
            runlocaltests.py). TODO: share common method across files?
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  return
  for path in paths:
    out, err = shellexec('rm -rf '+path+'/DIR.lock')
    format_and_print(out, err)

    
    
def clean_logs(paths):
  """
  <Purpose>
    Cleans possibly left behind log files from previous runs.
     
  <Arguments>
    paths:  Path's discovered to have seattle_repy directories (same method as
            runlocaltests.py).
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  global my_host_name
  # i clean the dirs for now so we cleanup all the stuff i might've left on 
  # some computers before i wrote this script.. but this will eventually be
  # phased out.
  for path in paths:
    out, err = shellexec('rm -rf '+path+'/deploy.logs/')
    format_and_print(out, err)
  out, err = shellexec('rm -rf ./deploy.logs/')
  format_and_print(out, err)
  
  # clean logfile
  #out, err =  shellexec('rm -rf *.deployrun.log')
  #format_and_print(out, err)

  # clean errlog
  #out, err =  shellexec('rm -rf *.deployrun.err.log')
  #format_and_print(out, err)
  
  # clean tar files 
  #out, err =  shellexec('rm -rf '+my_host_name+'.tgz')
  #format_and_print(out, err)

  
  
def format_and_print(out, err):
  """
  <Purpose>
    Helper method to format and print out from shellexec which returns two stdout
    and err
     
  <Arguments>
    out:  first string to format and print. typically stdout.
    err:  second string to format and print. typically err.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  out = out.strip('\n ')
  err = out.strip('\n ')
  format_print(out)
  format_print(err)

  

def main():
  """
  <Purpose>
    Launches the program.
    
    - Finds installs
    - Cleans old log files
    - Cleans old lock files
     
    Error on no seattle installations found.

  <Arguments>
    None.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  global my_host_name

  # assume this is safe for now because only deploy.py should be calling this script.
  my_host_name = sys.argv[1]

  # get the install paths
  install_paths = find_seattle_installs()
  
  # empty!?
  if not install_paths:
    format_print('No valid installations of seattle found.')
    return
  
  clean_locks(install_paths)
  clean_logs(install_paths)

if __name__ == '__main__':
  main()
