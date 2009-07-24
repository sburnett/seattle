"""
<Program Name>
  custom.py

<Started>
  May 2009

<Author>
  n2k8000@u.washington.edu
  Konstantin Pik

<Purpose>
  This is a sample of what type of custom scripts can be added to be deployed
  on machines. This script in particular grabs the version from nmmain.py by
  executing a grep through the shell, then prints it to console and all output
  is logged from this script.

<Usage>
  This script is called by runlocaltests.py and takes in the path to the
  seattle install.  Not intended to run as a stand-alone.
  
"""

import subprocess
import sys
import os



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
  # get a handle to the subprocess we're creating..
  handle = subprocess.Popen(cmd_str, shell=True, 
      stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  # execute and grab the stdout and err
  stdoutdata, strerrdata = handle.communicate("")

  return stdoutdata, strerrdata 

  
  
def format_print(out, err):
  """
  <Purpose>
    Will print out the non-empty out/err strings once they're properly
    formatted. Intended to format stdout and stderr

  <Arguments>
    out:
      stdout
    err:
      std error

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  out = out.strip('\n\r ')
  err = err.strip('\n\r ')
  if out:
    print out
  if err:
    print err

    
    
def main(installpath):
  """
  <Purpose>
     Entry point into the script. Shell executes a grep command that will
     grab the version from nmmain.py. Then prints err&output of grep to stdout

  <Arguments>
    installpath:
      The seattle install path.

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  
  # this'll get the version
  out, err = shellexec('grep ^version '+installpath+'/nmmain.py')
  format_print(out, err)
  
  # check if we need to upgrade
  # check_if_update(out)
  
  #shellexec('rm -rf '+installpath+'/seattle_repy')
  
  # check for memory hogs
  check_highest_mem_use()
  
  if not is_cron_running():
    start_cron()
  
  try:
    # try and print all file content of /v2 folder
    print 'The following files exist in /v2:'+str(os.listdir(installpath+'/v2'))
    # now dump any log files we may have that would be located in /v2
    for each_file in os.listdir(installpath+'/v2'):
      # check that it's a file and not a dir, just in case.
      if os.path.isfile(installpath+'/v2/'+each_file):
        # yup, dump it so we can see it
        print '\nFile contents of '+each_file
        # filtering out expired because that's taking up a lot of space.
        out, err = shellexec('cat '+installpath+'/v2/'+each_file+' | grep -v \'Expired signature\'')
        format_print(out, err)
        print 'End contents of '+each_file
        
    # We're also gonna try and print the content of the vesseldict file
    print '\nGrabbing vesseldict from seattle_repy.'
    print '\nFile contents of vesseldict:'
    
    # we also need to dump the vesseldict file
    if os.path.isfile(installpath+'/vesseldict'):
      out, err = shellexec('cat '+installpath+'/vesseldict')
      format_print(out, err)
    else:
      print '\tvesseldict is missing!!!'
      
    print 'End contents of vesseldict'
  except Exception, e:
    print e
    return

def stop_seattle():
  """
  <Purpose>
    Makes a call to stop seattle on current node.

  <Arguments>
    None.

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  
  installpath = sys.argv[1]
  out, err = shellexec(installpath+'/stop_seattle.sh')
  return


  
def check_highest_mem_use():
  """
  <Purpose>
     Checks for the processes that have the highest memory usage

  <Arguments>
    None.

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  # this'll get the top 3 memory hogs on the system
  out, err = shellexec('ps -eo pcpu,pid,user,args | sort -r -k1 | head -4')
  print 'Memory usage information:'
  print out
  print err


  
def upgrade_node():
  """
  <Purpose>
     Executes shell commands to download an install file and then
     install the seattle node.

  <Arguments>
    None.

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  
  # stop seattle first. 
  stop_seattle()
  
  # we need to 'cd ~/' since the cwd will be the current install directory 
  # but we want to do everything from ~/ to make it easier.

  # build up a command list that we'll execute that'll upgrade the node
  cmd_list = []
  # uninstall, and then delete old .tgz if one exists.
  cmd_list.append('python uninstall.py; cd ~/; rm -rf seattle_linux.tgz ')
  
  # download the newest file
  cmd_list.append('cd ~/; wget https://seattlegeni.cs.washington.edu/geni/download/flibble/seattle_linux.tgz')
    
  # Untar, then move to move all files to the old install directory.
  cmd_list.append('cd ~/; tar -xf seattle_linux.tgz; cp -rf seattle_repy/ '+sys.argv[1]+'/..')
  
  # Change into seattle_repy directory and execute python install.py, then start seattle
  cmd_list.append('cd '+sys.argv[1]+'; python install.py; ./start_seattle.sh')  
  
  # delete old install
  cmd_list.append('cd ~/; rm -rf seattle_linux.tgz')

  
  cmd_string = "; ".join(cmd_list)
  out, err = shellexec(cmd_string)
  format_print(out, err)
  return
  
  

def is_cron_running():
  """
  <Purpose>
     Checks to see if cron is running.

  <Arguments>
    None.

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    Boolean. True if cron is running, False if not.
  """
  
  # we'll build up commands in a list, then join with ;'s.
  cmd_list = []
  
  # command that we're going to execute
  cmd_list.append('ps auwx | grep crond | grep -v grep')
  
  # build the command string
  cmd_str = '; '.join(cmd_list)
  
  print '\nChecking if crond is running'
  
  # execute the string
  out, err = shellexec(cmd_str)
  
  # check to see if cron* was listed in the ps command
  crond_running = out.find('cron') > -1
  
  format_print(out, err)
  print 'crond is running: '+str(crond_running)+'\n'
  return crond_running
  
  
  
def start_cron():
  """
  <Purpose>
     Starts up crond on this machine

  <Arguments>
    None.

  <Exceptions>
    None.

  <Side Effects>
    Dumps any stderr/out produced when starting crond to stdout which in turn
    will be logged.

  <Returns>
    None.
  """
  
  # build up a list of commands
  cmd_list = []
  cmd_list.append('sudo mkdir /usr/lib/cron')
  cmd_list.append('sudo touch /usr/lib/cron/cron.deny')
  cmd_list.append('sudo /sbin/chkconfig --level 12345 crond on')
  cmd_list.append('sudo /etc/init.d/crond start')
  
  # make it a string and execute it
  cmd_str = '; '.join(cmd_list)
  out, err = shellexec(cmd_str)
  
  # dump to stdout
  format_print(out, err)
  return
  
  
  
def check_if_update(out):
  """
  <Purpose>
     Checks whether a node needs to be updated or not.

  <Arguments>
    out:
      output from shell grabbing the version info from nmmain.

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  
  # checks if node needs to be updated
  is1i_node = out.find('0.1i') > -1
  is1j_node = out.find('0.1j') > -1
  is1k_node = out.find('0.1k') > -1
  if not is1k_node and not is1i_node and not is1j_node:
    print "Starting node update"
    upgrade_node()
    # get the possibly new version from the file and dump it.
    out, err = shellexec('grep ^version '+sys.argv[1]+'/nmmain.py')  
    format_print(out, err)
    print "Node update complete"
  return

if __name__ == "__main__":
  main(sys.argv[1])

